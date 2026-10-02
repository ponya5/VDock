"""Developer tool buttons: run the repo's tests (DL-145).

Logic lives in ``services/``; this pack only exposes it as catalog actions.
"""
from pathlib import Path
from typing import Any, Dict, Sequence

from actions.catalog import ActionSpec, ConfigField, RUNS_BACKEND
from plugins.base_plugin import PluginInfo
from services import agent_prompt, test_runner

from . import context
from .live_pack_base import SpecPlugin


def _specs() -> Sequence[ActionSpec]:
    return (
        ActionSpec(
            id='dev_run_tests', label='Run Tests', category='dev',
            icon=('fas', 'flask'), action_type='dev_run_tests',
            runs_on=RUNS_BACKEND, long_running=True,
            description="Run this project's tests with one tap. The button "
                        'stays green or red until the next run.',
            keywords=('test', 'tests', 'pytest', 'vitest', 'jest', 'ci'),
            poll_seconds=15, poll_config={'op': 'status'},
            config_fields=(
                ConfigField('command', 'Test command', 'text', advanced=True,
                            placeholder='Auto-detected'),
                ConfigField('watch', 'Re-run when files change', 'boolean',
                            default=False, advanced=True),
                ConfigField('cwd', 'Project directory', 'path', advanced=True,
                            help='Empty: the project focused in your editor.'),
            ),
        ),
    )


class Plugin(SpecPlugin):
    """Run Tests."""

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            id='dev_tools', name='Developer Tools', version='1.0.0',
            author='VDock',
            description='One-tap test runs and live developer status.',
            actions=[spec.id for spec in _specs()],
        )

    def is_available(self) -> tuple:
        return True, ''

    def get_action_specs(self) -> Sequence[ActionSpec]:
        return _specs()

    def execute_action(self, action_id: str,
                       config: Dict[str, Any]) -> Dict[str, Any]:
        if action_id == 'dev_run_tests':
            return self._tests(config)
        return {'success': False, 'message': f'Unknown action: {action_id}'}

    def _tests(self, config: Dict[str, Any]) -> Dict[str, Any]:
        repo = context.focused_repo(config.get('cwd') or None)
        op = str(config.get('op') or 'run')

        if op == 'status':
            data = test_runner.status(repo, watch=bool(config.get('watch')))
            return {'success': True, 'message': data['sublabel'],
                    'data': data}
        if op == 'fix':
            return agent_prompt.prompt_preset('fix_tests', cwd=repo)
        if op == 'failure':
            return {'success': True, 'message': 'Last failure',
                    'data': test_runner.status(repo)}

        command = str(config.get('command') or '').strip()
        plans = ([test_runner.plan_from_command(command, repo)] if command
                 else test_runner.detect(repo))
        if not plans:
            return {'success': False,
                    'message': f'No tests found in {Path(repo).name} - set a test '
                               'command under Advanced'}
        return test_runner.run(repo, plans)
