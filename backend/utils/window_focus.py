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

Session handles (``hwnd`` in the session functions) are opaque: a real HWND on
Windows, the session process's pid on macOS (DL-007) -- macOS has no window
handle a process can address without Accessibility, so the pid stands in and
``focus_hwnd`` resolves it to the hosting app/tab at focus time.
"""
import logging
import os
import platform
import re
import subprocess
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


def _macos_screen_locked() -> bool:
    """True while the Mac shows its lock screen (no permission needed)."""
    try:
        import Quartz
        session = Quartz.CGSessionCopyCurrentDictionary()
    except Exception:  # noqa: BLE001 - unknown means "not known to be locked"
        return False
    return bool(session and session.get('CGSSessionScreenIsLocked'))


def interactive_desktop_blocked() -> bool:
    """True while Windows shows the lock screen or its screensaver.

    Input then goes to a separate desktop ('Winlogon' / 'Screen-saver'), so
    no window can be focused and no keystroke reaches an app -- worth
    telling the user instead of reporting a generic focus failure. macOS:
    the lock screen does the same (DL-009).
    """
    if platform.system() == 'Darwin':
        return _macos_screen_locked()
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
    if platform.system() == 'Darwin':
        return _focus_session_macos(hwnd)
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


_LSAPPINFO_ENTRY = re.compile(r'^\s*\d+\) ', re.MULTILINE)


def _lsappinfo_foreground_apps() -> Optional[List[Tuple[int, str]]]:
    """(pid, bundle path) of every regular app, read fresh from ``lsappinfo``.

    ``NSWorkspace.runningApplications()`` only refreshes while an AppKit run
    loop spins; the backend has none, so an app launched after VDock started
    (a Terminal opened by "Open Claude", Cursor opened later) never showed up
    (DL-007). ``type="Foreground"`` is lsappinfo's name for a regular app.
    None when lsappinfo cannot run.
    """
    try:
        listing = subprocess.run(['lsappinfo', 'list'], capture_output=True,
                                 text=True, timeout=3).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    apps: List[Tuple[int, str]] = []
    for entry in _LSAPPINFO_ENTRY.split(listing)[1:]:
        if 'type="Foreground"' not in entry:
            continue
        path = re.search(r'bundle path="([^"]+)"', entry)
        pid = re.search(r'\bpid = (\d+)', entry)
        if path and pid:
            apps.append((int(pid.group(1)), path.group(1).rstrip('/')))
    return apps


def _macos_foreground_apps() -> List[Tuple[int, str]]:
    """(pid, bundle path) of regular running apps; NSWorkspace as fallback."""
    apps = _lsappinfo_foreground_apps()
    if apps is not None:
        return apps
    from AppKit import NSWorkspace

    regular_policy = 0  # NSApplicationActivationPolicyRegular
    apps = []
    for running_app in NSWorkspace.sharedWorkspace().runningApplications():
        bundle_url = running_app.bundleURL()
        if running_app.activationPolicy() != regular_policy or bundle_url is None:
            continue
        apps.append((int(running_app.processIdentifier()),
                     str(bundle_url.path()).rstrip('/')))
    return apps


def _macos_regular_apps() -> List[Tuple[str, str]]:
    """(identity, bundle path) of every regular running macOS app.

    Identity is the lowercased bundle folder name (``cursor.app``) -- the same
    string the macOS app monitor reports and the keymaps list in their
    ``target_exes``.
    """
    return [(os.path.basename(path).lower(), path)
            for _pid, path in _macos_foreground_apps()]


def _focus_app_window_macos(target_exes: Sequence[str]) -> Optional[bool]:
    wanted = {exe.lower() for exe in target_exes}
    try:
        matches = [path for identity, path in _macos_regular_apps() if identity in wanted]
    except ImportError:
        return None
    if not matches:
        return False
    # ``open -a`` always raises the app and needs no permission, unlike
    # NSRunningApplication.activate, which recent macOS refuses for
    # background processes.
    completed = subprocess.run(['open', '-a', matches[0]], capture_output=True)
    return completed.returncode == 0


def _frontmost_bundle_path_lsappinfo() -> Optional[str]:
    """Frontmost app's bundle path via ``lsappinfo`` (no permission needed).

    ``NSWorkspace.frontmostApplication()`` only refreshes while an AppKit run
    loop spins; the backend has none, so it keeps answering with whatever was
    frontmost at first call and the "is the editor focused" guard goes wrong.
    """
    try:
        front = subprocess.run(['lsappinfo', 'front'], capture_output=True,
                               text=True, timeout=2).stdout.strip()
        if not front.startswith('ASN:'):
            return None
        info = subprocess.run(['lsappinfo', 'info', '-only', 'bundlepath', front],
                              capture_output=True, text=True, timeout=2).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r'bundle path="([^"]+)"', info)
    return match.group(1) if match else None


def _foreground_exe_macos() -> Optional[str]:
    path = _frontmost_bundle_path_lsappinfo()
    if path:
        return os.path.basename(path.rstrip('/')).lower()
    try:
        from AppKit import NSWorkspace
    except ImportError:
        return None
    frontmost = NSWorkspace.sharedWorkspace().frontmostApplication()
    bundle_url = frontmost.bundleURL() if frontmost else None
    if bundle_url is None:
        return None
    return os.path.basename(str(bundle_url.path()).rstrip('/')).lower()


def focus_app_window(
    target_exes: Sequence[str],
    prefer_title: Optional[str] = None,
) -> Optional[bool]:
    """Bring a window of one of ``target_exes`` to the front.

    See the module docstring for the tri-state return.
    """
    if platform.system() == 'Darwin':
        return _focus_app_window_macos(target_exes)
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
    unambiguous. Doesn't steal focus. False on API failure.

    macOS has no titlebar flash for another app's window, so there the
    session's window is brought to the front instead (DL-007).
    """
    if platform.system() == 'Darwin':
        return _focus_session_macos(hwnd)
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
    if platform.system() == 'Darwin':
        return _foreground_exe_macos()
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

