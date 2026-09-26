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
import os
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


def interactive_desktop_blocked() -> bool:
    """True while Windows shows the lock screen or its screensaver.

    Input then goes to a separate desktop ('Winlogon' / 'Screen-saver'), so
    no window can be focused and no keystroke reaches an app -- worth
    telling the user instead of reporting a generic focus failure.
    """
    if platform.system() != 'Windows':
        return False
    import ctypes
    import ctypes.wintypes

    user32 = ctypes.windll.user32
    desktop_read_objects = 0x0001
    user_object_name = 2
    desktop = user32.OpenInputDesktop(0, False, desktop_read_objects)
    if not desktop:
        # Access denied to the input desktop is itself the lock screen.
        return True
    try:
        name_buffer = ctypes.create_unicode_buffer(256)
        needed = ctypes.wintypes.DWORD()
        if not user32.GetUserObjectInformationW(
                desktop, user_object_name, name_buffer,
                ctypes.sizeof(name_buffer), ctypes.byref(needed)):
            return False
        return name_buffer.value.lower() != 'default'
    finally:
        user32.CloseDesktop(desktop)


def _attach_input(current_thread: int, foreground_thread: int) -> bool:
    """Share the foreground thread's input state, when Windows allows it.

    Some foreground apps refuse the attach (Access is denied), e.g. the
    Claude desktop app. That must only skip this step, not abort the Alt-tap
    and minimise/restore fallbacks that follow.
    """
    import win32process

    try:
        return bool(win32process.AttachThreadInput(current_thread, foreground_thread, True))
    except Exception as error:  # noqa: BLE001 - pywintypes.error on refusal
        logger.debug('AttachThreadInput refused: %s', error)
        return False


def _try_set_foreground(hwnd: int) -> bool:
    """One SetForegroundWindow attempt, attached to the foreground thread's
    input queue. pywin32 raises when Windows refuses; that is a normal
    outcome here, not an error."""
    import win32api
    import win32gui
    import win32process

    foreground = win32gui.GetForegroundWindow()
    attached = False
    foreground_thread = current_thread = 0
    if foreground and foreground != hwnd:
        foreground_thread = win32process.GetWindowThreadProcessId(foreground)[0]
        current_thread = win32api.GetCurrentThreadId()
        if foreground_thread != current_thread:
            attached = _attach_input(current_thread, foreground_thread)
    try:
        win32gui.BringWindowToTop(hwnd)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:  # noqa: BLE001 - refusal is signalled by raising
        pass
    finally:
        if attached:
            win32process.AttachThreadInput(current_thread, foreground_thread, False)
    time.sleep(0.05)
    return win32gui.GetForegroundWindow() == hwnd


def _tap_alt_key() -> None:
    """Synthesise an Alt press/release.

    Windows' foreground lock only lets the process that received the last
    input event change the foreground window. The backend never receives
    input -- the user tapped the deck -- so a synthetic keystroke from this
    process is what unlocks SetForegroundWindow. Alt alone has no side
    effect once released (it is swallowed before any menu opens because a
    focus change follows immediately).
    """
    import win32api
    import win32con

    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_EXTENDEDKEY, 0)
    win32api.keybd_event(
        win32con.VK_MENU, 0,
        win32con.KEYEVENTF_EXTENDEDKEY | win32con.KEYEVENTF_KEYUP, 0,
    )


def _minimise_and_restore(hwnd: int) -> None:
    """Last resort: a restore from minimised is always allowed to activate."""
    import win32con
    import win32gui

    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)


def focus_hwnd(hwnd: int) -> bool:
    """Force ``hwnd`` to the foreground. Returns True when it got there.

    Windows only lets a process set the foreground window under narrow
    conditions, so this escalates: plain attach-and-set, then unlock the
    foreground lock with a synthetic Alt tap, then minimise/restore.
    """
    import win32con
    import win32gui

    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        if _try_set_foreground(hwnd):
            return True
        _tap_alt_key()
        if _try_set_foreground(hwnd):
            return True
        _minimise_and_restore(hwnd)
        time.sleep(0.15)
        if _try_set_foreground(hwnd):
            return True
        logger.warning('Windows refused to focus window %s', hwnd)
        return False
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


