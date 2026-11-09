"""A running job can be cancelled: clients are told, the late result is discarded."""
import threading

from services.job_runner import JobRunner, STATUS_CANCELLED


def test_cancel_marks_job_and_discards_late_result():
    gate = threading.Event()
    events = []
    runner = JobRunner()
    runner.set_emitter(lambda name, payload: events.append(payload['status']))
    runner.set_spawner(lambda fn, *a: threading.Thread(target=fn, args=a, daemon=True).start())

    def slow():
        gate.wait(5)
        return {'success': True, 'message': 'done'}

    job = runner.submit('cc_prompt', slow)
    cancelled = runner.cancel(job.id)
    assert cancelled.status == STATUS_CANCELLED
    gate.set()
    for t in threading.enumerate():
        if t is not threading.current_thread() and t.daemon:
            t.join(1)
    assert runner.get_job(job.id).status == STATUS_CANCELLED
    assert events.count('cancelled') == 1


def test_cancel_unknown_job_is_none():
    assert JobRunner().cancel('nope') is None
