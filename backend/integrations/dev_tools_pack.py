"""Developer tool buttons: tests, git, dev servers, Docker (DL-145).

Logic lives in ``services/``; this pack only exposes it as catalog actions.
"""
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from actions.catalog import (ActionSpec, ConfigField, PRESS_MENU, RUNS_BACKEND)
from plugins.base_plugin import PluginInfo
from services import (agent_prompt, dev_servers, docker_status, git_context,
                      test_runner)
from utils import subprocess_runner as sr

from . import context
from .live_pack_base import SpecPlugin

_CWD_FIELD = ConfigField(
    'cwd', 'Project directory', 'path', advanced=True,
    help='Empty: the project focused in your editor.')


def _live_menu_spec(action_id: str, label: str, icon: str, description: str,
                    keywords: Sequence[str], poll_seconds: int,
                    unavailable_reason: Optional[str] = None) -> ActionSpec:
    """A live button with no visible field whose press opens a menu."""
    return ActionSpec(
        id=action_id, label=label, category='dev', icon=('fas', icon),
        action_type=action_id, runs_on=RUNS_BACKEND,
        description=description, keywords=tuple(keywords),
        poll_seconds=poll_seconds, poll_config={'op': 'status'},
        press=PRESS_MENU, config_fields=(_CWD_FIELD,),
        unavailable_reason=unavailable_reason,
    )


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
                _CWD_FIELD,
            ),
        ),
        _live_menu_spec(
            'git_context', 'Git Branch', 'code-branch',
            'Branch, changed files and ahead/behind at a glance. Tap for '
            'pull, push, stash and pull request.',
            ('git', 'status', 'branch', 'commit', 'push', 'pull', 'stash',
             'pr'), 30),
        _live_menu_spec(
            'dev_servers', 'Dev Servers', 'server',
            'Shows the dev servers running on this machine. Tap to open, '
            'restart or stop one.',
            ('server', 'port', 'localhost', 'vite', 'node', 'dev'), 10),
        _live_menu_spec(
            'docker_status', 'Docker Containers', 'cubes',
            'Shows how many containers or compose services are up. Tap to '
            'start, stop, restart or read logs.',
            ('docker', 'compose', 'container', 'logs'), 20,
            None if sr.find_binary('docker')
            else 'Docker CLI not found - install Docker Desktop'),
    )


_LIVE_SERVICES: Dict[str, Any] = {
    'git_context': git_context,
    'dev_servers': dev_servers,
    'docker_status': docker_status,
}


class Plugin(SpecPlugin):
    """Run Tests, Git Branch, Dev Servers and Docker Containers."""

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
        service = _LIVE_SERVICES.get(action_id)
        if service is None:
            return {'success': False, 'message': f'Unknown action: {action_id}'}
        return self._live(service, config)

    @staticmethod
    def _live(service, config: Dict[str, Any]) -> Dict[str, Any]:
        """Status read by default; ``config.op`` runs a menu item."""
        repo = context.focused_repo(config.get('cwd') or None)
        op = str(config.get('op') or 'status')
        try:
            if op == 'status':
                return service.status(repo)
            return service.run_op(repo, op)
        except sr.BinaryNotFoundError as e:
            return {'success': False, 'message': str(e)}

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
