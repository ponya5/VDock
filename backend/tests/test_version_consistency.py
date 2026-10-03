"""One version, three files (DL-146 Task 2.6)."""
import json
import re
from pathlib import Path

import pytest

from version import __version__

REPO = Path(__file__).resolve().parents[2]


def test_version_is_semver():
    assert re.fullmatch(r'\d+\.\d+\.\d+', __version__)


@pytest.mark.parametrize('rel', ['frontend/package.json', 'frontend/electron/package.json'])
def test_package_json_matches_backend_version(rel):
    path = REPO / rel
    if not path.exists():
        pytest.skip(f'{rel} not present')
    assert json.loads(path.read_text(encoding='utf-8'))['version'] == __version__


def test_health_and_mcp_report_the_single_version():
    from app import app
    from routes import mcp

    assert mcp.SERVER_VERSION == __version__
    body = app.test_client().get('/api/health').get_json()
    assert body['version'] == __version__