#: Terminal apps that can host a *delegated* console (Windows "default
#: terminal" mode). The console window is then owned by the terminal's
#: own process tree — disconnected from the session's ancestors, so the
#: ancestor walk cannot reach it. These hosts title their windows after
#: the hosted app ("✳ Claude Code" for a claude session), which is the
#: only remaining link (DL-111).
_TERMINAL_HOST_EXES = {
    'windowsterminal.exe', 'openconsole.exe', 'wezterm-gui.exe',
    'tabby.exe', 'alacritty.exe', 'hyper.exe', 'fluent-terminal.exe',
    'wave.exe', 'warp.exe',
}

#: Display names for the process that owns a session's host window —
#: shown in the picker so "backend · Cursor" reads different from
#: "backend · Windows Terminal" (DL-071 follow-up 11).
_FRIENDLY_HOST_NAMES = {
    'windowsterminal.exe': 'Windows Terminal',
    'conhost.exe': 'Console',
    'openconsole.exe': 'Console',
    'cursor.exe': 'Cursor',
    'code.exe': 'VS Code',
    'code - insiders.exe': 'VS Code Insiders',
    'windsurf.exe': 'Windsurf',
    'zed.exe': 'Zed',
    'devenv.exe': 'Visual Studio',
    'wezterm-gui.exe': 'WezTerm',
    'alacritty.exe': 'Alacritty',
    'tabby.exe': 'Tabby',
    'warp.exe': 'Warp',
    'hyper.exe': 'Hyper',
    'powershell.exe': 'PowerShell',
    'pwsh.exe': 'PowerShell',
    'cmd.exe': 'Command Prompt',
    'claude.exe': 'Claude',
    'devin.exe': 'Devin',
}


def _host_display_name(owner_pid: Optional[int]) -> Optional[str]:
    """Friendly name of the app owning a session's host window."""
    if not owner_pid:
        return None
    import psutil
    try:
        exe = (psutil.Process(owner_pid).name() or '').lower()
    except Exception:
        return None
    if exe in _FRIENDLY_HOST_NAMES:
        return _FRIENDLY_HOST_NAMES[exe]
    stem = exe[:-4] if exe.endswith('.exe') else exe
    return stem.title() if stem else None


