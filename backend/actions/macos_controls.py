"""macOS system controls (volume, media, lock, power, microphone).

Every call goes through ``osascript`` with an argv list - never a shell string.
The old implementation nested double quotes inside ``osascript -e "..."`` which
the shell silently stripped (``tell application Music ...`` -> AppleScript
error -2740/-2753), so quoting must stay out of the shell's reach.
"""
import ctypes
import re
import subprocess
from typing import List, Optional, Tuple

from .base_action import ActionResult
from .volume_steps import MAX_VOLUME_PERCENT, parse_volume_step  # noqa: F401

OSASCRIPT_TIMEOUT_SECONDS = 10
DEFAULT_UNMUTED_INPUT_VOLUME = 50

# Order matters only as a tie-breaker when several players are running and
# none of them is currently playing.
SCRIPTABLE_PLAYERS = ('Spotify', 'Music')

NX_KEYTYPE_PLAY = 16
NX_KEYTYPE_NEXT = 17
NX_KEYTYPE_PREVIOUS = 18

# command -> (AppleScript verb understood by Spotify and Music, system media key)
MEDIA_COMMANDS = {
    'play_pause': ('playpause', NX_KEYTYPE_PLAY),
    'next': ('next track', NX_KEYTYPE_NEXT),
    'previous': ('previous track', NX_KEYTYPE_PREVIOUS),
    # macOS has no system "Stop" key, so stop only works on a scriptable player.
    'stop': ('pause', None),
}

LOGIN_FRAMEWORK_PATH = (
    '/System/Library/PrivateFrameworks/login.framework/Versions/Current/login'
)

AUTOMATION_DENIED_ERROR_CODE = '-1743'

SCREEN_RECORDING_DENIED_FRAGMENT = 'could not create image from display'

APPLICATION_SERVICES_PATH = (
    '/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices'
)

ACCESSIBILITY_HELP = (
    'macOS is blocking VDock from pressing keys. Allow it under System Settings > '
    'Privacy & Security > Accessibility (add the app that starts VDock - '
    'VDock, Terminal or your editor), then relaunch VDock. Settings > Agent '
    'alerts has a button that opens the right page.'
)

# Synthetic system key events are dropped by macOS unless the sending process
# holds the Accessibility permission; this is the fallback for players that
# AppleScript cannot reach (browsers, VLC, ...).
MEDIA_KEY_SCRIPT = """
ObjC.import('Cocoa');
function run(argv) {
  const keyType = parseInt(argv[0], 10);
  [0xa, 0xb].forEach(function (keyState) {
    const flags = keyState << 8;
    const event = $.NSEvent.otherEventWithTypeLocationModifierFlagsTimestampWindowNumberContextSubtypeData1Data2(
      14, { x: 0, y: 0 }, flags, 0, 0, null, 8, (keyType << 16) | flags, -1);
    $.CGEventPost(0, event.CGEvent);
  });
}
"""

VOLUME_SETTINGS_PATTERN = re.compile(r'(output|input) volume:(\d+)')
OUTPUT_MUTED_PATTERN = re.compile(r'output muted:(true|false)')

COREAUDIO_PATH = '/System/Library/Frameworks/CoreAudio.framework/CoreAudio'

_input_volume_before_mute: Optional[int] = None
# Spotify Connect "mute" = its volume 0; the level to restore on unmute.
_remote_volume_before_mute: Optional[int] = None