def flash_window(hwnd: int, count: int = 4) -> bool:
    """Blink a window's titlebar + taskbar button ``count`` times.

    The session picker's "which one is this" affordance (DL-071): a human
    can't map a pid to a physical terminal, but a flashing window is
    unambiguous. Doesn't steal focus. False off Windows or on API failure.
    """
    if platform.system() != 'Windows':
        return False
    import ctypes

    class FLASHWINFO(ctypes.Structure):
        _fields_ = [
            ('cbSize', ctypes.c_uint),
            ('hwnd', ctypes.c_void_p),
            ('dwFlags', ctypes.c_uint),
            ('uCount', ctypes.c_uint),
            ('dwTimeout', ctypes.c_uint),
        ]

    FLASHW_ALL = 0x00000003  # titlebar caption + taskbar button
    try:
        info = FLASHWINFO(
            cbSize=ctypes.sizeof(FLASHWINFO),
            hwnd=hwnd,
            dwFlags=FLASHW_ALL,
            uCount=count,
            dwTimeout=0,
        )
        return bool(ctypes.windll.user32.FlashWindowEx(ctypes.byref(info)))
    except Exception as e:  # noqa: BLE001 - cosmetic affordance, never fatal
        logger.debug('FlashWindowEx failed for %s: %s', hwnd, e)
        return False


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
    """PIDs of live ``marker`` session processes.

    Delegates to ``integrations.sessions`` so window resolution and the
    ``session_alive`` gate share one definition of what a session is --
    the tightened matcher ignores the desktop app and helper processes
    that merely mention the marker. Imported lazily: utils must not grow
    a hard dependency on the integrations package.
    """
    from integrations import sessions

    return sessions.iter_session_pids(marker)


def _cwd_tier(session_cwd: Optional[str], prefer_cwd: Optional[str]) -> int:
    """How well a session's working directory matches the preferred one.

    0 -- exact match;
    1 -- the session sits at or above the project directory (e.g. the
         session was launched in the repo root, the button resolved a
         subdirectory);
    2 -- the session is nested inside the preferred directory;
    3 -- unrelated, or no preference was given.
    """
    if not session_cwd or not prefer_cwd:
        return 3
    a = os.path.normcase(os.path.normpath(session_cwd))
    b = os.path.normcase(os.path.normpath(prefer_cwd))
    if a == b:
        return 0
    if b.startswith(a + os.sep):
        return 1
    if a.startswith(b + os.sep):
        return 2
    return 3


#: Ancestors that are shell roots, not session hosts: enumerating their
#: children would admit every unrelated top-level window as a candidate.
_NON_HOST_ANCESTORS = {'explorer.exe'}


def _session_host_candidates(
    marker: str,
    prefer_cwd: Optional[str] = None,
) -> List[Tuple[int, int, str, bool, int, float]]:
    """(pid, hwnd, title, self_owned, cwd_tier, create_time) per host window.

    Finds processes matching the marker, then walks each one's ancestor chain
    (checking each ancestor's children too) until a PID owns a visible window.
    That is what makes agent buttons host-agnostic: a claude session inside
    Devin or Cursor's integrated terminal resolves to the Devin/Cursor window,
    one in Windows Terminal resolves to the wt window, and one in a classic
    console resolves to its conhost window -- no exe list needed.

    Several windows can share one session (a process and its children can own
    more than one), and several sessions can share one window (two agent tabs
    in the same terminal map both pids to the same hwnd).
    """
    import psutil

    session_pids = _session_pids(marker)
    if not session_pids:
        return []

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

    candidates: List[Tuple[int, int, str, bool, int, float]] = []
    for pid in session_pids:
        sess_cwd: Optional[str] = None
        create_time = 0.0
        try:
            proc = psutil.Process(pid)
            parents = proc.parents()
            chain = [pid] + [p.pid for p in parents]
            try:
                cwd = proc.cwd()
                sess_cwd = cwd if isinstance(cwd, str) else None
            except Exception:
                pass
            try:
                create_time = float(proc.create_time())
            except Exception:
                pass
            chain_names = {pid: (proc.name() or '').lower()}
            for p in parents:
                try:
                    chain_names[p.pid] = (p.name() or '').lower()
                except Exception:
                    pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            chain = [pid]
            chain_names = {}
        tier = _cwd_tier(sess_cwd, prefer_cwd)
        found = False
        for anc in chain:
            if chain_names.get(anc) in _NON_HOST_ANCESTORS:
                # A shell root's children are every app on the desktop --
                # not this session's host window. Stop walking here.
                break
            for owner in [anc] + children_of.get(anc, []):
                for hwnd, title in win_by_pid.get(owner, ()):
                    candidates.append(
                        (pid, hwnd, title, owner == pid, tier, create_time))
                    found = True
            if found:
                break

    return candidates


