"""`app.py --version` prints the version and exits without starting a server (DL-151)."""
import subprocess
import sys
from pathlib import Path

from version import __version__

APP = Path(__file__).resolve().parents[1] / 'app.py'


def test_version_flag_prints_version_and_exits():
    for flag in ('--version', '-V'):
        out = subprocess.run([sys.executable, str(APP), flag], capture_output=True, text=True, timeout=30)
        assert out.returncode == 0
        assert out.stdout.strip() == f'VDock {__version__}'
