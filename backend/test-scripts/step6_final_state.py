"""STEPS 5+6 — final state: launcher button renders on the Cursor scene,
agent bar present, and the profile JSON carries the expected end state."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dl131_common import BASE, get_profile, scene_names
from playwright.sync_api import sync_playwright

REPO = Path(r"C:\Users\Daniel\CursorRepo\VDock2")

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                              has_touch=False)
    ctx.add_init_script("localStorage.setItem('vdock_tutorial_done','1')")
    page = ctx.new_page()
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector(".dashboard-view", timeout=15000)

    fab = page.locator(".header-reveal-fab")
    if fab.count() and fab.is_visible():
        fab.click()
    page.wait_for_selector(".deck-header", state="visible", timeout=8000)
    pill = page.locator(".autohide-pill")
    if pill.count() and pill.is_visible():
        pill.click()

    page.locator(".glass-pill-scene-selector .segment", has_text="Cursor").click()
    page.wait_for_timeout(1000)

    labels = page.locator(".deck-grid .deck-button .button-label").all_inner_texts()
    print(f"cursor scene buttons ({len(labels)}):", labels)
    assert "Launch Cursor" in labels

    bar = page.locator(".agent-action-bar")
    print("agent bar visible:", bar.count() > 0 and bar.is_visible())
    if bar.count() and bar.is_visible():
        print("  state:", bar.locator(".agent-state-text").inner_text().replace("\n", " / "))
        print("  actions:", bar.locator(".agent-action .agent-action-label").all_inner_texts())

    page.screenshot(path=str(REPO / "dl131-cursor-scene.png"))
    print("final screenshot -> dl131-cursor-scene.png")
    browser.close()

p = get_profile()
cur = next(s for s in p["scenes"] if s["name"] == "Cursor")
print("\nend-state JSON:")
print("  scenes:", scene_names(p))
print(f"  cursor scene: id={cur['id']} icon={cur.get('icon')!r} color={cur.get('color')!r}")
print(f"  buttons={len(cur['pages'][0]['buttons'])} grid={cur['pages'][0]['grid_config']}")
launch = next(b for b in cur["pages"][0]["buttons"] if b["id"] == "btn-dl131-launch-cursor")
print("  launcher:", launch["label"], launch["action"]["type"],
      launch["action"]["config"]["path"], "@", launch["position"])
