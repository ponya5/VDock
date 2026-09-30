"""Cross-platform system actions for shutdown, restart, sleep, lock, volume, brightness, and media control."""
import platform
import queue
import re
import subprocess
import os
import sys
import threading
import time
from typing import Dict, Any, Optional
from .base_action import BaseAction, ActionResult

# Platform detection
_SYSTEM = platform.system()

# Windows API imports for media keys
if _SYSTEM == 'Windows':
    try:
        import ctypes
        from ctypes import wintypes
        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP = 0x0002
        VK_VOLUME_MUTE = 0xAD
        VK_VOLUME_DOWN = 0xAE  
        VK_VOLUME_UP = 0xAF
        VK_MEDIA_NEXT_TRACK = 0xB0
        VK_MEDIA_PREV_TRACK = 0xB1
        VK_MEDIA_STOP = 0xB2
        VK_MEDIA_PLAY_PAUSE = 0xB3
        WINDOWS_API_AVAILABLE = True
    except:
        WINDOWS_API_AVAILABLE = False
else:
    WINDOWS_API_AVAILABLE = False


# Dedicated COM apartment thread for Core Audio (pycaw). IAudioEndpointVolume
# pointers must be created AND released on the same initialized thread —
# creating them on Flask workers left __del__→Release() to GC on arbitrary
# threads, which raised access violations and could kill the process silently.
#
# What makes this subtle: comtypes pointer wrappers are self-cycled (their
# bound-method cache points back at the instance), so refcounting NEVER frees
# them — only the cyclic GC does, on whatever thread happens to collect, and
# __del__→Release() off the owning apartment is the access violation. `del`
# is therefore useless as cleanup. The guard below defers every off-worker
# __del__ back onto this thread's job queue, and _release_com marks wrappers
# so a second release can never fire.
_audio_worker_lock = threading.Lock()
_audio_worker_thread = None
_audio_worker_queue = None
_worker_tid = None


def _release_com(*ptrs):
    """Release() COM pointers on the calling thread and disarm the wrapper.

    The ``_vdock_released`` flag makes the patched __del__ skip any later
    release — without it, GC of the (self-cycled) wrapper would Release()
    the already-freed object, the same access violation from the other side.
    """
    for p in ptrs:
        if p is None or getattr(p, '__dict__', {}).get('_vdock_released'):
            continue
        try:
            p._vdock_released = True
            p.Release()
        except Exception:
            pass


def _install_com_gc_guard():
    """Defer off-thread COM pointer finalization to the audio worker.

    A wrapper GC'd on a foreign thread would Release() outside the owning
    apartment → access violation. The patched __del__ instead enqueues the
    release onto the audio worker (same `(fn, done, box)` job shape), so
    pycaw-internal pointers this code cannot reach are also made safe.
    Runs on the worker or before it exists → fall through to the original.
    """
    if _SYSTEM != 'Windows':
        return
    try:
        from comtypes._post_coinit.unknwn import _compointer_base
    except ImportError:
        try:
            # Private module moved (older/newer comtypes): fish the base out
            # of a pointer class's MRO instead.
            from ctypes import POINTER
            import comtypes
            _compointer_base = next(
                c for c in POINTER(comtypes.IUnknown).mro()
                if c.__name__ == '_compointer_base')
        except Exception:
            return
    if getattr(_compointer_base, '_vdock_guard', False):
        return
    orig_del = _compointer_base.__del__

    def _com_pointer_del(self, _debug=None):
        if self.__dict__.get('_vdock_released') or not self:
            return
        if (_worker_tid is not None
                and threading.get_ident() != _worker_tid
                and _audio_worker_queue is not None):
            try:
                done = threading.Event()
                _audio_worker_queue.put_nowait(
                    (lambda ctx: _release_com(self), done, {}))
                return  # the worker will release it; wrapper stays inert
            except Exception:
                pass
        orig_del(self)

    _compointer_base.__del__ = _com_pointer_del
    _compointer_base._vdock_guard = True


_install_com_gc_guard()


