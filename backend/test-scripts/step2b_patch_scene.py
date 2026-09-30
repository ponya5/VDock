"""STEP 2 tail — patch the UI-created Cursor scene with the original page
(buttons + grid) and scene-level fields the SceneEditor can't express
(transition_style, stagger_order, overlay_style, appId/triggeredByApp)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dl131_common import get_profile, put_profile, scene_names

ORIG_SCENE = json.loads(
    (Path(__file__).parent / "cursor-scene-original.json").read_text()
)

profile = get_profile()
print("scenes:", scene_names(profile))
new_scene = next(s for s in profile["scenes"] if s["name"] == "Cursor")
print(f"before: id={new_scene['id']} icon={new_scene.get('icon')!r} "
      f"color={new_scene.get('color')!r} "
      f"buttons={len(new_scene['pages'][0]['buttons'])} "
      f"grid={new_scene['pages'][0]['grid_config']}")

new_scene["pages"] = ORIG_SCENE["pages"]
for k in ("transition_style", "stagger_order", "overlay_style",
          "overlay_mode", "appId", "triggeredByApp", "buttonSize"):
    if ORIG_SCENE.get(k) is not None:
        new_scene[k] = ORIG_SCENE[k]

status, data = put_profile(profile)
print(f"PATCH PUT -> {status} success={data.get('success')}")
assert status == 200 and data.get("success"), data

check = get_profile()
cur = next(s for s in check["scenes"] if s["name"] == "Cursor")
btns = cur["pages"][0]["buttons"]
print(f"after: id={cur['id']} buttons={len(btns)} "
      f"grid={cur['pages'][0]['grid_config']} "
      f"transition={cur.get('transition_style')} "
      f"actions={sorted({b['action']['type'] for b in btns})}")
assert len(btns) == 8 and cur["pages"][0]["grid_config"] == {"cols": 4, "rows": 2}
print("STEP 2 PASS — UI-created scene now carries the original bindings.")
