"""DL-145 Phase 4: true microphone mute on the capture endpoint."""
import pytest

from actions import cross_platform_action as cpa
from actions.base_action import ActionResult
from integrations import system_live_pack as pack


class FakeEndpoint:
    def __init__(self, muted=False):
        self.muted = muted
        self.writes = []

    def GetMute(self):
        return int(self.muted)

    def SetMute(self, value, _ctx):
        self.writes.append(bool(value))
        self.muted = bool(value)


@pytest.fixture
def mic(mocker):
    """Route audio-thread jobs to a fake capture endpoint."""
    endpoint = FakeEndpoint()

    def run(job, timeout=5):
        return job({'mic_endpoint_op': lambda fn: (fn(endpoint), None)})

    mocker.patch.object(cpa, '_SYSTEM', 'Windows')
    mocker.patch.object(cpa, '_run_on_audio_thread', side_effect=run)
    return endpoint


def test_read_does_not_write(mic):
    mic.muted = True
    assert cpa.read_mic_mute() == (True, None)
    assert mic.writes == []


def test_toggle_flips_state(mic):
    assert cpa.set_mic_mute(None) == (True, None)
    assert cpa.set_mic_mute(None) == (False, None)
    assert mic.writes == [True, False]


def test_explicit_set_is_idempotent(mic):
    assert cpa.set_mic_mute(True) == (True, None)
    assert cpa.set_mic_mute(True) == (True, None)
    assert cpa.set_mic_mute(False) == (False, None)


def test_no_microphone_reports_plain_message(mocker):
    mocker.patch.object(cpa, '_SYSTEM', 'Windows')
    mocker.patch.object(
        cpa, '_run_on_audio_thread',
        side_effect=lambda job, timeout=5: job(
            {'mic_endpoint_op': lambda fn: (None, 'No microphone found')}))
    assert cpa.read_mic_mute() == (None, 'No microphone found')
    assert cpa.set_mic_mute(None) == (None, 'No microphone found')


def test_worker_timeout_becomes_error(mocker):
    mocker.patch.object(cpa, '_SYSTEM', 'Windows')
    mocker.patch.object(cpa, '_run_on_audio_thread',
                        side_effect=TimeoutError('Audio worker did not respond'))
    muted, err = cpa.read_mic_mute()
    assert muted is None and 'did not respond' in err


def test_not_windows_is_unsupported(mocker):
    mocker.patch.object(cpa, '_SYSTEM', 'Linux')
    muted, err = cpa.read_mic_mute()
    assert muted is None and 'Windows' in err


# --- endpoint cache: invalidate and retry once ------------------------------

def _ticking_clock(mocker):
    """Every read advances 10 s, so the flap guard never blocks a retry."""
    now = [100.0]

    def tick():
        now[0] += 10
        return now[0]

    mocker.patch.object(cpa.time, 'time', side_effect=tick)


def test_endpoint_op_invalidates_and_retries_once(mocker):
    _ticking_clock(mocker)
    release = mocker.patch.object(cpa, '_release_com')
    made = []

    def activate():
        ep = FakeEndpoint()
        made.append(ep)
        return ep

    cache = cpa._make_endpoint_cache(activate, lambda e: f'x: {e}')
    calls = []

    def use(ep):
        calls.append(ep)
        if len(calls) == 1:
            raise OSError('device gone')
        return 'ok'

    assert cache.op(use) == ('ok', None)
    assert len(made) == 2 and calls == made
    release.assert_called()


def test_endpoint_op_gives_up_after_second_failure(mocker):
    _ticking_clock(mocker)
    mocker.patch.object(cpa, '_release_com')
    cache = cpa._make_endpoint_cache(FakeEndpoint, lambda e: str(e))

    def use(_ep):
        raise OSError('still broken')

    assert cache.op(use) == (None, 'still broken')


def test_activate_failure_uses_caller_message(mocker):
    def activate():
        raise OSError('E_NOTFOUND')

    cache = cpa._make_endpoint_cache(activate, lambda e: 'No microphone found')
    assert cache.op(lambda ep: 1) == (None, 'No microphone found')


# --- legacy actions now use the same path ----------------------------------