def _delegated_terminal_windows(
    needle: str,
    win_by_pid: dict,
    claimed_hwnds: set,
) -> List[Tuple[int, str]]:
    """(hwnd, title) of marker-titled windows owned by terminal hosts.

    Last-resort pairings for sessions whose console was delegated to an
    external terminal — the host window is unreachable from the session's
    process tree. Only windows not already claimed by the ancestor walk
    are offered, so a normal in-tree host always wins.
    """
    import psutil

    windows: List[Tuple[int, str]] = []
    for pid, wins in win_by_pid.items():
        try:
            exe = psutil.Process(pid).name().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if exe not in _TERMINAL_HOST_EXES:
            continue
        for hwnd, title in wins:
            if needle in title.lower() and hwnd not in claimed_hwnds:
                windows.append((hwnd, title))
    return windows


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
    unresolved: List[Tuple[int, int, float]] = []  # (pid, tier, create_time)
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
        if not found:
            unresolved.append((pid, tier, create_time))

    # Delegated consoles (default-terminal mode): the host window lives on
    # a disconnected terminal-app tree, so only a marker-titled terminal
    # window can stand in. Newest session claims the topmost free window;
    # extra sessions share the last one (several sessions per hwnd is a
    # supported shape).
    if unresolved:
        claimed = {hwnd for _p, hwnd, _t, _s, _ti, _c in candidates}
        free_windows = _delegated_terminal_windows(
            marker.lower(), win_by_pid, claimed)
        if free_windows:
            for i, (pid, tier, create_time) in enumerate(
                    sorted(unresolved, key=lambda u: -u[2])):
                hwnd, title = free_windows[min(i, len(free_windows) - 1)]
                candidates.append((pid, hwnd, title, False, tier, create_time))

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
    needle = (marker or '').lower().strip()
    if not needle:
        return None
    if platform.system() == 'Darwin':
        return _find_session_host_macos(needle, prefer_cwd, prefer_pid)
    if platform.system() != 'Windows':
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


def host_window_for_pid(marker: str, pid: int) -> Optional[int]:
    """HWND hosting exactly the ``marker`` session ``pid``, else None.

    Unlike ``find_session_host_window(prefer_pid=...)`` this never falls back
    to another session: answering an approval prompt in the wrong terminal is
    worse than refusing (DL-012).
    """
    for host in list_session_hosts(marker):
        if host.get('pid') == pid:
            return host.get('hwnd')
    return None


def list_session_hosts(marker: str) -> List[dict]:
    """One row per live ``marker`` session that owns a host window.

    Powers the deck's session picker (DL-071). Windowless sessions --
    headless ``claude -p`` jobs and friends -- are excluded: nothing can be
    typed into them. Newest session first.
    """
    needle = (marker or '').lower().strip()
    if not needle:
        return []
    if platform.system() == 'Darwin':
        rows = _macos_session_hosts(needle)
        return sorted(rows, key=lambda r: -r['create_time'])
    if platform.system() != 'Windows':
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

    # hwnd -> owning process, to name the surface hosting each session.
    owner_by_hwnd: dict = {}
    if by_pid:
        try:
            for owner, wins in _visible_windows_by_pid().items():
                for hwnd, _t in wins:
                    owner_by_hwnd[hwnd] = owner
        except Exception:
            pass

    # Per-session cwd rides along for display and hook matching; it was
    # already read during candidate enumeration, so re-read just it here.
    import psutil
    for pid, row in by_pid.items():
        try:
            row['cwd'] = psutil.Process(pid).cwd()
        except Exception:
            row['cwd'] = None
        row['host'] = _host_display_name(owner_by_hwnd.get(row['hwnd']))

    return sorted(by_pid.values(), key=lambda r: -r['create_time'])


# --------------------------------------------------------------------------
# macOS session hosts (DL-007)
# --------------------------------------------------------------------------

#: Friendly names for host apps whose bundle name reads badly in the picker.
_MACOS_HOST_NAMES = {
    'visual studio code.app': 'VS Code',
    'visual studio code - insiders.app': 'VS Code Insiders',
    'iterm.app': 'iTerm2',
}

#: Terminal apps that can select the exact tab running a tty. AppleScript by
#: bundle id, so a renamed app still resolves. The tty arrives as argv --
#: never pasted into the script text.
_TTY_TAB_SCRIPTS = {
    'terminal.app': """on run argv
    set ttyName to item 1 of argv
    tell application id "com.apple.Terminal"
        repeat with w in windows
            repeat with t in tabs of w
                if tty of t is ttyName then
                    set selected of t to true
                    set index of w to 1
                    activate
                    return "ok"
                end if
            end repeat
        end repeat
    end tell
    return "missing"
end run""",
    'iterm.app': """on run argv
    set ttyName to item 1 of argv
    tell application id "com.googlecode.iterm2"
        repeat with w in windows
            repeat with t in tabs of w
                repeat with s in sessions of t
                    if tty of s is ttyName then
                        tell w to select
                        tell t to select
                        tell s to select
                        activate
                        return "ok"
                    end if
                end repeat
            end repeat
        end repeat
    end tell
    return "missing"
end run""",
}