def find_session_host_window(
    marker: str,
    prefer_title: Optional[str] = None,
    prefer_cwd: Optional[str] = None,
    prefer_pid: Optional[int] = None,
) -> Optional[int]:
    """HWND of the top-level window hosting a ``marker`` session process.

    Windows whose owner IS the session process itself (e.g. the Claude desktop
    app matching 'claude') sort last: a deck button means the hosted terminal
    session, not a standalone app that happens to share the name.

    With several sessions running, ``prefer_cwd`` picks the one whose working
    directory matches (or nests inside) the button's project; remaining ties
    break toward the most recently started session rather than process
    enumeration order.

    ``prefer_pid`` (DL-071: the pinned deck target) beats every ranking
    signal -- when that session owns a host window it wins outright; a pinned
    session without a window (minimised host gone, headless job) falls back
    to normal ranking instead of dead-ending the press.
    """
    if platform.system() != 'Windows':
        return None

    needle = (marker or '').lower().strip()
    if not needle:
        return None

    candidates = _session_host_candidates(needle, prefer_cwd)

    if not candidates:
        return None

    if prefer_pid is not None:
        for pid, hwnd, _title, _self_owned, _tier, _created in candidates:
            if pid == prefer_pid:
                return hwnd

    def _rank(item: Tuple[int, int, str, bool, int, float]) -> tuple:
        _pid, _hwnd, title, self_owned, cwd_tier, create_time = item
        title_miss = bool(
            prefer_title and prefer_title.lower() not in title.lower()
        )
        # Project-matching session first, hosted before self-owned apps,
        # title hint, then newest session as a deterministic tiebreak.
        return (cwd_tier, self_owned, title_miss, -create_time)

    candidates.sort(key=_rank)
    return candidates[0][1]


def list_session_hosts(marker: str) -> List[dict]:
    """One row per live ``marker`` session that owns a host window.

    Powers the deck's session picker (DL-071). Windowless sessions --
    headless ``claude -p`` jobs and friends -- are excluded: nothing can be
    typed into them. Newest session first.
    """
    if platform.system() != 'Windows':
        return []

    needle = (marker or '').lower().strip()
    if not needle:
        return []

    by_pid: dict = {}
    for pid, hwnd, title, self_owned, _tier, create_time in _session_host_candidates(needle):
        row = by_pid.setdefault(pid, {
            'pid': pid,
            'hwnd': hwnd,
            'title': title,
            'self_owned': self_owned,
            'create_time': create_time,
        })
        # A self-owned window would mean the process IS an app (desktop app
        # shape); a hosted terminal window is the better row to show.
        if row['self_owned'] and not self_owned:
            row.update({'hwnd': hwnd, 'title': title, 'self_owned': False})

    # Per-session cwd rides along for display and hook matching; it was
    # already read during candidate enumeration, so re-read just it here.
    import psutil
    for pid, row in by_pid.items():
        try:
            row['cwd'] = psutil.Process(pid).cwd()
        except Exception:
            row['cwd'] = None

    return sorted(by_pid.values(), key=lambda r: -r['create_time'])
