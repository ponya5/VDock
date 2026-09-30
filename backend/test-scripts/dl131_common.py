"""Shared helpers for the DL-131 end-to-end scene/launcher test.

The Flask backend serves the API with auth OFF, so plain urllib is enough.
"""
import json
import urllib.request
import urllib.error
from pathlib import Path

BASE = "http://127.0.0.1:5000"
PROFILE_ID = "0027a602-99fa-4a3f-882d-2f32e6bccc9a"
PROFILE_PATH = Path(r"C:\Users\Daniel\CursorRepo\VDock2\backend\data\profiles\0027a602-99fa-4a3f-882d-2f32e6bccc9a.json")
BACKUP_DIR = Path(r"C:\Users\Daniel\CursorRepo\VDock2\backend\data\backups")
REPO_ROOT = Path(r"C:\Users\Daniel\CursorRepo\VDock2")
CURSOR_LNK = r"C:\Users\Daniel\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Cursor.lnk"


def api(method: str, path: str, payload=None):
    """Tiny JSON client -> (status, parsed_json)."""
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}


def get_profile() -> dict:
    status, data = api("GET", f"/api/profiles/{PROFILE_ID}")
    assert status == 200 and data.get("profile"), f"GET profile failed: {status} {data}"
    return data["profile"]


def put_profile(profile: dict):
    return api("PUT", f"/api/profiles/{PROFILE_ID}", profile)


def scene_names(profile: dict):
    return [s.get("name") for s in profile.get("scenes", [])]
