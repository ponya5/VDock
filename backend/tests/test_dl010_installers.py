"""DL-010: installers pick a supported Python and repair a broken venv.

Python 3.15 shipped (Homebrew's `python` is 3.15), but pywinrt, PyInstaller
and friends have no 3.15 builds yet, so setup must prefer 3.13/3.12/... and
explain an unsupported-only machine instead of failing inside pip.

setup.sh's functions are exercised for real against fake interpreters (a
`python3.X` stub that reports its version). setup.bat, the NSIS hooks and the
requirement pins cannot run here, so they get static contract checks.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SETUP_SH = REPO / 'setup.sh'
BASH = shutil.which('bash')

posix_only = pytest.mark.skipif(
    sys.platform == 'win32' or BASH is None, reason='setup.sh runs on macOS/Linux')


def _stub_python(directory: Path, name: str, version: str, venv_ok: bool = True) -> Path:
    """A fake interpreter: prints `version` for the version query, and fails
    `import venv, ensurepip` when venv_ok is False (Debian without python3-venv)."""
    stub = directory / name
    stub.write_text(
        '#!/bin/sh\n'
        'case "$2" in\n'
        f'  *version_info*) echo "{version}"; exit 0 ;;\n'
        f'  *ensurepip*) exit {0 if venv_ok else 1} ;;\n'
        'esac\n'
        'exit 0\n',
        encoding='utf-8',
    )
    stub.chmod(0o755)
    return stub


def _tools_dir(tmp_path: Path) -> Path:
    """Only the external commands setup.sh's helpers need - and no python."""
    tools = tmp_path / 'tools'
    tools.mkdir()
    for tool in ('uname', 'sed', 'grep', 'head', 'tail', 'cat', 'dirname'):
        found = shutil.which(tool)
        if found:
            (tools / tool).symlink_to(found)
    return tools


def run_setup_fn(tmp_path: Path, path_dirs, script: str) -> str:
    """Source setup.sh (functions only) with PATH = path_dirs and run `script`."""
    env = {
        'HOME': str(tmp_path),
        'VDOCK_SETUP_LIB_ONLY': '1',
        # No Homebrew kegs / python.org frameworks from the machine running the test.
        'VDOCK_PYTHON_SEARCH_DIRS': '',
        'TEST_PATH': os.pathsep.join(str(d) for d in path_dirs),
        'PATH': os.environ.get('PATH', ''),
    }
    command = f'source "{SETUP_SH}"; PATH="$TEST_PATH"; hash -r; set +e\n{script}'
    out = subprocess.run([BASH, '-c', command], capture_output=True, text=True, env=env, timeout=60)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


@posix_only
def test_supported_window_is_3_9_to_3_14(tmp_path):
    out = run_setup_fn(tmp_path, [_tools_dir(tmp_path)], '''
        for v in 3.8 3.9 3.10 3.13 3.14 3.15 2.7 garbage; do
          if python_minor_supported "$v"; then echo "$v yes"; else echo "$v no"; fi
        done
    ''')
    assert out.splitlines() == [
        '3.8 no', '3.9 yes', '3.10 yes', '3.13 yes', '3.14 yes', '3.15 no', '2.7 no', 'garbage no']


@posix_only
def test_prefers_a_supported_python_over_a_newer_default(tmp_path):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    _stub_python(bin_dir, 'python3', '3.15')      # Homebrew's new default
    _stub_python(bin_dir, 'python3.14', '3.14')
    _stub_python(bin_dir, 'python3.12', '3.12')
    out = run_setup_fn(tmp_path, [bin_dir, _tools_dir(tmp_path)],
                       'find_python && echo "$PYTHON_BIN"')
    assert out == str(bin_dir / 'python3.12')


@posix_only
def test_keg_only_homebrew_python_is_found_off_path(tmp_path):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    _stub_python(bin_dir, 'python3', '3.15')
    keg = tmp_path / 'opt' / 'python@3.13' / 'bin'
    keg.mkdir(parents=True)
    _stub_python(keg, 'python3.13', '3.13')
    out = run_setup_fn(
        tmp_path, [bin_dir, _tools_dir(tmp_path)],
        f'VDOCK_PYTHON_SEARCH_DIRS="{tmp_path}/opt/python@3.MINOR/bin"\n'
        'find_python && echo "$PYTHON_BIN"')
    assert out == str(keg / 'python3.13')