def _run_osascript(
    script: str,
    javascript: bool = False,
    arguments: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    command = ['osascript']
    if javascript:
        command += ['-l', 'JavaScript']
    command += ['-e', script] + list(arguments or [])
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=OSASCRIPT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False, 'osascript timed out'
    except OSError as error:
        return False, f'osascript unavailable: {error}'

    if completed.returncode != 0:
        return False, (completed.stderr or completed.stdout).strip()
    return True, completed.stdout.strip()


def is_accessibility_trusted() -> bool:
    """Whether macOS lets this process post keyboard events.

    Without the permission, synthetic key presses are dropped silently, so
    callers check first and report it instead of claiming success. If the check
    itself cannot run, assume trusted rather than block a working setup.
    """
    try:
        application_services = ctypes.cdll.LoadLibrary(APPLICATION_SERVICES_PATH)
        application_services.AXIsProcessTrusted.restype = ctypes.c_bool
        return bool(application_services.AXIsProcessTrusted())
    except (OSError, AttributeError):
        return True


ACCESSIBILITY_SETTINGS_URL = (
    'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
)


def request_accessibility() -> bool:
    """Ask macOS for the Accessibility grant and open its settings pane.

    The prompt option makes macOS add the app that started VDock to the
    Accessibility list (switched off) and show its own "would like to control
    this computer" dialog once, so the user only has to flip the switch. The
    pane is opened as well because macOS shows that dialog only the first
    time. Returns whether the process is trusted already.
    """
    trusted = False
    try:
        from ApplicationServices import (
            AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt,
        )
        trusted = bool(AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True}))
    except ImportError:
        trusted = is_accessibility_trusted()
    if not trusted:
        subprocess.run(['open', ACCESSIBILITY_SETTINGS_URL], capture_output=True, timeout=10)
    return trusted


def _read_volume_levels() -> Optional[dict]:
    """Return {'output': int, 'input': int}, or None if unreadable.

    Fixed-level outputs (HDMI, some DACs) report ``missing value`` for the
    output level; in that case only the input level is present.
    """
    succeeded, output = _run_osascript('get volume settings')
    if not succeeded:
        return None
    return {
        name: int(level)
        for name, level in VOLUME_SETTINGS_PATTERN.findall(output)
    }


def _fourcc(code: str) -> int:
    return int.from_bytes(code.encode('ascii'), 'big')


def _output_device_running() -> Optional[bool]:
    """Whether any process is playing through the default output device.

    Core Audio's "running somewhere" flag, no permission needed. None when it
    cannot be read.
    """
    class PropertyAddress(ctypes.Structure):
        _fields_ = [('selector', ctypes.c_uint32), ('scope', ctypes.c_uint32),
                    ('element', ctypes.c_uint32)]

    def read_uint32(object_id: int, selector: str) -> Optional[int]:
        address = PropertyAddress(_fourcc(selector), _fourcc('glob'), 0)
        value = ctypes.c_uint32(0)
        size = ctypes.c_uint32(ctypes.sizeof(value))
        status = core_audio.AudioObjectGetPropertyData(
            object_id, ctypes.byref(address), 0, None,
            ctypes.byref(size), ctypes.byref(value))
        return None if status else value.value

    try:
        core_audio = ctypes.cdll.LoadLibrary(COREAUDIO_PATH)
    except OSError:
        return None
    system_object = 1  # kAudioObjectSystemObject
    device = read_uint32(system_object, 'dOut')  # default output device
    if not device:
        return None
    running = read_uint32(device, 'gone')  # IsRunningSomewhere
    return None if running is None else bool(running)


def remote_spotify_volume() -> Optional[int]:
    """Spotify's volume when it plays on another device, else None.

    Spotify Connect (a TV, a speaker) plays elsewhere while the Mac app
    reports "playing" -- and the Mac's own output stays idle. The system
    volume then changes nothing the user hears; Spotify's volume controls
    the remote device (DL-007).
    """
    if not _is_app_running('Spotify') or not _is_player_playing('Spotify'):
        return None
    if _output_device_running() is not False:
        return None
    succeeded, output = _run_osascript('tell application "Spotify" to return sound volume')
    return int(output) if succeeded and output.isdigit() else None


