"""Tests for the safe subprocess helper.

Feature: ai-dev-integration-packs, Property 1.5: user text never reaches a shell.

Integration-pack arguments are user-authored free text -- a Claude prompt is the
obvious case. If any of these fail, a prompt containing shell metacharacters
could execute instead of being sent as a prompt.

Existing code in this repo sets the opposite precedent (CrossPlatformAction.
_run_command and ProgramAction both use shell=True), which is exactly why the
packs route through this helper instead.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import subprocess_runner as sr  # noqa: E402

PY = sys.executable

# Text a user might legitimately type into a prompt or commit message.
NASTY = [
    'fix the bug; rm -rf ~',
    'explain `whoami`',
    'why does $(echo pwned) happen',
    'handle a && b || c',
    'quote "this" and \'that\'',
    'a | b > c < d',
    'path\\with\\backslashes',
    'newline\nand tab\t',
    '${HOME}',
    '%USERPROFILE%',
    '../../etc/passwd',
]


# --- the core guarantee ------------------------------------------------------

@pytest.mark.parametrize('payload', NASTY)
def test_metacharacters_arrive_verbatim(payload):
    """The argument must reach the program byte-for-byte, unexecuted."""
    result = sr.run([PY, '-c', 'import sys; print(sys.argv[1], end="")', payload])

    assert result.ok, result.stderr
    assert result.stdout == payload


@pytest.mark.parametrize('payload', NASTY)
def test_metacharacters_have_no_side_effects(payload, tmp_path):
    """A command substitution in the payload must not run."""
    canary = tmp_path / 'canary.txt'
    attack = f'{payload}; echo owned > {canary}'

    sr.run([PY, '-c', 'import sys; print(len(sys.argv))', attack])

    assert not canary.exists(), 'the payload was interpreted by a shell'


def test_a_string_argv_is_refused():
    """Passing a string is the mistake that reintroduces shell injection."""
    with pytest.raises(ValueError, match='not a string'):
        sr.run('echo hello')


def test_empty_argv_is_refused():
    with pytest.raises(ValueError):
        sr.run([])


def test_spawn_also_refuses_a_string_argv():
    with pytest.raises(ValueError, match='not a string'):
        sr.spawn('notepad')


def test_spawn_gives_windows_children_their_own_console(monkeypatch):
    """WinError 87 regression: CREATE_NEW_CONSOLE and DETACHED_PROCESS are
    mutually exclusive and CreateProcess rejects the pair with
    ERROR_INVALID_PARAMETER. The console flag must be *present* — dropping
    it entirely would open the terminal invisibly and still pass a purely
    negative assertion."""
    calls = []

    class FakePopen:
        def __init__(self, argv, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(sr.subprocess, 'Popen', FakePopen)
    sr.spawn([PY, '--version'])

    flags = calls[0].get('creationflags', 0)
    if os.name == 'nt':
        assert flags & sr.subprocess.CREATE_NEW_CONSOLE
        assert not flags & sr.subprocess.DETACHED_PROCESS
    else:
        assert flags == 0


# --- npm .cmd shims -----------------------------------------------------------

@pytest.mark.skipif(os.name != 'nt', reason='.cmd shims are a Windows/npm thing')
def test_cmd_shim_is_unwrapped_and_args_arrive_verbatim(tmp_path, monkeypatch):
    """A `.cmd` shim re-parses argv through cmd.exe -- metacharacters and
    newlines get eaten (a prompt containing code never arrives). The npm
    `"<path>" %*` idiom is unwrapped to the real binary instead."""
    shim = tmp_path / 'shimtool.cmd'
    shim.write_text(
        f'@echo off\n"{PY}" %*\n', encoding='ascii'
    )
    monkeypatch.setenv('PATH', str(tmp_path) + os.pathsep + os.environ['PATH'])

    payload = 'def f(x):\n    return "a|b" ^ x & "c%"\n'
    result = sr.run(['shimtool', '-c',
                     'import sys; print(sys.argv[1], end="")', payload])

    assert result.ok, result.stderr
    assert result.stdout == payload


def test_non_shim_binary_is_returned_unchanged():
    binary = sr.find_binary(os.path.basename(PY))
    assert binary is not None
    assert binary.lower().endswith('.exe')


# --- resolution and failure reporting ----------------------------------------

def test_missing_binary_raises_a_named_error():
    with pytest.raises(sr.BinaryNotFoundError, match='definitely_not_a_real_binary'):
        sr.run(['definitely_not_a_real_binary'])


def test_find_binary_locates_python():
    assert sr.find_binary(os.path.basename(PY)) is not None


def test_find_binary_returns_none_when_absent():
    assert sr.find_binary('definitely_not_a_real_binary') is None


def test_nonzero_exit_is_reported_not_raised():
    result = sr.run([PY, '-c', 'import sys; sys.exit(3)'])

    assert result.ok is False
    assert result.exit_code == 3


def test_stderr_is_captured():
    result = sr.run([PY, '-c', 'import sys; sys.stderr.write("boom")'])

    assert 'boom' in result.stderr
    assert result.output == 'boom'


def test_timeout_is_reported_not_raised():
    result = sr.run([PY, '-c', 'import time; time.sleep(5)'], timeout=1)

    assert result.ok is False
    assert result.timed_out is True
    assert 'Timed out' in result.stderr


def test_missing_cwd_is_reported_not_raised(tmp_path):
    result = sr.run([PY, '-c', 'pass'], cwd=str(tmp_path / 'nope'))

    assert result.ok is False
    assert 'does not exist' in result.stderr


def test_cwd_is_honoured(tmp_path):
    result = sr.run([PY, '-c', 'import os; print(os.getcwd(), end="")'],
                    cwd=str(tmp_path))

    assert os.path.realpath(result.stdout) == os.path.realpath(str(tmp_path))


# --- resource limits ---------------------------------------------------------

def test_output_is_capped():
    result = sr.run(
        [PY, '-c', f'print("x" * {sr.MAX_OUTPUT_CHARS * 2}, end="")']
    )

    assert len(result.stdout) < sr.MAX_OUTPUT_CHARS + 100
    assert 'truncated' in result.stdout


def test_summary_is_single_line_and_short():
    result = sr.run([PY, '-c', r'print("a\n" * 100, end="")'])

    summary = result.summary(limit=50)
    assert '\n' not in summary
    assert len(summary) <= 50


# --- environment and stdin ---------------------------------------------------

def test_env_is_merged_over_the_real_environment():
    result = sr.run(
        [PY, '-c', 'import os; print(os.environ["VDOCK_TEST"], end="")'],
        env={'VDOCK_TEST': 'set'},
    )

    assert result.stdout == 'set'


def test_env_does_not_wipe_the_existing_environment():
    result = sr.run(
        [PY, '-c', 'import os; print("PATH" in os.environ, end="")'],
        env={'VDOCK_TEST': 'set'},
    )

    assert result.stdout == 'True'


def test_stdin_is_piped():
    result = sr.run([PY, '-c', 'import sys; print(sys.stdin.read(), end="")'],
                    stdin='piped text')

    assert result.stdout == 'piped text'


def test_argv_is_recorded_with_an_absolute_binary():
    result = sr.run([PY, '-c', 'pass'])

    assert os.path.isabs(result.argv[0])