@posix_only
def test_only_unsupported_python_is_explained(tmp_path):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    _stub_python(bin_dir, 'python3', '3.15')
    out = run_setup_fn(tmp_path, [bin_dir, _tools_dir(tmp_path)], '''
        if find_python; then echo "picked $PYTHON_BIN"; else echo "none"; fi
        report_unsupported_python
    ''')
    assert out.splitlines()[0] == 'none'
    assert '3.15' in out and 'needs Python 3.9-3.14' in out and '3.13' in out


@posix_only
def test_python_without_venv_is_skipped(tmp_path):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    _stub_python(bin_dir, 'python3.13', '3.13', venv_ok=False)   # no python3-venv
    _stub_python(bin_dir, 'python3.11', '3.11')
    out = run_setup_fn(tmp_path, [bin_dir, _tools_dir(tmp_path)],
                       'find_python && echo "$PYTHON_BIN"')
    assert out == str(bin_dir / 'python3.11')


@posix_only
@pytest.mark.parametrize('venv_python, recorded, ok, problem', [
    ('3.13', 'version = 3.13.2', True, ''),
    ('3.13', 'version_info = 3.13.2.final.0', True, ''),
    # mise "latest" / brew upgrade moved the base interpreter under the venv.
    ('3.15', 'version = 3.14.8', False, 'unsupported or mismatched'),
    ('3.14', 'version = 3.13.2', False, 'made with Python 3.13 but now runs 3.14'),
    (None, 'version = 3.13.2', False, 'missing'),
])
def test_broken_or_moved_venv_is_detected(tmp_path, venv_python, recorded, ok, problem):
    venv = tmp_path / 'venv'
    (venv / 'bin').mkdir(parents=True)
    (venv / 'pyvenv.cfg').write_text(f'home = /somewhere\n{recorded}\n', encoding='utf-8')
    if venv_python:
        _stub_python(venv / 'bin', 'python', venv_python)
    out = run_setup_fn(tmp_path, [_tools_dir(tmp_path)], f'''
        if venv_python_ok "{venv}"; then echo ok; else echo "bad: $VENV_PROBLEM"; fi
    ''')
    if ok:
        assert out == 'ok'
    else:
        assert out.startswith('bad: ')
        if problem == 'missing':
            assert 'missing' in out
        elif problem.startswith('made with'):
            assert problem in out
        else:
            assert 'does not support' in out or 'made with' in out


@posix_only
def test_pip_failure_names_the_real_cause(tmp_path):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    venv_python = _stub_python(bin_dir, 'python', '3.15')
    no_wheel = tmp_path / 'no-wheel.log'
    no_wheel.write_text(
        'Collecting pywin32==311\n'
        'ERROR: Could not find a version that satisfies the requirement pywin32==311\n'
        'ERROR: No matching distribution found for pywin32==311\n', encoding='utf-8')
    offline = tmp_path / 'offline.log'
    offline.write_text(
        "WARNING: Retrying ... after connection broken by 'NewConnectionError'\n"
        'ERROR: Could not install packages due to an OSError: Could not fetch URL\n', encoding='utf-8')
    out = run_setup_fn(tmp_path, [_tools_dir(tmp_path)], f'''
        report_pip_failure "{no_wheel}" "{venv_python}"
        echo ----
        report_pip_failure "{offline}" "{venv_python}"
    ''')
    first, second = out.split('----')
    assert 'Python 3.15' in first and 'No matching distribution found for pywin32==311' in first
    assert 'no ready-made build' in first and 'rm -rf backend/venv' in first
    assert 'check your internet connection' in second
    assert 'no ready-made build' not in second


# --- static contracts for what cannot run here -----------------------------------

def test_setup_bat_tries_the_py_launcher_versions_before_python():
    text = (REPO / 'setup.bat').read_text(encoding='utf-8').replace('\r\n', '\n')
    find = text[text.index('\n:find_python\n'):text.index('\n:report_unsupported_python\n')]
    assert re.search(r'for %%v in \(3\.13 3\.12 3\.14 3\.11 3\.10\)', find)
    assert find.index('py -%%v') < find.index('python -c')
    assert '(3, 9) <= sys.version_info[:2] <= (3, 14)' in find
    assert 'Python.Python.3.13' in text and 'Python.Python.3.12' not in text
    # The pip failure message is no longer a blanket "check your connection".
    assert 'pip install failed. Check your connection' not in text
    assert ':report_pip_failure' in text and ':venv_python_ok' in text


