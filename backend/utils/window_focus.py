"""Bring a target application's window to the foreground.

VDock buttons are pressed on a touch panel (or a browser window) -- the press
itself steals focus, so "send keys to the focused window" can never work on
its own. The deck has to put the target window back in front first, which is
what this module does on Windows.

`focus_app_window` returns a tri-state:

* ``True``  -- a matching window was found and is now foreground;
* ``False`` -- supported platform, but no matching window exists;
* ``None``  -- focusing is not implemented on this platform, so the caller
  should fall back to its old "already focused?" check.
"""
import logging
import platform
import time
from typing import List, Optional, Sequence, Tuple

logger = logging.getLogger('vdock')


def _enum_windows_windows(
    target_exes: Sequence[str],
) -> List[Tuple[int, str, str]]:
    """Visible top-level windows owned by ``target_exes``, in Z order."""
    import win32gui
    import win32process
    import psutil

    lowered = {exe.lower() for exe in target_exes}
    found: List[Tuple[int, str, str]] = []

    def _callback(hwnd: int, _extra) -> None:
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            exe = psutil.Process(pid).name().lower()
            if exe in lowered:
                found.append((hwnd, exe, title))
        except Exception:
            # A window can vanish or deny its pid mid-enumeration.
            return

    win32gui.EnumWindows(_callback, None)
    return found


def find_target_window(
    target_exes: Sequence[str],
    prefer_title: Optional[str] = None,
) -> Optional[int]:
    """HWND of the best matching window, or None.

    ``prefer_title`` lets a caller disambiguate several windows of the same
    process -- e.g. prefer the terminal tab whose title mentions 'claude'
    over other terminal windows.
    """
    if platform.system() != 'Windows':
        return None
    try:
        matches = _enum_windows_windows(target_exes)
    except Exception as e:
        logger.warning('Could not enumerate windows: %s', e)
        return None
    if not matches:
        return None
    if prefer_title:
        needle = prefer_title.lower()
        matches.sort(key=lambda m: needle not in m[2].lower())
    return matches[0][0]


def focus_hwnd(hwnd: int) -> bool:
    """Force ``hwnd`` to the foreground. Returns True when it got there.

    Windows only lets a process set the foreground window under narrow
    conditions; attaching to the foreground thread's input queue is the
    standard way to satisfy them.
    """
    import win32api
    import win32con
    import win32gui
    import win32process

    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        foreground = win32gui.GetForegroundWindow()
        attached = False
        if foreground and foreground != hwnd:
            fg_thread = win32process.GetWindowThreadProcessId(foreground)[0]
            current_thread = win32api.GetCurrentThreadId()
            if fg_thread != current_thread:
                win32process.AttachThreadInput(
                    current_thread, fg_thread, True
                )
                attached = True
        try:
            win32gui.BringWindowToTop(hwnd)
            win32gui.SetForegroundWindow(hwnd)
        finally:
            if attached:
                win32process.AttachThreadInput(
                    current_thread, fg_thread, False
                )

        time.sleep(0.05)
        return win32gui.GetForegroundWindow() == hwnd
    except Exception as e:
        logger.warning('Could not focus window %s: %s', hwnd, e)
        return False


def focus_app_window(
    target_exes: Sequence[str],
    prefer_title: Optional[str] = None,
) -> Optional[bool]:
    """Bring a window of one of ``target_exes`` to the front.

    See the module docstring for the tri-state return.
    """
    if platform.system() != 'Windows':
        return None
    hwnd = find_target_window(target_exes, prefer_title=prefer_title)
    if not hwnd:
        return False
    return focus_hwnd(hwnd)
