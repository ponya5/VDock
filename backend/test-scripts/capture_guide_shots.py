"""Capture guide screenshots for the /guide landing page (DL-132).

Shoots the live app at a desktop viewport (1440x900 -> desktop chrome path)
and saves PNGs into frontend/public/guide/.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5000"
OUT = Path(r"C:\Users\Daniel\CursorRepo\VDock2\frontend\public\guide")
OUT.mkdir(parents=True, exist_ok=True)


def shoot(page, name, clip=None):
    path = OUT / name
    page.screenshot(path=str(path), clip=clip)
    print(f"  {name} ({path.stat().st_size // 1024} KB)")


def goto_scene(page, label):
    pill = page.locator(
        ".glass-pill-scene-selector .segment", has_text=label
    )
    if pill.count():
        pill.first.click()
        page.wait_for_timeout(600)
        return True
    print(f"  scene pill {label!r} not found")
    return False


def reveal_header_and_pin(page):
    fab = page.locator(".header-reveal-fab")
    if fab.count() and fab.is_visible():
        fab.click()
    page.wait_for_selector(".deck-header", state="visible", timeout=8000)
    pill = page.locator(".autohide-pill")
    if pill.count():
        pill.click()  # pin so it can't hide mid-shoot


def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900}, has_touch=False
        )
        ctx.add_init_script("localStorage.setItem('vdock_tutorial_done','1')")
        page = ctx.new_page()

        # --- 1. Deck -----------------------------------------------------
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_selector(".dashboard-view", timeout=15000)
        reveal_header_and_pin(page)
        page.wait_for_timeout(700)
        shoot(page, "guide-deck.png")

        # --- 2. Media scene (Now Playing card) ---------------------------
        goto_scene(page, "Media")
        page.wait_for_timeout(900)
        shoot(page, "guide-media.png")

        # --- 3. Cursor scene (agent bar) ---------------------------------
        goto_scene(page, "Cursor")
        page.wait_for_timeout(900)
        shoot(page, "guide-agents.png")

        # --- 4. Header + countdown pill (crop the header band) -----------
        goto_scene(page, "Media")
        page.wait_for_timeout(400)
        hdr = page.locator(".deck-header")
        box = hdr.bounding_box()
        if box:
            shoot(page, "guide-header.png", clip={
                "x": box["x"], "y": box["y"],
                "width": box["width"],
                "height": min(box["height"] + 60, 900 - box["y"]),
            })

        # --- 5. Settings: appearance sub-tabs ----------------------------
        page.goto(f"{BASE}/settings?tab=appearance", wait_until="networkidle")
        page.wait_for_selector(".settings-app", timeout=15000)
        page.wait_for_timeout(900)
        shoot(page, "guide-settings.png")

        # --- 6. Integrations (apps & scenes sub-tab) ---------------------
        page.goto(f"{BASE}/settings?tab=integration&sub=apps",
                  wait_until="networkidle")
        page.wait_for_timeout(900)
        shoot(page, "guide-integrations.png")

        # --- 7. MCP section + Help & test modal --------------------------
        page.goto(f"{BASE}/settings?tab=integration&sub=mcp",
                  wait_until="networkidle")
        page.wait_for_timeout(800)
        help_btn = page.locator("button", has_text="Help")
        if help_btn.count():
            help_btn.first.click()
            page.wait_for_selector(".modal", state="visible", timeout=5000)
            page.wait_for_timeout(500)
        shoot(page, "guide-mcp.png")
        # close modal for cleanliness
        kb = page.locator(".modal .modal-close, .modal button[aria-label*=Close]")
        if kb.count():
            kb.first.click()

        # --- 8. Tour overlay ----------------------------------------------
        page.goto(BASE, wait_until="networkidle")
        page.evaluate(
            "localStorage.removeItem('vdock_tutorial_done');"
            "localStorage.setItem('vdock_pending_tutorial','1')"
        )
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_selector(".tour-bubble, .tutorial-tour", timeout=10000)
        page.wait_for_timeout(700)
        shoot(page, "guide-tour.png")

        # --- 9. Screensaver picker (settings Appearance -> Screensaver) --
        page.evaluate("localStorage.setItem('vdock_tutorial_done','1')")
        page.goto(f"{BASE}/settings?tab=appearance&sub=screensaver",
                  wait_until="networkidle")
        page.wait_for_selector(".settings-app", timeout=15000)
        page.wait_for_timeout(900)
        shoot(page, "guide-screensaver.png")

        browser.close()
    print("done —", len(list(OUT.glob('*.png'))), "shots in", OUT)


if __name__ == "__main__":
    run()
