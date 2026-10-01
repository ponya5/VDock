"""STEP 2 — re-add the Cursor scene through the real UI with playwright.

Desktop chrome (min viewport dim > 700 -> not the mobile path):
  reveal header FAB -> Toggle Edit Mode -> [+] Add scene -> SceneEditor
  (name 'Cursor', icon 'i-cursor', color '#1f6fd1') -> Save.

Headless chromium reports maxTouchPoints=10, so the app's global focusin
handler opens the OnScreenKeypad on every text input — the same UX a real
touch-panel user gets. We therefore type through the keypad itself
(tap field -> keypad opens seeded with the field value -> press keys ->
Enter closes).

The SceneEditor exposes no marker/binding fields (Scene has no `appMarkers`;
agent binding is inferred from button command ids / scene name), so the
original 8 buttons + 4x2 grid + transition fields are patched back onto the
UI-created scene via PUT /api/profiles afterwards.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dl131_common import BASE, get_profile, put_profile, scene_names
from playwright.sync_api import sync_playwright

ORIG_SCENE = json.loads(
    (Path(__file__).parent / "cursor-scene-original.json").read_text()
)
SHOT_DIR = Path(r"C:\Users\Daniel\CursorRepo\VDock2") / "design-log" / "refs"


def _key_labels(page):
    keys = page.locator(".onscreen-keypad .keypad-key")
    return [keys.nth(i).inner_text().strip() for i in range(keys.count())]


def keypad_tap(page, label):
    keys = page.locator(".onscreen-keypad .keypad-key")
    for i in range(keys.count()):
        if keys.nth(i).inner_text().strip() == label:
            keys.nth(i).click()
            return
    raise AssertionError(f"no keypad key labeled {label!r}; have {_key_labels(page)}")


def keypad_type(page, text):
    """Type on the on-screen keypad. Shift is a LATCHING toggle: tap it on
    for a capital, tap the (now uppercase-labeled) letter, tap it off."""
    shifted = False
    for ch in text:
        if ch == " ":
            keypad_tap(page, "Space")
            continue
        need_shift = ch.isalpha() and ch.isupper()
        if need_shift and not shifted:
            keypad_tap(page, "⇧")
            shifted = True
        elif not need_shift and shifted:
            keypad_tap(page, "⇧")
            shifted = False
        keypad_tap(page, ch)


def keypad_clear(page, n):
    for _ in range(n):
        keypad_tap(page, "⌫")


def keypad_close(page):
    keypad_tap(page, "Enter")
    page.locator(".onscreen-keypad-container").wait_for(state="hidden", timeout=5000)


def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900}, has_touch=False
        )
        # Fresh profile would auto-start the first-run tour (server-side
        # tutorialCompleted=false) and steal the UI — mark it done locally.
        ctx.add_init_script("localStorage.setItem('vdock_tutorial_done','1')")
        page = ctx.new_page()

        page.goto(BASE, wait_until="networkidle")
        page.wait_for_selector(".dashboard-view", timeout=15000)
        coarse = page.evaluate("window.matchMedia('(pointer: coarse)').matches")
        print(f"maxTouchPoints={page.evaluate('navigator.maxTouchPoints')}")
        print(f"viewport={page.evaluate('window.innerWidth')}x{page.evaluate('window.innerHeight')}, "
              f"pointer:coarse={coarse}")

        mobile = page.locator(".mobile-chrome").count() > 0
        print("chrome:", "mobile rail" if mobile else "desktop header path")
        assert not mobile

        # Header hidden by default (settings.showHeader unset/false) -> reveal.
        fab = page.locator(".header-reveal-fab")
        if fab.count() and fab.is_visible():
            fab.click()
        page.wait_for_selector(".deck-header", state="visible", timeout=8000)

        labels = page.locator(
            ".glass-pill-scene-selector .segment .segment-label"
        ).all_inner_texts()
        print("scene pills before add:", labels)
        assert "Cursor" not in labels

        # Edit mode -> '+' add-scene button.
        page.click('button[aria-label="Toggle Edit Mode"]')
        page.locator('button[aria-label="Add scene"]').wait_for(
            state="visible", timeout=5000
        )
        page.click('button[aria-label="Add scene"]')

        modal = page.locator(".modal.scene-editor")
        modal.wait_for(state="visible", timeout=5000)
        print("modal title:", modal.locator(".modal-header h2").inner_text())

        # --- Scene Name via the on-screen keypad (touch UX) ---------------
        name_input = modal.locator('input[placeholder="Enter scene name"]')
        name_input.click()
        page.locator(".onscreen-keypad-container").wait_for(
            state="visible", timeout=5000
        )
        # keypad is seeded with the field's current value ('New Scene').
        keypad_clear(page, len(name_input.input_value()))
        keypad_type(page, "Cursor")
        keypad_close(page)
        print("name field now:", name_input.input_value())
        assert name_input.input_value() == "Cursor"

        # --- Scene Icon ----------------------------------------------------
        icon_input = modal.locator(".icon-input-group input")
        icon_input.click()
        page.locator(".onscreen-keypad-container").wait_for(
            state="visible", timeout=5000
        )
        keypad_clear(page, len(icon_input.input_value()))
        keypad_type(page, "i-cursor")
        keypad_close(page)
        print("icon field now:", icon_input.input_value())
        assert icon_input.input_value() == "i-cursor"

        # --- Scene Color (input[type=color]: set + dispatch input) --------
        modal.locator("input.color-input").evaluate(
            "el => { el.value = '#1f6fd1';"
            " el.dispatchEvent(new Event('input', {bubbles:true})); }"
        )
        modal.screenshot(path=str(SHOT_DIR / "dl131-scene-editor.png"))

        modal.locator(".modal-footer button.btn-primary").click()
        modal.wait_for(state="hidden", timeout=8000)
        page.wait_for_timeout(1500)  # let saveProfile() PUT land

        labels = page.locator(
            ".glass-pill-scene-selector .segment .segment-label"
        ).all_inner_texts()
        print("scene pills after add:", labels)
        assert "Cursor" in labels, "Cursor pill did not render after UI add"

        page.screenshot(path=str(SHOT_DIR / "dl131-scene-added-ui.png"))
        browser.close()

    # Verify server-side, then patch the original page/buttons back in.
    profile = get_profile()
    print("scenes after UI add (GET):", scene_names(profile))
    new_scene = next(s for s in profile["scenes"] if s["name"] == "Cursor")
    print(f"new scene id={new_scene['id']} icon={new_scene.get('icon')!r} "
          f"color={new_scene.get('color')!r} "
          f"buttons={len(new_scene['pages'][0]['buttons'])} "
          f"grid={new_scene['pages'][0]['grid_config']}")

    # PATCH: original page (8 cursor_* buttons, 4x2 grid) + original
    # transition fields onto the UI-created scene — the sanctioned
    # 'set what the UI cannot express via API' step.
    new_scene["pages"] = ORIG_SCENE["pages"]
    new_scene["transition_style"] = ORIG_SCENE.get("transition_style")
    new_scene["stagger_order"] = ORIG_SCENE.get("stagger_order")
    if ORIG_SCENE.get("overlay_style"):
        new_scene["overlay_style"] = ORIG_SCENE["overlay_style"]
    if ORIG_SCENE.get("appId"):
        new_scene["appId"] = ORIG_SCENE["appId"]

    status, data = put_profile(profile)
    print(f"PATCH PUT -> {status} success={data.get('success')}")
    assert status == 200 and data.get("success"), data

    check = get_profile()
    cur = next(s for s in check["scenes"] if s["name"] == "Cursor")
    btns = cur["pages"][0]["buttons"]
    print(f"patched scene: id={cur['id']} buttons={len(btns)} "
          f"grid={cur['pages'][0]['grid_config']} "
          f"actions={sorted({b['action']['type'] for b in btns})}")
    assert len(btns) == 8 and cur["pages"][0]["grid_config"] == {"cols": 4, "rows": 2}
    print("STEP 2 PASS — scene re-created via UI, bindings restored via API.")


if __name__ == "__main__":
    run()