def _audio_worker_loop(work_q):
    """Single-tenant COM thread: initialize once, own the endpoint lifecycle."""
    global _worker_tid
    import comtypes
    import gc as _gc
    comtypes.CoInitialize()
    _worker_tid = threading.get_ident()

    # Cached endpoint + how it gets invalidated. Per-call re-resolution was
    # tried and abandoned: on a machine whose wireless headset flaps the
    # default output, every CoCreateInstance/Activate rolls the dice on an
    # access violation. Hold the endpoint; Windows tells us when the default
    # render device changes, and a TTL hedge covers notifications that never
    # arrive.
    state = {'endpoint': None, 'resolved_at': 0.0}
    dirty = {'device': True}
    ENDPOINT_TTL_SECONDS = 60
    # Flap guard: while a device is connecting/disconnecting the default
    # endpoint can change repeatedly; each resolve creates COM pointers, and
    # pointer churn on an unstable stack is the crash fuel. Never resolve
    # more often than this — the stale endpoint (or a clean error) is served
    # until the gap has passed.
    RESOLVE_MIN_GAP_SECONDS = 3.0

    def _notifier_thread():
        """Owns the IMMNotificationClient. MTA so Windows dispatches
        callbacks on COM threads without needing a message pump on this
        thread — the callback only flips a Python flag, no COM calls."""
        try:
            comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
        except Exception:
            return
        try:
            from pycaw.callbacks import MMNotificationClient
            from pycaw.api.mmdeviceapi import IMMDeviceEnumerator
            from pycaw.constants import CLSID_MMDeviceEnumerator

            class _Notifier(MMNotificationClient):
                def on_default_device_changed(
                        self, flow, flow_id, role, role_id, device_id):
                    # eRender + eMultimedia/eConsole — the roles volume uses
                    if flow == 'eRender' and role in ('eMultimedia', 'eConsole'):
                        dirty['device'] = True
            enumerator = comtypes.CoCreateInstance(
                CLSID_MMDeviceEnumerator, IMMDeviceEnumerator,
                comtypes.CLSCTX_INPROC_SERVER)
            notifier = _Notifier()
            enumerator.RegisterEndpointNotificationCallback(notifier)
            # Park forever — the frame keeps enumerator + notifier alive.
            threading.Event().wait()
        except Exception:
            pass  # TTL refresh still covers device switches

    threading.Thread(
        target=_notifier_thread, name='vdock-audio-notify', daemon=True
    ).start()

    def get_endpoint():
        """The cached default render endpoint; re-resolve only when dirty.

        Dirty sources: the device-change notification, a failed op (callers
        invalidate via ctx['invalidate']()), or the TTL. The pointer is
        created on this thread and stays referenced here until replaced —
        the DL-058 crash class does not apply to an object that never dies.
        """
        now = time.time()
        stale = dirty['device'] or (now - state['resolved_at'] > ENDPOINT_TTL_SECONDS)
        if now - state['resolved_at'] < RESOLVE_MIN_GAP_SECONDS:
            if state['endpoint'] is not None:
                return state['endpoint'], None
            return None, 'Audio device is still settling'
        if state['endpoint'] is not None and not stale:
            return state['endpoint'], None

        devices = interface = endpoint = None
        ok = False
        try:
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            # QueryInterface, not cast(): cast aliases Activate's single
            # native reference, so releasing `interface` would free the COM
            # object out from under `endpoint` (vtable reads 0xFFFF...).
            # QI gives endpoint its own reference — interface can be
            # released safely below.
            endpoint = interface.QueryInterface(IAudioEndpointVolume)
            ok = True
        except ImportError:
            return None, 'pycaw not installed (pip install pycaw)'
        except Exception as e:
            return None, f'Audio device unavailable: {e}'
        finally:
            _release_com(devices, interface)
            if not ok:
                _release_com(endpoint)
        if ok:
            _release_com(state['endpoint'])
            state['endpoint'] = endpoint
            state['resolved_at'] = time.time()
            dirty['device'] = False
        return state['endpoint'], None

    def invalidate():
        dirty['device'] = True
        _release_com(state['endpoint'])
        state['endpoint'] = None

    def endpoint_op(fn):
        """Run fn(endpoint) against the cached endpoint; on failure invalidate
        and retry once against a freshly-resolved one. Returns (result, err)
        where result is whatever fn returned."""
        endpoint, err = get_endpoint()
        if endpoint is None:
            return None, err
        try:
            return fn(endpoint), None
        except Exception as e:
            invalidate()
            endpoint, err = get_endpoint()
            if endpoint is None:
                return None, err or str(e)
            try:
                return fn(endpoint), None
            except Exception as e2:
                invalidate()
                return None, str(e2)

    def app_volume(process, set_value=None):
        """Per-app session volume. set_value 0.0-1.0 or None to read.

        Returns (percent | True, None) or (None, error)."""
        try:
            from pycaw.pycaw import AudioUtilities
        except ImportError:
            return None, 'pycaw not installed (pip install pycaw)'
        proc = (process or '').strip().lower()
        if not proc:
            return None, 'No process configured'
        if not proc.endswith('.exe'):
            proc += '.exe'
        vol = None
        try:
            for session in AudioUtilities.GetAllSessions():
                name = ''
                try:
                    if session.Process:
                        name = session.Process.name().lower()
                except Exception:
                    name = ''
                if name == proc:
                    vol = session.SimpleAudioVolume
                    break
            if vol is None:
                return None, f'No audio session for {proc}'
            if set_value is None:
                return round(vol.GetMasterVolume() * 100), None
            vol.SetMasterVolume(set_value, None)
            return True, None
        except Exception as e:
            return None, str(e)
        finally:
            _release_com(vol)

    while True:
        job = work_q.get()
        if job is None:
            break
        fn, done, box = job
        try:
            box['result'] = fn({
                'endpoint': get_endpoint,
                'endpoint_op': endpoint_op,
                'invalidate': invalidate,
                'app_volume': app_volume,
            })
        except Exception as e:
            box['error'] = e
        done.set()
        # Reclaim any wrappers that slipped into cycles (pycaw internals,
        # frames captured by tracebacks) while still on the COM thread —
        # cheaper to sweep here than to wait for a foreign-thread collect.
        _gc.collect(0)
    comtypes.CoUninitialize()


