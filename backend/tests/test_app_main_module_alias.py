"""`python app.py` must not create a second app when a route imports `app`.

Routes lazily `from app import action_executor`. Run as a script, app.py is
module `__main__`, so without an alias that import executed the file again:
a second SocketIO was built and every broadcaster re-pointed at it, silently
dropping all server pushes (agent state, alerts, background-job results).
"""
import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

PROBE = r'''
import os
import runpy
import sys
from pathlib import Path
import flask_socketio

# The __main__ block persists a generated SECRET_KEY; keep that off the
# developer's real backend/.env.
import config
config.env_file = lambda: Path(os.environ["VDOCK_PROBE_ENV"])

flask_socketio.SocketIO.run = lambda *args, **kwargs: None
served = runpy.run_path("app.py", run_name="__main__")

from app import socketio as imported_socketio
print("same" if imported_socketio is served["socketio"] else "different")
'''


def test_importing_app_while_running_as_script_reuses_the_served_socketio(tmp_path):
    env = {**os.environ, 'VDOCK_PROBE_ENV': str(tmp_path / '.env'), 'SECRET_KEY': ''}
    completed = subprocess.run(
        [sys.executable, '-c', PROBE], cwd=BACKEND_DIR, env=env,
        capture_output=True, text=True, timeout=120,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    assert completed.stdout.strip().splitlines()[-1] == 'same'
