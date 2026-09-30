"""STEP 0 — dated backup of the live profile + extract the Cursor scene object."""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dl131_common import PROFILE_PATH, BACKUP_DIR, get_profile, scene_names

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"profile-pre-dl131-e2e-{stamp}.json"
shutil.copy2(PROFILE_PATH, backup)
print(f"Backup written: {backup} ({backup.stat().st_size} bytes)")

profile = get_profile()
print("Scenes:", scene_names(profile))

cursor = next((s for s in profile["scenes"] if s.get("name") == "Cursor"), None)
assert cursor, "No scene named 'Cursor' found!"
out = Path(__file__).parent / "cursor-scene-original.json"
out.write_text(json.dumps(cursor, indent=2))
print(f"Cursor scene id={cursor['id']} icon={cursor.get('icon')!r} color={cursor.get('color')!r}")
print(f"  appId={cursor.get('appId')} triggeredByApp={cursor.get('triggeredByApp')}")
print(f"  pages={len(cursor['pages'])} buttons={len(cursor['pages'][0]['buttons'])} grid={cursor['pages'][0]['grid_config']}")
print(f"  saved verbatim -> {out}")
