"""STEP 1 — remove the Cursor scene via PUT /api/profiles/<id> (full object)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dl131_common import get_profile, put_profile, scene_names

profile = get_profile()
before = scene_names(profile)
print("Before:", before)

scenes = [s for s in profile["scenes"] if s.get("name") != "Cursor"]
assert len(scenes) == len(profile["scenes"]) - 1, "expected exactly one Cursor scene"

payload = {
    "name": profile["name"],
    "description": profile.get("description", ""),
    "icon": profile.get("icon"),
    "avatar": profile.get("avatar"),
    "theme": profile.get("theme", "default"),
    "pages": profile.get("pages", []),
    "scenes": scenes,
    "dockedButtons": profile.get("dockedButtons", []),
    "settings": profile.get("settings"),
}
status, data = put_profile(payload)
print(f"PUT /api/profiles -> {status}, success={data.get('success')}, scenes in response: {scene_names(data.get('profile', {}))}")
assert status == 200 and data.get("success"), data

after = scene_names(get_profile())
print("After (GET):", after)
assert "Cursor" not in after
print("STEP 1 PASS — Cursor scene removed and persisted.")