#: Seconds to wait for the host app to become frontmost after activation.
_MACOS_FRONT_TIMEOUT = 1.5


def _outer_app_bundle(path: Optional[str]) -> Optional[str]:
    """The outermost ``.app`` bundle containing ``path``, or None.

    Outermost, because helpers nest their own bundles: Cursor's integrated
    terminal runs under ``Cursor.app/Contents/Frameworks/Cursor Helper.app``
    -- the window belongs to ``Cursor.app``.
    """
    if not path:
        return None
    index = path.find('.app/')
    if index >= 0:
        return path[:index + len('.app')]
    stripped = path.rstrip('/')
    return stripped if stripped.endswith('.app') else None


def _macos_regular_app_pids() -> dict:
    """lowercased bundle path -> (pid, bundle path) of regular running apps."""
    return {path.lower(): (pid, path) for pid, path in _macos_foreground_apps()}


def _macos_host_app(proc, regular: dict) -> Optional[Tuple[int, str]]:
    """(app pid, bundle path) of the GUI app hosting ``proc``, or None.

    Walks the process and its ancestors until an executable lives inside a
    running regular app: Terminal (via ``login``), iTerm2 (its daemonised
    ``iTermServer`` still lives in ``iTerm.app``), Cursor / VS Code (pty host
    helpers), Warp... No app list, so any terminal or editor works. A
    session with no such ancestor (headless ``claude -p``, tmux) has no
    window to type into.
    """
    import psutil

    try:
        chain = [proc] + proc.parents()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        chain = [proc]
    for ancestor in chain:
        try:
            bundle = _outer_app_bundle(ancestor.exe())
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
            continue
        if bundle and bundle.lower() in regular:
            return regular[bundle.lower()]
    return None


def _macos_host_name(bundle_path: str) -> str:
    identity = os.path.basename(bundle_path).lower()
    if identity in _MACOS_HOST_NAMES:
        return _MACOS_HOST_NAMES[identity]
    return os.path.basename(bundle_path)[:-len('.app')] or identity


def _macos_session_hosts(marker: str, prefer_cwd: Optional[str] = None) -> List[dict]:
    """One row per live ``marker`` session hosted by a GUI app.

    ``hwnd`` is the session pid (see the module docstring); ``title`` is
    built from host + project because reading another app's window titles
    needs Accessibility.
    """
    import psutil

    try:
        regular = _macos_regular_app_pids()
    except ImportError:
        return []
    rows: List[dict] = []
    for pid in _session_pids(marker):
        try:
            proc = psutil.Process(pid)
            host = _macos_host_app(proc, regular)
            if host is None:
                continue
            create_time = float(proc.create_time())
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        try:
            cwd = proc.cwd()
        except (psutil.Error, OSError):
            cwd = None
        app_pid, bundle = host
        host_name = _macos_host_name(bundle)
        project = os.path.basename(cwd.rstrip('/')) if cwd else ''
        rows.append({
            'pid': pid,
            'hwnd': pid,
            'title': f'{host_name} \u2014 {project}' if project else host_name,
            'self_owned': False,
            'create_time': create_time,
            'cwd': cwd,
            'host': host_name,
            'tier': _cwd_tier(cwd, prefer_cwd),
            'app_pid': app_pid,
            'bundle': bundle,
        })
    return rows


def _find_session_host_macos(
    marker: str,
    prefer_cwd: Optional[str],
    prefer_pid: Optional[int],
) -> Optional[int]:
    """Same ranking as Windows: pin, project directory, newest session."""
    rows = _macos_session_hosts(marker, prefer_cwd)
    if not rows:
        return None
    if prefer_pid is not None:
        for row in rows:
            if row['pid'] == prefer_pid:
                return row['hwnd']
    rows.sort(key=lambda r: (r['tier'], -r['create_time']))
    return rows[0]['hwnd']


