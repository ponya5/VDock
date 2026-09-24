"""focus_hwnd escalation: a refused AttachThreadInput must not skip the
fallbacks (DL-065 live test — the Claude desktop app in the foreground)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason='Win32 focus APIs')

from utils import window_focus  # noqa: E402

TARGET_WINDOW = 1001
FOREGROUND_WINDOW = 2002


@pytest.fixture
def win32_stubs(mocker):
    import win32gui
    import win32process

    foreground = {'window': FOREGROUND_WINDOW}
    mocker.patch.object(win32gui, 'IsIconic', return_value=False)
    mocker.patch.object(win32gui, 'GetForegroundWindow', side_effect=lambda: foreground['window'])
    mocker.patch.object(win32gui, 'BringWindowToTop')
    mocker.patch.object(win32gui, 'SetForegroundWindow')
    mocker.patch.object(win32process, 'GetWindowThreadProcessId', return_value=(77, 88))
    mocker.patch.object(
        win32process, 'AttachThreadInput', side_effect=OSError(5, 'AttachThreadInput', 'Access is denied.'),
    )
    mocker.patch.object(window_focus.time, 'sleep')
    mocker.patch.object(window_focus, '_minimise_and_restore')
    return foreground


def test_refused_attach_still_escalates_to_the_alt_tap(win32_stubs, mocker):
    def alt_tap_unlocks_the_foreground():
        win32_stubs['window'] = TARGET_WINDOW

    alt_tap = mocker.patch.object(window_focus, '_tap_alt_key', side_effect=alt_tap_unlocks_the_foreground)

    assert window_focus.focus_hwnd(TARGET_WINDOW) is True
    alt_tap.assert_called_once()


def test_refused_attach_reaches_the_last_resort(win32_stubs, mocker):
    mocker.patch.object(window_focus, '_tap_alt_key')

    assert window_focus.focus_hwnd(TARGET_WINDOW) is False
    window_focus._minimise_and_restore.assert_called_once_with(TARGET_WINDOW)
