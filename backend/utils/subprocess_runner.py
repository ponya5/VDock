"""Safe subprocess execution for CLI-backed integrations.

Every shell-out from an integration pack (``claude``, ``gh``, ``git``) goes
through here. The rule is simple and absolute: **arguments are passed as a
list and never through a shell**.

That matters more for these packs than for the rest of VDock, because their
arguments are user-authored free text. A Claude prompt is the obvious case --
``claude -p "fix the bug; rm -rf ~"`` must send those characters to Claude as a
prompt, not run them. The existing code in the repo sets the opposite
precedent: ``CrossPlatformAction._run_command`` and ``ProgramAction`` both use
``shell=True``. Nothing here may follow it.

The other jobs this does:

* resolve the binary with ``shutil.which`` so a pack can report "gh is not
  installed" up front rather than failing when a button is pressed;
* enforce a timeout, since a CLI that waits on input would otherwise hang a
  worker thread forever;
* cap captured output, so a command that prints a hundred megabytes cannot
  exhaust memory on its way into a toast notification.
"""
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

logger = logging.getLogger('vdock')

# Captured stdout/stderr is bound for a notification or a button face; there is
# no reason to hold more than this in memory.
MAX_OUTPUT_CHARS = 64_000
DEFAULT_TIMEOUT = 120


class BinaryNotFoundError(RuntimeError):
    """Raised when the requested executable is not on PATH."""


@dataclass(frozen=True)
class CommandResult:
    """The outcome of one command."""
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    argv: Sequence[str]
    timed_out: bool = False

    @property
    def output(self) -> str:
        """Whichever stream carries the useful text."""
        return self.stdout.strip() or self.stderr.strip()

    def summary(self, limit: int = 200) -> str:
        """A short single-line description, for toasts and button sublabels."""
        text = ' '.join(self.output.split())
        return text if len(text) <= limit else text[: limit - 1] + '…'


def find_binary(name: str) -> Optional[str]:
    """Absolute path to ``name`` on PATH, or None.

    Packs call this at init so they can mark themselves unavailable with a
    useful reason instead of failing at press time.
    """
    return shutil.which(name)


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + '\n... [output truncated]'


def run(
    argv: Sequence[str],
    *,
    cwd: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    env: Optional[Dict[str, str]] = None,
    stdin: Optional[str] = None,
) -> CommandResult:
    """Run ``argv`` without a shell and capture its output.

    Args:
        argv: Program and arguments. argv[0] is resolved on PATH. Never a
            single string -- that is what invites shell injection.
        cwd: Working directory. Must exist.
        timeout: Seconds before the process is killed.
        env: Extra environment variables, merged over the current environment.
        stdin: Text piped to the process.

    Returns:
        A CommandResult. Failure is reported, not raised, so a button press
        surfaces a message rather than a stack trace.

    Raises:
        BinaryNotFoundError: argv[0] is not on PATH.
        ValueError: argv is empty, or argv was passed as a bare string.
    """
    if isinstance(argv, (str, bytes)):
        raise ValueError(
            'argv must be a list of arguments, not a string: passing a string '
            'is what enables shell injection'
        )
    argv = list(argv)
    if not argv:
        raise ValueError('argv must not be empty')

    binary = find_binary(argv[0])
    if binary is None:
        raise BinaryNotFoundError(f'{argv[0]!r} was not found on PATH')

    resolved = [binary, *(str(a) for a in argv[1:])]

    if cwd is not None:
        cwd_path = Path(cwd).expanduser()
        if not cwd_path.is_dir():
            return CommandResult(
                ok=False, exit_code=-1, stdout='',
                stderr=f'Working directory does not exist: {cwd}',
                argv=resolved,
            )
        cwd = str(cwd_path)

    run_env = None
    if env:
        run_env = {**os.environ, **env}

    logger.debug('Running %s (cwd=%s)', resolved[0], cwd)

    try:
        completed = subprocess.run(
            resolved,
            cwd=cwd,
            env=run_env,
            input=stdin,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            shell=False,  # never; see the module docstring
            check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning('%s timed out after %ss', resolved[0], timeout)
        return CommandResult(
            ok=False, exit_code=-1, stdout='',
            stderr=f'Timed out after {timeout}s', argv=resolved, timed_out=True,
        )
    except OSError as e:
        logger.error('Failed to run %s: %s', resolved[0], e)
        return CommandResult(
            ok=False, exit_code=-1, stdout='', stderr=str(e), argv=resolved,
        )

    return CommandResult(
        ok=completed.returncode == 0,
        exit_code=completed.returncode,
        stdout=_truncate(completed.stdout or ''),
        stderr=_truncate(completed.stderr or ''),
        argv=resolved,
    )


def spawn(
    argv: Sequence[str],
    *,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> None:
    """Start a detached process without waiting for it.

    For actions that hand off to a window the user then drives themselves --
    opening an interactive ``claude`` session in a terminal, say.
    """
    if isinstance(argv, (str, bytes)):
        raise ValueError('argv must be a list of arguments, not a string')
    argv = list(argv)
    if not argv:
        raise ValueError('argv must not be empty')

    binary = find_binary(argv[0])
    if binary is None:
        raise BinaryNotFoundError(f'{argv[0]!r} was not found on PATH')

    run_env = {**os.environ, **env} if env else None
    creation_flags = 0
    if os.name == 'nt':
        # A console of its own keeps the terminal usable and alive after
        # VDock exits. DETACHED_PROCESS must not be OR'd in: the two flags
        # are mutually exclusive, and CreateProcess fails the combination
        # with WinError 87.
        creation_flags = getattr(subprocess, 'CREATE_NEW_CONSOLE', 0)

    subprocess.Popen(  # noqa: S603 - argv list, shell=False
        [binary, *(str(a) for a in argv[1:])],
        cwd=cwd,
        env=run_env,
        shell=False,
        creationflags=creation_flags,
    )
