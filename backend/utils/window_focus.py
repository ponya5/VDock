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


def foreground_hwnd() -> Optional[int]:
    """HWND of the foreground window right now, or None on non-Windows."""
    if platform.system() != 'Windows':
        return None
    import win32gui

    return win32gui.GetForegroundWindow()


def foreground_exe_live() -> Optional[str]:
    """Exe of the foreground window, read fresh -- not the monitor's cache.

    AppMonitor polls on a seconds-long interval, so a window VDock just raised
    still reports the previous app for a while. Verification right after a
    refocus must not use the cache.
    """
    if platform.system() != 'Windows':
        return None
    import win32process
    import psutil

    hwnd = foreground_hwnd()
    if not hwnd:
        return None
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name().lower()
    except Exception:
        return None


def _visible_windows_by_pid() -> dict:
    """pid -> [(hwnd, title)] for visible, titled top-level windows."""
    import win32gui
    import win32process

    by_pid: dict = {}

    def _callback(hwnd: int, _extra) -> None:
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            by_pid.setdefault(pid, []).append((hwnd, title))
        except Exception:
            return

    win32gui.EnumWindows(_callback, None)
    return by_pid


def _session_pids(marker: str) -> List[int]:
    """PIDs whose name or command line contains ``marker``."""
    import psutil

    needle = marker.lower()
    pids: List[int] = []
    for proc in psutil.process_iter(('name', 'cmdline')):
        try:
            info = proc.info
            if needle in (info.get('name') or '').lower():
                pids.append(proc.pid)
                continue
            cmdline = info.get('cmdline')
            if cmdline and needle in ' '.join(cmdline).lower():
                pids.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied,
                psutil.ZombieProcess):
            continue
    return pids


def find_session_host_window(
    marker: str,
    prefer_title: Optional[str] = None,
) -> Optional[int]:
    """HWND of the top-level window hosting a ``marker`` session process.

    Finds processes matching the marker, then walks each one's ancestor chain
    (checking each ancestor's children too) until a PID owns a visible window.
    That is what makes agent buttons host-agnostic: a claude session inside
    Devin or Cursor's integrated terminal resolves to the Devin/Cursor window,
    one in Windows Terminal resolves to the wt window, and one in a classic
    console resolves to its conhost window -- no exe list needed.

    Windows whose owner IS the session process itself (e.g. the Claude desktop
    app matching 'claude') sort last: a deck button means the hosted terminal
    session, not a standalone app that happens to share the name.
    """
    if platform.system() != 'Windows':
        return None
    import psutil

    needle = (marker or '').lower().strip()
    if not needle:
        return None

    session_pids = _session_pids(needle)
    if not session_pids:
        return None

    win_by_pid = _visible_windows_by_pid()

    # ppid -> children, one pass, so each ancestor's descendants can be checked
    # (the classic console case: the console window belongs to conhost.exe, a
    # child of the session's parent shell, not an ancestor).
    children_of: dict = {}
    for proc in psutil.process_iter(('ppid',)):
        try:
            ppid = proc.info.get('ppid')
            if ppid:
                children_of.setdefault(ppid, []).append(proc.pid)
        except Exception:
            continue

    candidates: List[Tuple[int, str, bool]] = []  # (hwnd, title, self_owned)
    for pid in session_pids:
        try:
            chain = [pid] + [p.pid for p in psutil.Process(pid).parents()]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            chain = [pid]
        found = False
        for anc in chain:
            for owner in [anc] + children_of.get(anc, []):
                for hwnd, title in win_by_pid.get(owner, ()):
                    candidates.append((hwnd, title, owner == pid))
                    found = True
            if found:
                break

    if not candidates:
        return None

    def _rank(item: Tuple[int, str, bool]) -> Tuple[bool, bool]:
        hwnd, title, self_owned = item
        title_miss = bool(
            prefer_title and prefer_title.lower() not in title.lower()
        )
        # Hosted sessions before self-owned apps; title hint last.
        return (self_owned, title_miss)

    candidates.sort(key=_rank)
    return candidates[0][0]