def test_microphone_mute_action_sets_mute_without_disabling_device(mocker):
    mocker.patch.object(cpa, '_SYSTEM', 'Windows')
    setter = mocker.patch.object(cpa, 'set_mic_mute', return_value=(True, None))
    run = mocker.patch.object(cpa.CrossPlatformAction, '_run_command')
    result = cpa.CrossPlatformAction({'action': 'microphone_mute'}).execute()
    setter.assert_called_once_with(True)
    run.assert_not_called()
    assert result.success is True


def test_microphone_unmute_action_sets_unmute(mocker):
    mocker.patch.object(cpa, '_SYSTEM', 'Windows')
    setter = mocker.patch.object(cpa, 'set_mic_mute', return_value=(False, None))
    result = cpa.CrossPlatformAction({'action': 'microphone_unmute'}).execute()
    setter.assert_called_once_with(False)
    assert result.success is True


def test_microphone_mute_action_reports_failure(mocker):
    mocker.patch.object(cpa, '_SYSTEM', 'Windows')
    mocker.patch.object(cpa, 'set_mic_mute',
                        return_value=(None, 'No microphone found'))
    result = cpa.CrossPlatformAction({'action': 'microphone_mute'}).execute()
    assert result.success is False and 'No microphone found' in result.message


def test_microphone_mute_falls_back_to_nircmd_without_pycaw(mocker):
    mocker.patch.object(cpa, '_SYSTEM', 'Windows')
    mocker.patch.object(cpa, 'set_mic_mute',
                        return_value=(None, cpa.PYCAW_MISSING))
    mocker.patch.object(cpa.CrossPlatformAction, '_check_nircmd',
                        return_value=True)
    run = mocker.patch.object(cpa.CrossPlatformAction, '_run_command',
                              return_value=ActionResult(True, 'ok'))
    cpa.CrossPlatformAction({'action': 'microphone_mute'}).execute()
    run.assert_called_once_with('nircmd.exe mutesysvolume 1 microphone')


# --- catalog action ---------------------------------------------------------

@pytest.fixture
def plugin():
    return pack.Plugin()


def test_spec_is_live_system_button_without_fields(plugin):
    spec = plugin.get_action_specs()[0]
    assert (spec.id, spec.category, spec.label) == ('mic_mute', 'system',
                                                    'Mic Mute')
    assert (spec.poll_seconds, spec.poll_config) == (3, {'op': 'status'})
    assert spec.press == 'run' and spec.config_fields == ()


def test_status_poll_never_writes(plugin, mocker):
    setter = mocker.patch.object(cpa, 'set_mic_mute')
    mocker.patch.object(cpa, 'read_mic_mute', return_value=(True, None))
    result = plugin.execute_action('mic_mute', {'op': 'status'})
    setter.assert_not_called()
    assert result['data'] == {'badge': 'MUTED', 'status': 'critical',
                              'sublabel': 'Microphone'}


def test_live_face(plugin, mocker):
    mocker.patch.object(cpa, 'read_mic_mute', return_value=(False, None))
    data = plugin.execute_action('mic_mute', {'op': 'status'})['data']
    assert (data['badge'], data['status']) == ('LIVE', 'normal')


def test_press_toggles_and_paints_new_state(plugin, mocker):
    setter = mocker.patch.object(cpa, 'set_mic_mute', return_value=(True, None))
    result = plugin.execute_action('mic_mute', {})
    setter.assert_called_once_with(None)
    assert result['success'] and result['data']['badge'] == 'MUTED'


def test_no_microphone_is_a_calm_face(plugin, mocker):
    mocker.patch.object(cpa, 'read_mic_mute',
                        return_value=(None, 'No microphone found'))
    result = plugin.execute_action('mic_mute', {'op': 'status'})
    assert result['message'] == 'No microphone found'
    assert result['data']['badge'] == '!'
    assert result['success'] is True  # a poll is silent; only a press errors


def test_press_without_microphone_is_an_error(plugin, mocker):
    mocker.patch.object(cpa, 'set_mic_mute',
                        return_value=(None, 'No microphone found'))
    result = plugin.execute_action('mic_mute', {})
    assert result['success'] is False
    assert result['message'] == 'No microphone found'


def test_unavailable_off_windows(plugin, mocker):
    mocker.patch.object(pack, '_SYSTEM', 'Linux')
    ok, reason = plugin.is_available()
    assert ok is False and 'Windows' in reason