def _select_tty_tab(identity: str, tty: Optional[str]) -> bool:
    """Bring the Terminal / iTerm2 tab running ``tty`` to the front.

    Needs the Automation permission (macOS asks once). Denied, timed out or
    tab gone -> False and the caller falls back to activating the app.
    """
    script = _TTY_TAB_SCRIPTS.get(identity)
    if not script or not tty:
        return False
    try:
        completed = subprocess.run(['osascript', '-e', script, tty],
                                   capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False
    if completed.returncode != 0:
        logger.info('Could not select the %s tab for %s: %s',
                    identity, tty, completed.stderr.strip())
        return False
    return completed.stdout.strip() == 'ok'


def _project_names(cwd: Optional[str]) -> List[str]:
    """The cwd's folder name and its parents' (nearest first), below $HOME.

    VS Code-family windows are titled after the workspace root, which may sit
    above the directory the session was started in.
    """
    if not cwd:
        return []
    home = os.path.expanduser('~').rstrip('/')
    names: List[str] = []
    path = cwd.rstrip('/')
    while path and path != home and path != '/' and len(names) < 4:
        names.append(os.path.basename(path))
        path = os.path.dirname(path)
    return names


def _title_names_project(title: str, project: str) -> bool:
    """True when a window title has ``project`` as one of its segments.

    VS Code-family titles read ``file.py \u2014 project`` (plus optional
    suffixes); a bare substring test would let ``app`` match ``webapp``.
    """
    segments = re.split(r'\s+[\u2014\u2013-]\s+', title)
    return any(segment.strip().split(' [')[0] == project for segment in segments)


def _raise_project_window(app_pid: int, cwd: Optional[str]) -> bool:
    """Raise the host app's window titled after the session's project.

    Accessibility API -- only when this process is trusted (the same grant
    keystrokes need). Without it the app's last-used window comes forward.
    """
    names = _project_names(cwd)
    if not names:
        return False
    try:
        from ApplicationServices import (
            AXIsProcessTrusted, AXUIElementCopyAttributeValue,
            AXUIElementCreateApplication, AXUIElementPerformAction,
            AXUIElementSetAttributeValue, kAXMainAttribute, kAXRaiseAction,
            kAXTitleAttribute, kAXWindowsAttribute,
        )
    except ImportError:
        return False
    try:
        if not AXIsProcessTrusted():
            return False
        app = AXUIElementCreateApplication(app_pid)
        error, windows = AXUIElementCopyAttributeValue(app, kAXWindowsAttribute, None)
        if error or not windows:
            return False
        titled = []
        for window in windows:
            error, title = AXUIElementCopyAttributeValue(window, kAXTitleAttribute, None)
            titled.append((window, str(title or '') if not error else ''))
        for name in names:
            for window, title in titled:
                if _title_names_project(title, name):
                    AXUIElementSetAttributeValue(window, kAXMainAttribute, True)
                    AXUIElementPerformAction(window, kAXRaiseAction)
                    return True
    except Exception as error:  # noqa: BLE001 - best effort; app activation follows
        logger.debug('Accessibility window raise failed: %s', error)
    return False


def _wait_frontmost(bundle_path: str, timeout: float = _MACOS_FRONT_TIMEOUT) -> bool:
    """True once ``bundle_path`` is the frontmost app (None-safe)."""
    deadline = time.time() + timeout
    wanted = bundle_path.rstrip('/').lower()
    while True:
        front = _frontmost_bundle_path_lsappinfo()
        if front is None:
            return True  # cannot read the front app -- trust the activation
        if front.rstrip('/').lower() == wanted:
            return True
        if time.time() >= deadline:
            logger.warning('macOS kept %s in front instead of %s', front, bundle_path)
            return False
        time.sleep(0.1)


#: Editors that host Claude Code in an integrated terminal pane: the app is
#: in front, but keystrokes go to whichever pane has focus (DL-009).
_EDITOR_HOST_IDENTITIES = frozenset({
    'cursor.app', 'visual studio code.app', 'visual studio code - insiders.app',
    'vscodium.app', 'windsurf.app', 'antigravity.app',
})

#: Why the last macOS focus attempt was refused - shown to the user.
_last_focus_problem: Optional[str] = None


def last_focus_problem() -> Optional[str]:
    return _last_focus_problem


def _ax_terminal_focused(app_pid: int) -> Optional[bool]:
    """Whether an editor's focused element is its integrated terminal.

    VS Code-family apps expose xterm's input as a textarea with class
    ``xterm-helper-textarea`` described "Terminal N, <process>" (read from
    Cursor 3.25's accessibility tree). None when it can't be told.
    """
    try:
        from ApplicationServices import (
            AXIsProcessTrusted, AXUIElementCopyAttributeValue,
            AXUIElementCreateApplication, AXUIElementSetAttributeValue,
        )
    except ImportError:
        return None
    try:
        if not AXIsProcessTrusted():
            return None
        app = AXUIElementCreateApplication(app_pid)
        # Electron builds its accessibility tree only when asked.
        AXUIElementSetAttributeValue(app, 'AXManualAccessibility', True)
        focused = None
        for _attempt in range(6):
            error, focused = AXUIElementCopyAttributeValue(app, 'AXFocusedUIElement', None)
            if not error and focused is not None:
                break
            time.sleep(0.1)
        if focused is None:
            return None
        error, classes = AXUIElementCopyAttributeValue(focused, 'AXDOMClassList', None)
        if not error and classes is not None and 'xterm-helper-textarea' in [str(c) for c in classes]:
            return True
        error, description = AXUIElementCopyAttributeValue(focused, 'AXDescription', None)
        return bool(not error and str(description or '').startswith('Terminal '))
    except Exception as error:  # noqa: BLE001 - unknown = let the caller decide
        logger.debug('Could not read the focused element: %s', error)
        return None


def session_input_focused(handle: int) -> Optional[bool]:
    """Will keystrokes reach the session's terminal? (macOS, DL-009)

    False only when the session runs in an editor's integrated terminal and
    the editor's focus is elsewhere (the open file, the chat) - typing there
    would edit a file. None when it doesn't apply or can't be told.
    """
    if platform.system() != 'Darwin':
        return None
    import psutil

    try:
        host = _macos_host_app(psutil.Process(int(handle)), _macos_regular_app_pids())
    except (ImportError, psutil.Error, TypeError, ValueError):
        return None
    if host is None or os.path.basename(host[1]).lower() not in _EDITOR_HOST_IDENTITIES:
        return None
    return _ax_terminal_focused(host[0])


def _visible_window_count(app_pid: int) -> Optional[int]:
    """On-screen normal windows of an app (no permission needed)."""
    try:
        from Quartz import (
            CGWindowListCopyWindowInfo, kCGNullWindowID,
            kCGWindowListExcludeDesktopElements, kCGWindowListOptionOnScreenOnly,
        )
    except ImportError:
        return None
    windows = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements, kCGNullWindowID)
    return sum(1 for w in windows or []
               if w.get('kCGWindowOwnerPID') == app_pid and w.get('kCGWindowLayer') == 0)


