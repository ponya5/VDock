"""Live system buttons whose face mirrors real OS state (DL-145).

Mic Mute reads and sets the default capture device's mute flag - the same
flag Windows Settings, Teams and hardware mute keys use - so the button
stays in step with them instead of tracking its own toggle.
"""
import platform
from typing import Any, Dict, Sequence

from actions import cross_platform_action as xp
from actions.catalog import ActionSpec, RUNS_BACKEND
from plugins.base_plugin import PluginInfo

from .live_pack_base import SpecPlugin, live_result

_SYSTEM = platform.system()


def _specs() -> Sequence[ActionSpec]:
    return (
        ActionSpec(
            id='mic_mute', label='Mic Mute', category='system',
            icon=('fas', 'microphone-slash'), action_type='mic_mute',
            runs_on=RUNS_BACKEND,
            description='Mute or unmute your microphone with one tap. The '
                        'button shows MUTED or LIVE, even when you mute from '
                        'Teams, Zoom or a keyboard key.',
            keywords=('mic', 'microphone', 'mute', 'unmute', 'meeting',
                      'call', 'teams', 'zoom'),
            poll_seconds=3, poll_config={'op': 'status'},
        ),
    )


class Plugin(SpecPlugin):
    """Mic Mute."""

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            id='system_live', name='System Status', version='1.0.0',
            author='VDock',
            description='Buttons that show live system state.',
            actions=[spec.id for spec in _specs()],
        )

    def is_available(self) -> tuple:
        if _SYSTEM != 'Windows':
            return False, 'Mic Mute is only available on Windows'
        return True, ''

    def get_action_specs(self) -> Sequence[ActionSpec]:
        return _specs()

    def execute_action(self, action_id: str,
                       config: Dict[str, Any]) -> Dict[str, Any]:
        if action_id != 'mic_mute':
            return {'success': False, 'message': f'Unknown action: {action_id}'}
        reading = str(config.get('op') or '') == 'status'
        muted, err = (xp.read_mic_mute() if reading
                      else xp.set_mic_mute(None))
        if muted is None:
            # A poll is silent (the face says why); only a press is an error.
            return live_result(err, '!', success=reading)
        return live_result('Microphone muted' if muted else 'Microphone live',
                           'MUTED' if muted else 'LIVE',
                           'critical' if muted else 'normal',
                           sublabel='Microphone')
