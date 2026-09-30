"""STEP 4 — add a 'Launch Cursor' program button and press it.

The recreated scene's page is a full 4x2 grid (8/8 cells), so the page grid
grows to 4x3 and the launcher lands in the free row at (row 2, col 0).

Press = POST /api/actions/execute with {"action": {...}, "button_id": ...,
"wait": true} — 'program' is not on the long-running list, so it executes
inline; wait:true just skips the job-runner branch.
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dl131_common import CURSOR_LNK, api, get_profile, put_profile

BTN_ID = "btn-dl131-launch-cursor"


def cursor_procs() -> list[str]:
    out = subprocess.run(
        ["tasklist"], capture_output=True, text=True
    ).stdout
    return [l.split()[0] for l in out.splitlines() if "cursor" in l.lower()]


def run():
    assert Path(CURSOR_LNK).exists(), f"lnk missing: {CURSOR_LNK}"

    before = cursor_procs()
    print("cursor procs before:", before)

    profile = get_profile()
    cur = next(s for s in profile["scenes"] if s["name"] == "Cursor")
    page = cur["pages"][0]
    # drop any stale copy of this button (idempotent re-runs)
    page["buttons"] = [b for b in page["buttons"] if b["id"] != BTN_ID]
    page["grid_config"]["rows"] = max(3, page["grid_config"]["rows"])
    page["buttons"].append({
        "id": BTN_ID,
        "label": "Launch Cursor",
        "secondary_label": "",
        "icon": ["fas", "rocket"],
        "icon_type": "fontawesome",
        "media_url": None,
        "media_type": None,
        "action": {"type": "program", "config": {"path": CURSOR_LNK}},
        "shape": "rounded",
        "position": {"col": 0, "row": 2},
        "size": {"cols": 1, "rows": 1},
        "style": {
            "backgroundColor": "#1f6fd1",
            "iconSize": 32,
            "textColor": "#ffffff",
        },
        "layers": {
            "icon": {"type": "fontawesome", "value": ["fas", "rocket"],
                     "loop": "swing"}
        },
        "tooltip": "Launch the Cursor editor",
        "enabled": True,
    })
    status, data = put_profile(profile)
    print(f"PUT launcher -> {status} success={data.get('success')}")
    assert status == 200 and data.get("success"), data

    check = get_profile()
    cur = next(s for s in check["scenes"] if s["name"] == "Cursor")
    btn = next(b for b in cur["pages"][0]["buttons"] if b["id"] == BTN_ID)
    print("persisted button:", btn["label"], btn["action"], btn["position"],
          "grid:", cur["pages"][0]["grid_config"])

    # --- press it ---------------------------------------------------------
    status, result = api("POST", "/api/actions/execute", {
        "action": btn["action"],
        "button_id": BTN_ID,
        "wait": True,
    })
    print(f"POST /api/actions/execute -> {status}")
    print("ActionResult:", result)

    deadline = time.time() + 20
    procs = []
    while time.time() < deadline:
        procs = cursor_procs()
        if procs:
            break
        time.sleep(1)
    print("cursor procs after launch:", procs)

    ok = bool(result.get("success")) and bool(procs)
    print("STEP 4", "PASS" if ok else "FAIL",
          f"— result.success={result.get('success')} message={result.get('message')!r} procs={procs}")


if __name__ == "__main__":
    run()