def _set_spotify_volume(level: int, message: str) -> ActionResult:
    level = max(0, min(MAX_VOLUME_PERCENT, int(level)))
    succeeded, error = _run_osascript(
        'on run argv\n'
        '  tell application "Spotify" to set sound volume to (item 1 of argv as integer)\n'
        'end run', arguments=[str(level)])
    if not succeeded:
        return ActionResult(False, f'Spotify volume change failed: {error}')
    return ActionResult(True, message.format(level=level),
                        {'value': level, 'badge': f'{level}%'})


def change_output_volume(percent_delta: int) -> ActionResult:
    remote = remote_spotify_volume()
    if remote is not None:
        return _set_spotify_volume(remote + percent_delta,
                                   'Spotify (other device) volume {level}%')
    levels = _read_volume_levels()
    if levels is None or 'output' not in levels:
        return ActionResult(
            False,
            'This audio output has no adjustable volume '
            '(e.g. HDMI/DisplayPort). Use the device\'s own controls.',
        )

    new_volume = max(0, min(MAX_VOLUME_PERCENT, levels['output'] + percent_delta))
    succeeded, error = _run_osascript(f'set volume output volume {new_volume}')
    if not succeeded:
        return ActionResult(False, f'Volume change failed: {error}')
    return ActionResult(True, f'Volume {new_volume}%')


def set_output_volume(value: int) -> ActionResult:
    """Absolute volume 0-100 (the slider) -- Spotify's when it plays remotely."""
    value = max(0, min(MAX_VOLUME_PERCENT, int(value)))
    if remote_spotify_volume() is not None:
        return _set_spotify_volume(value, 'Spotify (other device) volume {level}%')
    succeeded, error = _run_osascript(f'set volume output volume {value}')
    if not succeeded:
        return ActionResult(False, f'Volume change failed: {error}')
    return ActionResult(True, f'Volume set to {value}%', {'value': value, 'badge': f'{value}%'})


def _remote_mute(muted: bool, remote_level: int) -> ActionResult:
    global _remote_volume_before_mute
    if muted:
        if remote_level:
            _remote_volume_before_mute = remote_level
        return _set_spotify_volume(0, 'Spotify (other device) muted')
    return _set_spotify_volume(_remote_volume_before_mute or DEFAULT_UNMUTED_INPUT_VOLUME,
                               'Spotify (other device) volume {level}%')


def toggle_output_muted() -> ActionResult:
    """Mute button: toggles, like Windows (``nircmd mutesysvolume 2``)."""
    remote = remote_spotify_volume()
    if remote is not None:
        return _remote_mute(remote > 0, remote)
    succeeded, output = _run_osascript('get volume settings')
    match = OUTPUT_MUTED_PATTERN.search(output) if succeeded else None
    return _set_system_muted(not (match and match.group(1) == 'true'))


def set_output_muted(muted: bool) -> ActionResult:
    remote = remote_spotify_volume()
    if remote is not None:
        return _remote_mute(muted, remote)
    return _set_system_muted(muted)


def _set_system_muted(muted: bool) -> ActionResult:
    keyword = 'with' if muted else 'without'
    succeeded, error = _run_osascript(f'set volume {keyword} output muted')
    if not succeeded:
        return ActionResult(False, f'Mute change failed: {error}')
    return ActionResult(True, 'Muted' if muted else 'Unmuted')


def set_microphone_muted(muted: bool) -> ActionResult:
    """macOS has no input mute switch, so mute = input level 0 (remembered)."""
    global _input_volume_before_mute

    levels = _read_volume_levels() or {}
    current_level = levels.get('input')

    if muted:
        if current_level:
            _input_volume_before_mute = current_level
        target_level = 0
    else:
        if current_level:
            return ActionResult(True, 'Microphone already unmuted')
        target_level = _input_volume_before_mute or DEFAULT_UNMUTED_INPUT_VOLUME

    succeeded, error = _run_osascript(f'set volume input volume {target_level}')
    if not succeeded:
        return ActionResult(False, f'Microphone change failed: {error}')
    return ActionResult(True, 'Microphone muted' if muted else 'Microphone unmuted')


