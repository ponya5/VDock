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
import re
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


def _unwrap_cmd_shim(binary: str) -> str:
    """Resolve an npm-style .cmd/.bat shim to the binary it forwards to.

    CreateProcess runs batch files through cmd.exe, so an argv list routed
    to a shim is re-parsed by the shell: quotes, carets, pipes, percent
    signs and newlines are mangled or interpreted. That silently breaks the
    no-shell guarantee this module exists for. npm shims all end with the
    same idiom -- ``"<real path>" %*`` -- so the true binary is recoverable.

    Only unwraps to a real executable target. A shim that forwards to a
    script (e.g. ``node cli.js``) is left alone: its interpreter pair can't
    be expressed as a single resolved path.

    Returns the inner executable when the pattern matches and the target
    exists; otherwise the original path unchanged.
    """
    if os.name != 'nt' or not binary.lower().endswith(('.cmd', '.bat')):
        return binary
    try:
        text = Path(binary).read_text(encoding='utf-8', errors='replace')
    except OSError:
        return binary
    match = re.search(r'"([^"]+)"\s+%\*', text)
    if not match:
        return binary
    # Shims express the target relative to their own directory via the
    # dp0 idiom (``%~dp0`` inline or ``%dp0%`` after a SETLOCAL helper).
    target = re.sub(r'%~?dp0%?', lambda _m: str(Path(binary).parent),
                    match.group(1), flags=re.IGNORECASE)
    target = os.path.normpath(target.replace('/', os.sep))
    if target.lower().endswith('.exe') and Path(target).is_file():
        return target
    return binary


def find_binary(name: str) -> Optional[str]:
    """Absolute path to ``name`` on PATH, or None.

    On Windows an npm ``.cmd``/``.bat`` shim is unwrapped to the binary it
    forwards to, so callers get the real executable rather than a batch
    file whose arguments would transit cmd.exe.

    Packs call this at init so they can mark themselves unavailable with a
    useful reason instead of failing when a button is pressed.
    """
    binary = shutil.which(name)
    if binary is None:
        return None
    return _unwrap_cmd_shim(binary)


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + '\n... [output truncated]'


def _kill_tree(proc: subprocess.Popen) -> None:
    """Kill ``proc`` and every descendant.

    Killing only the direct child leaks grandchildren, which keep our
    output pipes open and make the follow-up ``communicate()`` block
    forever -- observed when a timed-out ``claude.cmd`` shim left its
    inner claude.exe alive and the job sat 'running' past its timeout.
    """
    try:
        import psutil
        parent = psutil.Process(proc.pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except psutil.Error:
                pass
        parent.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


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

    # Popen + communicate rather than subprocess.run: on timeout we must kill
    # the process *tree*, which run()'s kill-the-child-only behaviour cannot
    # do -- a surviving grandchild would keep the output pipes open and hang
    # the follow-up communicate() forever.
    try:
        proc = subprocess.Popen(
            resolved,
            cwd=cwd,
            env=run_env,
            stdin=subprocess.PIPE if stdin is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            shell=False,  # never; see the module docstring
        )
    except OSError as e:
        logger.error('Failed to run %s: %s', resolved[0], e)
        return CommandResult(
            ok=False, exit_code=-1, stdout='', stderr=str(e), argv=resolved,
        )

    try:
        stdout, stderr = proc.communicate(input=stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.warning('%s timed out after %ss', resolved[0], timeout)
        _kill_tree(proc)
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            # An unkillable descendant still holds a pipe; report the
            # timeout rather than hang the job worker.
            stdout, stderr = '', ''
        return CommandResult(
            ok=False, exit_code=-1,
            stdout=_truncate(stdout or ''),
            stderr=_truncate(stderr or '') or f'Timed out after {timeout}s',
            argv=resolved, timed_out=True,
        )

    return CommandResult(
        ok=proc.returncode == 0,
        exit_code=proc.returncode,
        stdout=_truncate(stdout or ''),
        stderr=_truncate(stderr or ''),
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
