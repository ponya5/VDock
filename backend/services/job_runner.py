"""Background execution for long-running actions.

Some actions cannot finish inside an HTTP request. ``claude_prompt`` routinely
takes 30 seconds and is allowed up to ten minutes, while the frontend's axios
client gives up after 30 -- so running it synchronously means the UI reports a
timeout while the work carries on invisibly, and the user has no idea whether
it succeeded.

So actions the catalog marks ``long_running`` are submitted here instead. The
request returns a job id immediately and the result arrives over Socket.IO:

    action_job  { job_id, status: running,   action_type }
    action_job  { job_id, status: succeeded, result: {...} }
    action_job  { job_id, status: failed,    result: {...} }

The pool is bounded so a wall of button presses cannot spawn unbounded
subprocesses, and finished jobs are retained briefly so a client that missed
the event can still poll for the outcome.
"""
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger('vdock')

MAX_WORKERS = 4
#: How long a finished job stays readable via get_job().
RESULT_TTL_SECONDS = 600
#: Keep the job table from growing without bound.
MAX_TRACKED_JOBS = 200

STATUS_RUNNING = 'running'
STATUS_SUCCEEDED = 'succeeded'
STATUS_FAILED = 'failed'


@dataclass
class Job:
    """One submitted action."""
    id: str
    action_type: str
    status: str = STATUS_RUNNING
    result: Optional[Dict[str, Any]] = None
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    button_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            'job_id': self.id,
            'action_type': self.action_type,
            'status': self.status,
            'started_at': self.started_at,
        }
        if self.button_id:
            data['button_id'] = self.button_id
        if self.result is not None:
            data['result'] = self.result
        if self.finished_at is not None:
            data['finished_at'] = self.finished_at
            data['duration'] = round(self.finished_at - self.started_at, 2)
        return data


class JobRunner:
    """Runs long actions off the request thread and broadcasts the outcome."""

    def __init__(self, max_workers: int = MAX_WORKERS) -> None:
        self._pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix='vdock-job'
        )
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        #: Injected by app.py; kept optional so tests need no socket server.
        self._emit: Optional[Callable[[str, Dict[str, Any]], None]] = None

    def set_emitter(self, emit: Callable[[str, Dict[str, Any]], None]) -> None:
        """Provide the Socket.IO broadcast function."""
        self._emit = emit

    def _broadcast(self, job: Job) -> None:
        if self._emit is None:
            return
        try:
            self._emit('action_job', job.to_dict())
        except Exception as e:  # pragma: no cover - transport failure
            logger.error('Could not broadcast job %s: %s', job.id, e)

    def _prune(self) -> None:
        """Drop old finished jobs. Caller holds the lock."""
        if len(self._jobs) <= MAX_TRACKED_JOBS:
            cutoff = time.time() - RESULT_TTL_SECONDS
            stale = [
                job_id for job_id, job in self._jobs.items()
                if job.finished_at is not None and job.finished_at < cutoff
            ]
        else:
            finished = sorted(
                (j for j in self._jobs.values() if j.finished_at is not None),
                key=lambda j: j.finished_at or 0,
            )
            stale = [j.id for j in finished[: len(self._jobs) - MAX_TRACKED_JOBS]]

        for job_id in stale:
            self._jobs.pop(job_id, None)

    def submit(
        self,
        action_type: str,
        run: Callable[[], Any],
        button_id: Optional[str] = None,
    ) -> Job:
        """Queue ``run`` and return the tracking Job immediately.

        Args:
            action_type: For the client, so it knows what is running.
            run: Zero-argument callable returning an ActionResult-like object.
            button_id: Optional button to attribute progress to.
        """
        job = Job(id=uuid.uuid4().hex[:16], action_type=action_type,
                  button_id=button_id)

        with self._lock:
            self._prune()
            self._jobs[job.id] = job

        self._broadcast(job)
        self._pool.submit(self._run, job, run)
        return job

    def _run(self, job: Job, run: Callable[[], Any]) -> None:
        try:
            result = run()
            payload = result.to_dict() if hasattr(result, 'to_dict') else dict(result)
            job.status = (
                STATUS_SUCCEEDED if payload.get('success') else STATUS_FAILED
            )
            job.result = payload
        except Exception as e:
            logger.error('Job %s (%s) raised: %s', job.id, job.action_type, e)
            job.status = STATUS_FAILED
            job.result = {'success': False, 'message': f'Action failed: {e}'}
        finally:
            job.finished_at = time.time()
            self._broadcast(job)

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for j in self._jobs.values() if j.finished_at is None)

    def shutdown(self, wait: bool = False) -> None:
        self._pool.shutdown(wait=wait)


#: Process-wide runner, mirroring how app.py holds its other singletons.
_runner: Optional[JobRunner] = None


def get_job_runner() -> JobRunner:
    global _runner
    if _runner is None:
        _runner = JobRunner()
    return _runner