def session_host_frontmost(handle: int) -> Optional[bool]:
    """Whether the app hosting session ``handle`` is frontmost (macOS).

    None where it cannot be told -- Windows compares HWNDs directly via
    ``foreground_hwnd`` instead.
    """
    if platform.system() != 'Darwin':
        return None
    import psutil

    try:
        host = _macos_host_app(psutil.Process(int(handle)), _macos_regular_app_pids())
    except (ImportError, psutil.Error, TypeError, ValueError):
        return None
    front = _frontmost_bundle_path_lsappinfo()
    if host is None or front is None:
        return None
    in_front = front.rstrip('/').lower() == host[1].lower()
    if not in_front:
        logger.warning('Session %s lives in %s but %s is in front', handle, host[1], front)
    return in_front


def _focus_session_macos(session_pid: int) -> bool:
    """Bring the window hosting ``session_pid`` to the front (macOS).

    Terminal / iTerm2 select the session's exact tab by tty; editors raise
    the window named after the project; then the app is activated and the
    result verified -- the caller types into whatever is frontmost.
    """
    import psutil

    try:
        regular = _macos_regular_app_pids()
        proc = psutil.Process(int(session_pid))
        host = _macos_host_app(proc, regular)
    except (ImportError, psutil.Error, TypeError, ValueError):
        return False
    if host is None:
        return False
    app_pid, bundle = host
    try:
        tty = proc.terminal()
    except (psutil.Error, OSError):
        tty = None
    try:
        cwd = proc.cwd()
    except (psutil.Error, OSError):
        cwd = None
    identity = os.path.basename(bundle).lower()
    global _last_focus_problem
    _last_focus_problem = None
    if not _select_tty_tab(identity, tty):
        if identity in _TTY_TAB_SCRIPTS and (_visible_window_count(app_pid) or 0) > 1:
            # Without the exact tab, activating the app brings forward its
            # last-used window - with several open that may be another
            # shell. Refuse rather than guess (DL-009).
            name = _macos_host_name(bundle)
            _last_focus_problem = (
                f'Several {name} windows are open and macOS did not let VDock pick '
                f'the one running the session. Allow VDock to control {name} under '
                'System Settings > Privacy & Security > Automation, or close the '
                'other windows.')
            return False
        _raise_project_window(app_pid, cwd)
    # ``open -a`` activates without any permission (NSRunningApplication
    # activation is refused for background processes on recent macOS).
    try:
        subprocess.run(['open', '-a', bundle], capture_output=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False
    return _wait_frontmost(bundle)
