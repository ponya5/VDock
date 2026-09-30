"""STEP 3 — verify the recreated Cursor scene in the UI + screenshots.

Two passes:
  A) desktop chrome (1440x900, no touch): scene pill in the header pill
     selector, click -> deck grid renders the 8 cursor_* buttons. Also the
     AgentActionBar check (STEP 5) runs here — it's a desktop-only surface.
  B) mobile chrome (1024x600 + touch -> min dim 600 <= 700): bottom rail
     .mc-scene-rail; the Cursor scene renders MobileAgentConsole instead of
     the grid (by design — scene resolves to the 'cursor' app profile which
     carries state_actions, DL-065).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dl131_common import BASE
from playwright.sync_api import sync_playwright

REPO = Path(r"C:\Users\Daniel\CursorRepo\VDock2")

EXPECTED_LABELS = [
    "New Agent", "Review", "Commit", "Inline Edit",
    "Explain", "Write Tests", "Fix Tests", "Terminal",
]


def desktop_pass(pw):
    print("\n=== STEP 3a / 5 — desktop chrome ===")
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                              has_touch=False)
    ctx.add_init_script("localStorage.setItem('vdock_tutorial_done','1')")
    page = ctx.new_page()
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector(".dashboard-view", timeout=15000)

    print("chrome:", "mobile" if page.locator(".mobile-chrome").count() else "desktop")

    fab = page.locator(".header-reveal-fab")
    if fab.count() and fab.is_visible():
        fab.click()
    page.wait_for_selector(".deck-header", state="visible", timeout=8000)

    # Pin the header so the autohide countdown doesn't unmount the pills
    # mid-assertion (that was the earlier flake).
    pill = page.locator(".autohide-pill")
    if pill.count() and pill.is_visible():
        pill.click()

    labels = page.locator(
        ".glass-pill-scene-selector .segment .segment-label").all_inner_texts()
    print("pills:", labels)
    assert "Cursor" in labels, "Cursor pill missing"

    seg = page.locator(".glass-pill-scene-selector .segment",
                       has_text="Cursor")
    seg.click()
    page.wait_for_timeout(900)  # scene-wipe transition
    print("active pill:", page.locator(
        ".glass-pill-scene-selector .segment.is-active .segment-label"
    ).inner_text())

    buttons = page.locator(".deck-grid .deck-button")
    page.wait_for_timeout(400)
    btn_labels = buttons.locator(".button-label").all_inner_texts()
    print(f"deck buttons rendered: {buttons.count()} -> {btn_labels}")
    assert buttons.count() >= 8
    for lbl in EXPECTED_LABELS:
        assert lbl in btn_labels, f"missing button {lbl!r}"

    # --- STEP 5: agent action bar --------------------------------------
    bar = page.locator(".agent-action-bar")
    if bar.count() and bar.is_visible():
        state_txt = bar.locator(".agent-state-text").inner_text().replace("\n", " / ")
        acts = bar.locator(".agent-action .agent-action-label").all_inner_texts()
        print(f"AgentActionBar VISIBLE: state={state_txt!r} actions={acts}")
    else:
        print("AgentActionBar NOT rendered")
    mac = page.locator(".mobile-agent-console").count()
    print(f"mobile-agent-console elements on desktop: {mac}")

    page.screenshot(path=str(REPO / "dl131-cursor-scene.png"))
    print("screenshot -> dl131-cursor-scene.png")
    browser.close()
    return True


def mobile_pass(pw):
    print("\n=== STEP 3b — mobile chrome ===")
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1024, "height": 600},
                              has_touch=True)
    ctx.add_init_script("localStorage.setItem('vdock_tutorial_done','1')")
    page = ctx.new_page()
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector(".dashboard-view", timeout=15000)

    coarse = page.evaluate("window.matchMedia('(pointer: coarse)').matches")
    print(f"viewport 1024x600, touch on, coarse={coarse}, "
          f"maxTouchPoints={page.evaluate('navigator.maxTouchPoints')}")
    rail = page.locator(".mobile-chrome .mc-scene-rail")
    print("mobile rail present:", rail.count() > 0)
    assert rail.count() > 0, "mobile chrome did not render"

    seg_labels = page.locator(".mc-seg .mc-seg-label").all_inner_texts()
    print("rail segments:", seg_labels)
    assert "Cursor" in seg_labels, "Cursor missing from mobile rail"

    page.locator(".mc-seg", has_text="Cursor").click()
    page.wait_for_timeout(900)
    active = page.locator(".mc-seg.is-active .mc-seg-label")
    print("active segment:", active.inner_text() if active.count() else "?")

    console = page.locator(".mobile-agent-console")
    grid_buttons = page.locator(".deck-grid .deck-button")
    print(f"MobileAgentConsole rendered: {console.count() > 0}; "
          f"deck buttons on mobile: {grid_buttons.count()}")
    if console.count():
        print("console state line:",
              console.locator(".mac-state-label").inner_text())
        acts = console.locator(".mac-action").all_inner_texts()
        print("console actions:", acts)
    page.screenshot(path=str(REPO / "dl131-cursor-scene-mobile.png"))
    print("screenshot -> dl131-cursor-scene-mobile.png")
    browser.close()


def run():
    with sync_playwright() as pw:
        desktop_pass(pw)
        mobile_pass(pw)
    print("\nSTEP 3 PASS — Cursor scene verified in both chromes.")


if __name__ == "__main__":
    run()