def _is_app_running(app_name: str) -> bool:
    completed = subprocess.run(
        ['pgrep', '-x', app_name], capture_output=True, text=True
    )
    return completed.returncode == 0


def _is_player_playing(app_name: str) -> bool:
    succeeded, output = _run_osascript(
        f'tell application "{app_name}" to return player state as text'
    )
    return succeeded and output == 'playing'


def _pick_running_player() -> Optional[str]:
    """Prefer the player that is playing; never launch one that is closed."""
    running_players = [
        player for player in SCRIPTABLE_PLAYERS if _is_app_running(player)
    ]
    for player in running_players:
        if _is_player_playing(player):
            return player
    return running_players[0] if running_players else None


def _send_media_key(key_type: int) -> ActionResult:
    if not is_accessibility_trusted():
        return ActionResult(
            False,
            'No Spotify or Music is running, and the system media key needs '
            'Accessibility access. ' + ACCESSIBILITY_HELP,
        )
    succeeded, error = _run_osascript(
        MEDIA_KEY_SCRIPT, javascript=True, arguments=[str(key_type)]
    )
    if not succeeded:
        return ActionResult(False, f'Media key failed: {error}')
    return ActionResult(True, 'Sent the system media key')


def control_media(command: str) -> ActionResult:
    """command is one of MEDIA_COMMANDS: play_pause, next, previous, stop."""
    verb, media_key = MEDIA_COMMANDS[command]

    player = _pick_running_player()
    if player is not None:
        succeeded, error = _run_osascript(f'tell application "{player}" to {verb}')
        if succeeded:
            return ActionResult(True, f'{player}: {command.replace("_", " ")}')
        if AUTOMATION_DENIED_ERROR_CODE in error:
            return ActionResult(
                False,
                f'macOS blocked VDock from controlling {player}. Allow it under '
                'System Settings > Privacy & Security > Automation.',
            )
        return ActionResult(False, f'{player} did not respond: {error}')

    if media_key is None:
        return ActionResult(
            False, 'Nothing to stop - Spotify and Music are not running.'
        )
    return _send_media_key(media_key)


def lock_screen() -> ActionResult:
    try:
        login_framework = ctypes.CDLL(LOGIN_FRAMEWORK_PATH)
        login_framework.SACLockScreenImmediate()
        return ActionResult(True, 'Screen locked')
    except (OSError, AttributeError):
        completed = subprocess.run(
            ['pmset', 'displaysleepnow'], capture_output=True, text=True
        )
        if completed.returncode != 0:
            return ActionResult(False, f'Lock failed: {completed.stderr.strip()}')
        return ActionResult(True, 'Display put to sleep')


def power_via_system_events(command: str) -> ActionResult:
    """command is 'shut down' or 'restart'; needs no sudo, unlike shutdown(8)."""
    succeeded, error = _run_osascript(
        f'tell application "System Events" to {command}'
    )
    if not succeeded:
        return ActionResult(False, f'Could not {command}: {error}')
    return ActionResult(True, f'Mac is about to {command}')


def take_screenshot(output_path: str) -> ActionResult:
    try:
        completed = subprocess.run(
            ['screencapture', '-x', output_path],
            capture_output=True,
            text=True,
            timeout=OSASCRIPT_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError) as error:
        return ActionResult(False, f'Screenshot failed: {error}')

    if completed.returncode == 0:
        return ActionResult(True, f'Screenshot saved to {output_path}')

    error_text = (completed.stderr or completed.stdout).strip()
    if SCREEN_RECORDING_DENIED_FRAGMENT in error_text:
        return ActionResult(
            False,
            'macOS is blocking VDock from capturing the screen. Allow it under '
            'System Settings > Privacy & Security > Screen & System Audio '
            'Recording (add the app that starts VDock), then relaunch VDock.',
        )
    return ActionResult(False, f'Screenshot failed: {error_text}')