def _run_on_audio_thread(fn, timeout=5):
    """Run fn(ctx) on the COM worker; returns fn's result."""
    global _audio_worker_thread, _audio_worker_queue
    with _audio_worker_lock:
        if _audio_worker_thread is None or not _audio_worker_thread.is_alive():
            _audio_worker_queue = queue.Queue()
            _audio_worker_thread = threading.Thread(
                target=_audio_worker_loop, args=(_audio_worker_queue,),
                name='vdock-audio', daemon=True)
            _audio_worker_thread.start()
    done = threading.Event()
    box = {}
    _audio_worker_queue.put((fn, done, box))
    if not done.wait(timeout):
        raise TimeoutError('Audio worker did not respond')
    if 'error' in box:
        raise box['error']
    return box.get('result')


def read_output_volume():
    """Current default-output level and mute state for the host OS.

    Returns (percent|None, muted|None, err|None). Shared by volume_get and
    the system-volume monitor so the deck tracks changes made elsewhere —
    the Windows read rides the COM worker, which resolves the *current*
    default endpoint per call (device switches are followed, not cached).
    """
    if _SYSTEM == 'Windows':
        def job(ctx):
            # endpoint_op retries once on a fresh endpoint when the cached
            # one faulted — e.g. the device vanished mid-flight.
            return ctx['endpoint_op'](lambda ep: (
                int(round(ep.GetMasterVolumeLevelScalar() * 100)),
                bool(ep.GetMute()),
                None,
            ))
        try:
            inner, err = _run_on_audio_thread(job)
        except Exception as e:
            return (None, None, f'Volume read failed: {e}')
        if inner is None:
            return (None, None, err or 'Volume read unavailable on Windows')
        return inner
    if _SYSTEM == 'Darwin':
        result = subprocess.run(
            'osascript -e "get volume settings"',
            shell=True, capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return (None, None, 'Could not read volume (osascript)')
        # e.g. "output volume:56, input volume:50, alert volume:100, output muted:false"
        vol = re.search(r'output volume:(\d+)', result.stdout)
        muted = re.search(r'output muted:(true|false)', result.stdout)
        if not vol:
            return (None, None, 'Could not read volume (osascript)')
        return (
            int(vol.group(1)),
            (muted.group(1) == 'true') if muted else None,
            None,
        )
    if _SYSTEM == 'Linux':
        result = subprocess.run(
            'amixer get Master',
            shell=True, capture_output=True, text=True, timeout=5
        )
        # e.g. "Mono: Playback 49152 [75%] [-20.00dB] [on]"
        match = re.search(r'\[(\d+)%\][^\[]*\[(on|off)\]', result.stdout)
        if result.returncode == 0 and match:
            return (int(match.group(1)), match.group(2) == 'off', None)
        return (None, None, 'Could not read volume (amixer)')
    return (None, None, f'Volume control not supported on {_SYSTEM}')


class CrossPlatformAction(BaseAction):
    """Cross-platform system actions with OS-specific implementations."""

    VALID_ACTIONS = [
        # System control
        'shutdown', 'restart', 'sleep', 'lock_screen',
        # Volume control
        'volume_up', 'volume_down', 'volume_mute', 'volume_unmute',
        'volume_set', 'volume_get', 'app_volume_set', 'app_volume_get',
        # Microphone control
        'microphone_mute', 'microphone_unmute',
        # Brightness control
        'brightness_up', 'brightness_down', 'brightness_set',
        # Media control
        'media_play_pause', 'media_next', 'media_previous', 'media_stop',
        'media_play_stop',
        # Web & Apps
        'open_url', 'open_app', 'open_folder', 'open_file', 'screenshot',
        'run_command', 'close_app', 'empty_recycle_bin',
    ]

    def __init__(self, config: Dict[str, Any]):
        """Initialize cross-platform action."""
        super().__init__(config)

    def validate(self) -> bool:
        """Validate that action type is provided and valid."""
        action = self.config.get('action')
        return action in self.VALID_ACTIONS

    def execute(self) -> ActionResult:
        """Execute the cross-platform action."""
        if not self.validate():
            return ActionResult(
                False,
                'Invalid configuration: Valid action required'
            )

        action = self.config['action']

        try:
            if action == 'shutdown':
                return self._shutdown()
            elif action == 'restart':
                return self._restart()
            elif action == 'sleep':
                return self._sleep()
            elif action == 'lock_screen':
                return self._lock_screen()
            elif action == 'volume_up':
                return self._volume_up()
            elif action == 'volume_down':
                return self._volume_down()
            elif action == 'volume_mute':
                return self._volume_mute()
            elif action == 'volume_unmute':
                return self._volume_unmute()
            elif action == 'volume_set':
                return self._volume_set()
            elif action == 'volume_get':
                return self._volume_get()
            elif action == 'app_volume_set':
                return self._app_volume_set()
            elif action == 'app_volume_get':
                return self._app_volume_get()
            elif action == 'brightness_up':
                return self._brightness_up()
            elif action == 'brightness_down':
                return self._brightness_down()
            elif action == 'brightness_set':
                return self._brightness_set()
            elif action == 'media_play_pause':
                return self._media_play_pause()
            elif action == 'media_next':
                return self._media_next()
            elif action == 'media_previous':
                return self._media_previous()
            elif action == 'media_stop':
                return self._media_stop()
            elif action == 'media_play_stop':
                return self._media_play_stop()
            elif action == 'open_url':
                return self._open_url()
            elif action == 'open_app':
                return self._open_app()
            elif action == 'open_folder':
                return self._open_folder()
            elif action == 'open_file':
                return self._open_file()
            elif action == 'screenshot':
                return self._screenshot()
            elif action == 'microphone_mute':
                return self._microphone_mute()
            elif action == 'microphone_unmute':
                return self._microphone_unmute()
            elif action == 'run_command':
                return self._run_custom_command()
            elif action == 'close_app':
                return self._close_app()
            elif action == 'empty_recycle_bin':
                return self._empty_recycle_bin()
            else:
                return ActionResult(False, f'Unknown action: {action}')
        except Exception as e:
            return ActionResult(False, f'Error executing {action}: {str(e)}')

    def _run_command(self, command: str, shell: bool = True) -> ActionResult:
        """Run a system command safely."""
        from utils.subprocess_runner import child_env
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30,
                env=child_env()
            )
            if result.returncode == 0:
                return ActionResult(True, f'Command executed successfully')
            else:
                return ActionResult(
                    False,
                    f'Command failed: {result.stderr or result.stdout}'
                )
        except subprocess.TimeoutExpired:
            return ActionResult(False, 'Command timed out')
        except Exception as e:
            return ActionResult(False, f'Command error: {str(e)}')

    def _check_nircmd(self) -> bool:
        """Check if NirCmd is available on Windows."""
        if _SYSTEM != 'Windows':
            return False
        try:
            result = subprocess.run(
                'nircmd.exe',
                capture_output=True,
                timeout=5
            )
            return result.returncode != 9009  # Command not found error
        except:
            return False
    
    def _send_windows_key(self, vk_code: int) -> ActionResult:
        """Send a Windows virtual key code using ctypes."""
        if not WINDOWS_API_AVAILABLE:
            return ActionResult(False, 'Windows API not available')
        
        try:
            # Press key
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
            # Release key
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
            return ActionResult(True, 'Key sent successfully')
        except Exception as e:
            return ActionResult(False, f'Failed to send key: {str(e)}')

    # System Control Actions
    def _shutdown(self) -> ActionResult:
        """Shutdown the computer."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe exitwin poweroff')
            else:
                return self._run_command('shutdown /s /t 0')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command('sudo shutdown -h now')
        elif _SYSTEM == 'Linux':
            return self._run_command('sudo shutdown now')
        else:
            return ActionResult(False, f'Shutdown not supported on {_SYSTEM}')

    def _restart(self) -> ActionResult:
        """Restart the computer."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe exitwin reboot')
            else:
                return self._run_command('shutdown /r /t 0')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command('sudo shutdown -r now')
        elif _SYSTEM == 'Linux':
            return self._run_command('sudo shutdown -r now')
        else:
            return ActionResult(False, f'Restart not supported on {_SYSTEM}')

    def _sleep(self) -> ActionResult:
        """Put the computer to sleep."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe standby')
            else:
                return self._run_command('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command('pmset sleepnow')
        elif _SYSTEM == 'Linux':
            return self._run_command('sudo systemctl suspend')
        else:
            return ActionResult(False, f'Sleep not supported on {_SYSTEM}')

    def _lock_screen(self) -> ActionResult:
        """Lock the screen."""
        if _SYSTEM == 'Windows':
            return self._run_command('rundll32.exe user32.dll,LockWorkStation')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command('/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend')
        elif _SYSTEM == 'Linux':
            # Try xdg-screensaver first
            result = self._run_command('xdg-screensaver lock')
            if result.success:
                return result
            # Fallback to dbus
            return self._run_command('dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock')
        else:
            return ActionResult(False, f'Lock screen not supported on {_SYSTEM}')

    # Volume Control Actions
    def _volume_up(self) -> ActionResult:
        """Increase system volume."""
        step = self.config.get('step', 2000)  # Default step for NirCmd
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command(f'nircmd.exe changesysvolume {step}')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_VOLUME_UP)
        elif _SYSTEM == 'Darwin':  # macOS
            volume_step = self.config.get('step', 10)
            script = f'set volume output volume (output volume of (get volume settings) + {volume_step})'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            volume_step = self.config.get('step', 10)
            return self._run_command(f'amixer set Master {volume_step}%+')
        else:
            return ActionResult(False, f'Volume control not supported on {_SYSTEM}')

    def _volume_down(self) -> ActionResult:
        """Decrease system volume."""
        step = self.config.get('step', 2000)  # Default step for NirCmd
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command(f'nircmd.exe changesysvolume -{step}')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_VOLUME_DOWN)
        elif _SYSTEM == 'Darwin':  # macOS
            volume_step = self.config.get('step', 10)
            script = f'set volume output volume (output volume of (get volume settings) - {volume_step})'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            volume_step = self.config.get('step', 10)
            return self._run_command(f'amixer set Master {volume_step}%-')
        else:
            return ActionResult(False, f'Volume control not supported on {_SYSTEM}')

    def _volume_mute(self) -> ActionResult:
        """Toggle mute."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe mutesysvolume 2')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_VOLUME_MUTE)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'set volume with output muted'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            return self._run_command('amixer set Master mute')
        else:
            return ActionResult(False, f'Volume control not supported on {_SYSTEM}')

    def _volume_unmute(self) -> ActionResult:
        """Unmute."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe mutesysvolume 0')
            else:
                # Use Windows API via ctypes (mute is toggle)
                return self._send_windows_key(VK_VOLUME_MUTE)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'set volume without output muted'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            return self._run_command('amixer set Master unmute')
        else:
            return ActionResult(False, f'Volume control not supported on {_SYSTEM}')

    def _volume_scalar(self, set_value=None):
        """Read (set_value=None) or write (0.0-1.0) the master volume scalar.

        Runs on the dedicated COM apartment thread via _run_on_audio_thread —
        Core Audio objects must never be created or released on Flask workers.
        Returns (level_percent | True, None) or (None, error).
        """
        def job(ctx):
            def use(endpoint):
                if set_value is None:
                    return round(endpoint.GetMasterVolumeLevelScalar() * 100)
                endpoint.SetMasterVolumeLevelScalar(set_value, None)
                return True
            return ctx['endpoint_op'](use)

        try:
            return _run_on_audio_thread(job)
        except Exception as e:
            return None, str(e)

    def _volume_set(self) -> ActionResult:
        """Set absolute output volume 0-100 — the slider action."""
        try:
            value = max(0, min(100, int(float(self.config.get('value', 50)))))
        except (TypeError, ValueError):
            return ActionResult(False, 'Invalid volume value (0-100 expected)')

        if _SYSTEM == 'Windows':
            result, err = self._volume_scalar(value / 100.0)
            if result is not None:
                return ActionResult(
                    True, f'Volume set to {value}%',
                    {'value': value, 'badge': f'{value}%'}
                )
            if self._check_nircmd():
                # NirCmd takes 0-65535.
                result = self._run_command(
                    f'nircmd.exe setsysvolume {int(value / 100 * 65535)}'
                )
                if result.success:
                    result.data = {**(result.data or {}), 'value': value, 'badge': f'{value}%'}
                return result
            return ActionResult(False, err or 'Volume set unavailable on Windows')
        elif _SYSTEM == 'Darwin':
            result = self._run_command(f'osascript -e "set volume output volume {value}"')
            if result.success:
                result.data = {**(result.data or {}), 'value': value, 'badge': f'{value}%'}
            return result
        elif _SYSTEM == 'Linux':
            result = self._run_command(f'amixer set Master {value}%')
            if result.success:
                result.data = {**(result.data or {}), 'value': value, 'badge': f'{value}%'}
            return result
        return ActionResult(False, f'Volume control not supported on {_SYSTEM}')

    def _volume_get(self) -> ActionResult:
        """Current output volume 0-100 — sliders fetch this on mount."""
        value, _muted, err = read_output_volume()
        if value is None:
            return ActionResult(False, err or 'Could not read volume')
        return ActionResult(True, f'Volume {value}%', {'value': value})

    def _app_volume_process(self):
        return str(self.config.get('process') or self.config.get('app') or '').strip()

    def _app_volume_set(self) -> ActionResult:
        """Set one app's session volume 0-100 — the app_volume slider."""
        if _SYSTEM != 'Windows':
            return ActionResult(False, 'Per-app volume is Windows-only')
        process = self._app_volume_process()
        if not process:
            return ActionResult(False, 'No process configured')
        try:
            value = max(0, min(100, int(float(self.config.get('value', 50)))))
        except (TypeError, ValueError):
            return ActionResult(False, 'Invalid volume value (0-100 expected)')
        result, err = _run_on_audio_thread(
            lambda ctx: ctx['app_volume'](process, value / 100.0))
        if result is not None:
            return ActionResult(
                True, f'{process} volume set to {value}%',
                {'value': value, 'badge': f'{value}%'})
        return ActionResult(False, err or f'Could not set {process} volume')

    def _app_volume_get(self) -> ActionResult:
        """Current session volume 0-100 for the configured process."""
        if _SYSTEM != 'Windows':
            return ActionResult(False, 'Per-app volume is Windows-only')
        process = self._app_volume_process()
        if not process:
            return ActionResult(False, 'No process configured')
        value, err = _run_on_audio_thread(
            lambda ctx: ctx['app_volume'](process))
        if value is not None:
            return ActionResult(True, f'{process} volume {value}%', {'value': value})
        return ActionResult(False, err or f'Could not read {process} volume')

    # Brightness Control Actions
    def _brightness_up(self) -> ActionResult:
        """Increase screen brightness."""
        step = self.config.get('step', 10)
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                # Get current brightness and increase
                try:
                    result = subprocess.run(
                        'nircmd.exe getbrightness',
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        current = int(result.stdout.strip())
                        new_brightness = min(100, current + step)
                        return self._run_command(f'nircmd.exe setbrightness {new_brightness}')
                except:
                    pass
            
            # Try multiple Windows brightness control methods
            methods = [
                # Method 1: WMI with error handling
                f'powershell -Command "try {{ (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100) }} catch {{ Write-Host \\"WMI not supported\\" }}"',
                # Method 2: Windows 10+ brightness control
                f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\\"{{F15}}\\")"',
                # Method 3: Fallback hotkey
                'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\\"%{{F15}}\\")"'
            ]
            
            for method in methods:
                try:
                    result = self._run_command(method)
                    if result.success:
                        return ActionResult(True, 'Brightness increased')
                except:
                    continue
            
            return ActionResult(False, 'Brightness control not available on this system')
        elif _SYSTEM == 'Darwin':  # macOS
            # Check if brightness tool is available
            try:
                result = subprocess.run(
                    'brightness',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('brightness 1')  # Set to max
            except:
                pass
            return ActionResult(False, 'Brightness control requires brightness tool on macOS. Install with: brew install brightness')
        elif _SYSTEM == 'Linux':
            # Try to get current brightness and increase
            try:
                result = subprocess.run(
                    'xrandr --verbose | grep -i brightness',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Extract current brightness and increase
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'brightness:' in line.lower():
                            current = float(line.split(':')[1].strip())
                            new_brightness = min(1.0, current + 0.1)
                            # Get display name
                            display_result = subprocess.run(
                                'xrandr | grep " connected" | head -1 | cut -d" " -f1',
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if display_result.returncode == 0:
                                display = display_result.stdout.strip()
                                return self._run_command(f'xrandr --output {display} --brightness {new_brightness}')
            except:
                pass
            return ActionResult(False, 'Brightness control not available on Linux')
        else:
            return ActionResult(False, f'Brightness control not supported on {_SYSTEM}')

    def _brightness_down(self) -> ActionResult:
        """Decrease screen brightness."""
        step = self.config.get('step', 10)
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                # Get current brightness and decrease
                try:
                    result = subprocess.run(
                        'nircmd.exe getbrightness',
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        current = int(result.stdout.strip())
                        new_brightness = max(0, current - step)
                        return self._run_command(f'nircmd.exe setbrightness {new_brightness}')
                except:
                    pass
            
            # Try multiple Windows brightness control methods
            methods = [
                # Method 1: WMI with error handling
                f'powershell -Command "try {{ (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,50) }} catch {{ Write-Host \\"WMI not supported\\" }}"',
                # Method 2: Windows 10+ brightness control
                f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\\"{{F14}}\\")"',
                # Method 3: Fallback hotkey
                'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\\"%{{F14}}\\")"'
            ]
            
            for method in methods:
                try:
                    result = self._run_command(method)
                    if result.success:
                        return ActionResult(True, 'Brightness decreased')
                except:
                    continue
            
            return ActionResult(False, 'Brightness control not available on this system')
        elif _SYSTEM == 'Darwin':  # macOS
            # Check if brightness tool is available
            try:
                result = subprocess.run(
                    'brightness',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('brightness 0.5')  # Set to 50%
            except:
                pass
            return ActionResult(False, 'Brightness control requires brightness tool on macOS')
        elif _SYSTEM == 'Linux':
            # Try to get current brightness and decrease
            try:
                result = subprocess.run(
                    'xrandr --verbose | grep -i brightness',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Extract current brightness and decrease
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'brightness:' in line.lower():
                            current = float(line.split(':')[1].strip())
                            new_brightness = max(0.1, current - 0.1)
                            # Get display name
                            display_result = subprocess.run(
                                'xrandr | grep " connected" | head -1 | cut -d" " -f1',
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if display_result.returncode == 0:
                                display = display_result.stdout.strip()
                                return self._run_command(f'xrandr --output {display} --brightness {new_brightness}')
            except:
                pass
            return ActionResult(False, 'Brightness control not available on Linux')
        else:
            return ActionResult(False, f'Brightness control not supported on {_SYSTEM}')

    def _brightness_set(self) -> ActionResult:
        """Set screen brightness to specific value."""
        brightness = self.config.get('brightness', 50)
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command(f'nircmd.exe setbrightness {brightness}')
            else:
                # Fallback to WMI using PowerShell
                ps_script = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness})"
                return self._run_command(f'powershell -Command "{ps_script}"')
        elif _SYSTEM == 'Darwin':  # macOS
            try:
                result = subprocess.run(
                    'brightness',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    brightness_normalized = brightness / 100.0
                    return self._run_command(f'brightness {brightness_normalized}')
            except:
                pass
            return ActionResult(False, 'Brightness control requires brightness tool on macOS')
        elif _SYSTEM == 'Linux':
            try:
                # Get display name
                display_result = subprocess.run(
                    'xrandr | grep " connected" | head -1 | cut -d" " -f1',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if display_result.returncode == 0:
                    display = display_result.stdout.strip()
                    brightness_normalized = brightness / 100.0
                    return self._run_command(f'xrandr --output {display} --brightness {brightness_normalized}')
            except:
                pass
            return ActionResult(False, 'Brightness control not available on Linux')
        else:
            return ActionResult(False, f'Brightness control not supported on {_SYSTEM}')

    # Media Control Actions
    def _media_play_pause(self) -> ActionResult:
        """Toggle play/pause."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe sendkeypress media_play_pause')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_MEDIA_PLAY_PAUSE)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'tell application "Music" to playpause'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            # Check if playerctl is available
            try:
                result = subprocess.run(
                    'playerctl',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('playerctl play-pause')
            except:
                pass
            # Fallback to PowerShell SendKeys
            ps_script = "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{MEDIA_PLAY_PAUSE}')"
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ActionResult(True, 'Media play/pause toggled')
            return ActionResult(False, 'Media control not available')
        else:
            return ActionResult(False, f'Media control not supported on {_SYSTEM}')

    def _media_next(self) -> ActionResult:
        """Skip to next track."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe sendkeypress media_next_track')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_MEDIA_NEXT_TRACK)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'tell application "Music" to next track'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            # Check if playerctl is available
            try:
                result = subprocess.run(
                    'playerctl',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('playerctl next')
            except:
                pass
            # Fallback to PowerShell SendKeys
            ps_script = "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{MEDIA_NEXT_TRACK}')"
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ActionResult(True, 'Media next track')
            return ActionResult(False, 'Media control not available')
        else:
            return ActionResult(False, f'Media control not supported on {_SYSTEM}')

    def _media_previous(self) -> ActionResult:
        """Skip to previous track."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe sendkeypress media_prev_track')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_MEDIA_PREV_TRACK)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'tell application "Music" to previous track'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            # Check if playerctl is available
            try:
                result = subprocess.run(
                    'playerctl',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('playerctl previous')
            except:
                pass
            # Fallback to PowerShell SendKeys
            ps_script = "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{MEDIA_PREV_TRACK}')"
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ActionResult(True, 'Media previous track')
            return ActionResult(False, 'Media control not available')
        else:
            return ActionResult(False, f'Media control not supported on {_SYSTEM}')

    def _media_play_stop(self) -> ActionResult:
        """DL-128: state-split transport — Stop while media plays, Play
        otherwise. Decides from the now-playing service's last SMTC
        snapshot so the choice matches what the deck face shows; absent
        or unreadable state resolves to play/pause."""
        playing = False
        try:
            from services import now_playing
            snap = now_playing.snapshot() or {}
            playing = snap.get('playing') is True
        except Exception:
            pass
        if playing:
            return self._media_stop()
        return self._media_play_pause()

    def _media_stop(self) -> ActionResult:
        """Stop playback."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe sendkeypress media_stop')
            else:
                # Use Windows API via ctypes
                return self._send_windows_key(VK_MEDIA_STOP)
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'tell application "Music" to stop'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            # Check if playerctl is available
            try:
                result = subprocess.run(
                    'playerctl',
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 127:  # Command exists
                    return self._run_command('playerctl stop')
            except:
                pass
            # Fallback to PowerShell SendKeys
            ps_script = "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{MEDIA_STOP}')"
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return ActionResult(True, 'Media stopped')
            return ActionResult(False, 'Media control not available')
        else:
            return ActionResult(False, f'Media control not supported on {_SYSTEM}')

    # Web & Apps Actions
    def _open_url(self) -> ActionResult:
        """Open URL in default browser."""
        url = self.config.get('url')
        if not url:
            return ActionResult(False, 'URL not specified')
        
        # Validate URL
        if not url.startswith(('http://', 'https://', 'ftp://')):
            url = 'https://' + url
        
        if _SYSTEM == 'Windows':
            return self._run_command(f'start "" "{url}"')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command(f'open "{url}"')
        elif _SYSTEM == 'Linux':
            return self._run_command(f'xdg-open "{url}"')
        else:
            return ActionResult(False, f'URL opening not supported on {_SYSTEM}')

    def _open_app(self) -> ActionResult:
        """Open application."""
        app_path = self.config.get('path') or self.config.get('name')
        if not app_path:
            return ActionResult(False, 'Application path/name not specified')

        # DL-084: a configured app_paths override wins over OS name
        # resolution — the template ships a NAME ("cursor"), the user points
        # it at the real binary/bundle once.
        from services import app_paths as app_paths_svc
        override = app_paths_svc.override_for(str(app_path))
        if override and _SYSTEM == 'Darwin':
            # `open` handles .app bundles and bare executables by path;
            # `open -a` only takes installed app *names*.
            return self._run_command(f'open "{override}"')
        target = override or app_path

        if _SYSTEM == 'Windows':
            return self._run_command(f'start "" "{target}"')
        elif _SYSTEM == 'Darwin':  # macOS
            app_name = os.path.basename(target)
            return self._run_command(f'open -a "{app_name}"')
        elif _SYSTEM == 'Linux':
            # Try xdg-open first
            result = self._run_command(f'xdg-open "{target}"')
            if result.success:
                return result
            # Fallback to direct execution
            return self._run_command(f'"{target}"')
        else:
            return ActionResult(False, f'Application opening not supported on {_SYSTEM}')

    def _open_folder(self) -> ActionResult:
        """Open folder in file manager."""
        folder_path = self.config.get('path')
        if not folder_path:
            return ActionResult(False, 'Folder path not specified')
        
        if not os.path.exists(folder_path):
            return ActionResult(False, f'Folder does not exist: {folder_path}')
        
        if _SYSTEM == 'Windows':
            return self._run_command(f'explorer.exe "{folder_path}"')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command(f'open "{folder_path}"')
        elif _SYSTEM == 'Linux':
            return self._run_command(f'xdg-open "{folder_path}"')
        else:
            return ActionResult(False, f'Folder opening not supported on {_SYSTEM}')

    def _open_file(self) -> ActionResult:
        """Open file with default application."""
        file_path = self.config.get('path')
        if not file_path:
            return ActionResult(False, 'File path not specified')
        
        if not os.path.exists(file_path):
            return ActionResult(False, f'File does not exist: {file_path}')
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command(f'nircmd.exe shexec open "{file_path}"')
            else:
                return self._run_command(f'start "" "{file_path}"')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command(f'open "{file_path}"')
        elif _SYSTEM == 'Linux':
            return self._run_command(f'xdg-open "{file_path}"')
        else:
            return ActionResult(False, f'File opening not supported on {_SYSTEM}')

    def _screenshot(self) -> ActionResult:
        """Take a screenshot."""
        output_path = self.config.get('path', 'screenshot.png')
        
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command(f'nircmd.exe savescreenshot "{output_path}"')
            else:
                # Fallback to PowerShell with proper string escaping
                ps_script = f"Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; $Screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $bitmap = New-Object System.Drawing.Bitmap $Screen.Width, $Screen.Height; $graphics = [System.Drawing.Graphics]::FromImage($bitmap); $graphics.CopyFromScreen($Screen.Left, $Screen.Top, 0, 0, $Screen.Size); $bitmap.Save('{output_path}'); $graphics.Dispose(); $bitmap.Dispose()"
                return self._run_command(f'powershell -Command "{ps_script}"')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command(f'screencapture -x "{output_path}"')
        elif _SYSTEM == 'Linux':
            # Try gnome-screenshot first
            result = self._run_command(f'gnome-screenshot -f "{output_path}"')
            if result.success:
                return result
            # Fallback to ImageMagick
            result = self._run_command(f'import -window root "{output_path}"')
            if result.success:
                return result
            return ActionResult(False, 'Screenshot requires gnome-screenshot or ImageMagick on Linux')
        else:
            return ActionResult(False, f'Screenshot not supported on {_SYSTEM}')


    # Microphone Control Actions
    def _microphone_mute(self) -> ActionResult:
        """Mute microphone."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe mutesysvolume 1 microphone')
            else:
                # PowerShell method to mute microphone
                ps_script = "$devices = Get-WmiObject -Class Win32_SoundDevice; foreach ($device in $devices) { if ($device.Name -like '*Microphone*') { $device.Disable() } }"
                return self._run_command(f'powershell -Command "{ps_script}"')
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'set volume input volume 0'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            return self._run_command('amixer set Capture nocap')
        else:
            return ActionResult(False, f'Microphone control not supported on {_SYSTEM}')

    def _microphone_unmute(self) -> ActionResult:
        """Unmute microphone."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe mutesysvolume 0 microphone')
            else:
                # PowerShell method to unmute microphone
                ps_script = "$devices = Get-WmiObject -Class Win32_SoundDevice; foreach ($device in $devices) { if ($device.Name -like '*Microphone*') { $device.Enable() } }"
                return self._run_command(f'powershell -Command "{ps_script}"')
        elif _SYSTEM == 'Darwin':  # macOS
            script = 'set volume input volume 50'
            return self._run_command(f'osascript -e "{script}"')
        elif _SYSTEM == 'Linux':
            return self._run_command('amixer set Capture cap')
        else:
            return ActionResult(False, f'Microphone control not supported on {_SYSTEM}')

    # Additional Actions
    def _run_custom_command(self) -> ActionResult:
        """Run a custom command."""
        command = self.config.get('command')
        if not command:
            return ActionResult(False, 'Command not specified')
        
        return self._run_command(command)

    def _close_app(self) -> ActionResult:
        """Close an application by name."""
        app_name = self.config.get('app_name')
        if not app_name:
            return ActionResult(False, 'Application name not specified')
        
        if _SYSTEM == 'Windows':
            # Remove .exe extension if present for taskkill
            if app_name.endswith('.exe'):
                app_name_clean = app_name
            else:
                app_name_clean = app_name + '.exe'
            return self._run_command(f'taskkill /F /IM "{app_name_clean}"')
        elif _SYSTEM == 'Darwin':  # macOS
            # Remove .app extension if present
            app_name_clean = app_name.replace('.app', '')
            return self._run_command(f'pkill -x "{app_name_clean}"')
        elif _SYSTEM == 'Linux':
            return self._run_command(f'pkill "{app_name}"')
        else:
            return ActionResult(False, f'Close app not supported on {_SYSTEM}')

    def _empty_recycle_bin(self) -> ActionResult:
        """Empty the recycle bin."""
        if _SYSTEM == 'Windows':
            if self._check_nircmd():
                return self._run_command('nircmd.exe emptybin')
            else:
                # PowerShell method
                ps_script = "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"
                return self._run_command(f'powershell -Command "{ps_script}"')
        elif _SYSTEM == 'Darwin':  # macOS
            return self._run_command('rm -rf ~/.Trash/*')
        elif _SYSTEM == 'Linux':
            # Try multiple trash locations
            commands = [
                'rm -rf ~/.local/share/Trash/*',
                'rm -rf ~/.Trash/*'
            ]
            for cmd in commands:
                result = self._run_command(cmd)
                if result.success:
                    return result
            return ActionResult(False, 'Could not empty trash')
        else:
            return ActionResult(False, f'Empty recycle bin not supported on {_SYSTEM}')

    def get_description(self) -> str:
        """Get action description."""
        action = self.config.get('action', 'unknown')
        return f"Cross-platform: {action.replace('_', ' ').title()}"