def test_setup_bat_firewall_rule_is_private_and_skippable():
    text = (REPO / 'setup.bat').read_text(encoding='utf-8').replace('\r\n', '\n')
    offer = text[text.index('\n:offer_firewall_rule\n'):]
    assert 'profile=private' in offer and 'profile=public' not in offer
    assert 'localport=!BACKEND_PORT!' in offer
    assert '_base_executable' in offer          # the process that really listens
    assert '-Verb RunAs' in offer               # elevation, never assumed
    assert '.firewall-rule-declined' in offer   # asked once
    assert text.count('call :offer_firewall_rule') == 2   # menu + --full


def test_nsis_hooks_add_and_remove_the_packaged_firewall_rule():
    text = (REPO / 'frontend' / 'electron' / 'installer.nsh').read_text(encoding='utf-8')
    install = text[text.index('!macro customInstall'):text.index('!macroend')]
    assert 'vdock-backend.exe' in text
    assert 'profile=private' in install and 'add rule' in install
    assert '${Silent}' in install               # auto-updates never prompt
    uninstall = text[text.index('!macro customUnInstall'):]
    assert 'delete rule' in uninstall and '${isUpdated}' in uninstall
    assert 'DeleteRegValue HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Run" "VDock"' in uninstall


def test_launchers_run_the_venv_python():
    launch_sh = (REPO / 'launch.sh').read_text(encoding='utf-8')
    assert 'exec "$VENV_PYTHON" "$ROOT/scripts/VDock-Launcher.py"' in launch_sh
    assert 'command -v python3' not in launch_sh
    launch_bat = (REPO / 'launch.bat').read_text(encoding='utf-8')
    assert '"%VENV_PY%" scripts\\VDock-Launcher.py' in launch_bat
    assert '\npython scripts\\VDock-Launcher.py' not in launch_bat.replace('\r\n', '\n')


def _requirement_lines(name):
    text = (REPO / 'backend' / name).read_text(encoding='utf-8')
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith('#')]


def test_windows_arm64_and_new_python_pins():
    lines = _requirement_lines('requirements.txt')
    joined = '\n'.join(lines)
    # Never imported anywhere, and has no ARM64 wheel or sdist.
    assert 'python-magic' not in joined
    assert "pywin32==312; sys_platform == 'win32'" in lines      # cp39-cp315, win_arm64
    assert 'psutil==7.1.1' in lines                               # abi3 win_arm64
    assert 'bcrypt==5.0.0' in lines                               # abi3 win_arm64
    assert 'pyinstaller==6.22.3' in _requirement_lines('requirements-build.txt')
    spec = (REPO / 'backend' / 'vdock-backend.spec').read_text(encoding='utf-8')
    assert "collect_all('magic')" not in spec


def test_nothing_imports_magic():
    pattern = re.compile(r'^\s*(import magic\b|from magic\b)', re.M)
    offenders = []
    for path in (REPO / 'backend').rglob('*.py'):
        if any(part in ('venv', 'node_modules', '__pycache__') for part in path.parts):
            continue
        if pattern.search(path.read_text(encoding='utf-8', errors='ignore')):
            offenders.append(str(path.relative_to(REPO)))
    assert offenders == []


def test_launcher_wording_follows_the_os(monkeypatch):
    import importlib.util

    launcher_path = REPO / 'scripts' / 'VDock-Launcher.py'
    monkeypatch.syspath_prepend(str(launcher_path.parent))
    spec = importlib.util.spec_from_file_location('vdock_launcher_dl010', launcher_path)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)

    monkeypatch.setattr(launcher, 'IS_WINDOWS', False)
    monkeypatch.setattr(launcher.sys, 'platform', 'darwin')
    assert 'Activity Monitor' in launcher.stop_processes_hint()
    assert 'Task Manager' not in launcher.stop_processes_hint()
    monkeypatch.setattr(launcher, 'IS_WINDOWS', True)
    assert 'Task Manager' in launcher.stop_processes_hint()
    # The interpreter running the launcher (the venv) is the one reported.
    assert launcher.find_python() == sys.executable


def test_source_uninstall_keeps_the_packaged_apps_data():
    # The packaged app's userData is also called vdock-electron; its decks
    # live in vdock-data there and must survive a source-checkout uninstall.
    uninstall_sh = (REPO / 'uninstall.sh').read_text(encoding='utf-8')
    assert '! -name vdock-data' in uninstall_sh
    uninstall_bat = (REPO / 'uninstall.bat').read_text(encoding='utf-8')
    assert 'if /i not "%%~nxd"=="vdock-data"' in uninstall_bat
    assert 'goto :electron_profile_keep_data' in uninstall_bat
