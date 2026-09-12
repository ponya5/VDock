"""Claude integration pack: Claude Code CLI, the Messages API, and the apps.

Three transports, because they are good at different things:

* **Claude Code CLI** (``claude -p``) -- the default. Reuses the user's existing
  login, sees the repo it runs in, and can run slash commands. No key needed.
* **Messages API** -- for short one-shot prompts whose answer you want on the
  clipboard or typed into the focused window. Needs ANTHROPIC_API_KEY.
* **Desktop / web** -- open or focus the Claude app, or claude.ai.

Prompts are user-authored free text and are passed to the CLI as argv entries
through ``utils.subprocess_runner``, never through a shell. A prompt containing
``;`` or backticks is a prompt, not a command.
"""
import logging
from typing import Any, Dict, List, Optional, Sequence

from actions.catalog import ActionSpec, ConfigField, RUNS_BACKEND
from plugins.base_plugin import BasePlugin, PluginInfo
from services import secrets
from utils import subprocess_runner as sr

from . import context

logger = logging.getLogger('vdock')

CLAUDE_BINARY = 'claude'

# Model ids offered in the button editor. `claude-opus-5` is the default;
# the cheaper models are there for high-frequency buttons.
MODEL_OPTIONS = (
    {'value': 'claude-opus-5', 'label': 'Opus 5 (most capable)'},
    {'value': 'claude-sonnet-5', 'label': 'Sonnet 5 (balanced)'},
    {'value': 'claude-haiku-4-5', 'label': 'Haiku 4.5 (fastest)'},
)
DEFAULT_MODEL = 'claude-opus-5'

# How an action's result is delivered.
OUTPUT_OPTIONS = (
    {'value': 'notify', 'label': 'Show a notification'},
    {'value': 'clipboard', 'label': 'Copy to clipboard'},
    {'value': 'both', 'label': 'Notification and clipboard'},
)

_PROMPT_FIELD = ConfigField(
    'prompt', 'Prompt', 'textarea', required=True,
    placeholder='Review the staged changes in {repo} and suggest a commit message',
    help='Supports {clipboard}, {repo}, {project} and {branch}.',
)
_CWD_FIELD = ConfigField(
    'cwd', 'Working directory', 'path',
    placeholder='Leave blank to use the focused editor\'s project',
    help='Blank means VDock infers the project from the focused editor window.',
)
_MODEL_FIELD = ConfigField(
    'model', 'Model', 'select', default=DEFAULT_MODEL, options=MODEL_OPTIONS,
)
_OUTPUT_FIELD = ConfigField(
    'output', 'Result', 'select', default='notify', options=OUTPUT_OPTIONS,
)


def _deliver(text: str, mode: str) -> Dict[str, Any]:
    """Put ``text`` where the button asked for it."""
    data: Dict[str, Any] = {'text': text}

    if mode in ('clipboard', 'both'):
        try:
            import pyperclip
            pyperclip.copy(text)
            data['copied'] = True
        except Exception as e:
            logger.warning('Could not copy the result to the clipboard: %s', e)
            data['copied'] = False

    return data


class Plugin(BasePlugin):
    """Claude actions."""

    def __init__(self) -> None:
        super().__init__()
        self.cli_path: Optional[str] = None

    # --- lifecycle -----------------------------------------------------------

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            id='claude',
            name='Claude',
            version='1.0.0',
            author='VDock',
            description='Run Claude Code, call the Messages API, open Claude.',
            actions=[
                'claude_prompt',
                'claude_slash',
                'claude_continue',
                'claude_api_prompt',
                'claude_open',
            ],
        )

    def initialize(self) -> bool:
        self.cli_path = sr.find_binary(CLAUDE_BINARY)
        if self.cli_path:
            logger.info('Claude Code CLI found at %s', self.cli_path)
        else:
            logger.info(
                'Claude Code CLI not on PATH; CLI actions will be unavailable'
            )
        # The pack still loads: claude_open works with nothing installed, and
        # claude_api_prompt only needs a key.
        return True

    def cleanup(self) -> None:
        pass

    def is_available(self) -> tuple:
        if self.cli_path or secrets.is_configured(secrets.ANTHROPIC_API_KEY):
            return True, ''
        return False, (
            'Neither the Claude Code CLI nor ANTHROPIC_API_KEY was found. '
            'Install Claude Code, or set ANTHROPIC_API_KEY in backend/.env.'
        )

    # --- catalog -------------------------------------------------------------

    def get_action_specs(self) -> Sequence[ActionSpec]:
        cli_missing = None if self.cli_path else (
            'Claude Code CLI not found on PATH. Install it from '
            'https://claude.com/product/claude-code'
        )
        api_missing = None if secrets.is_configured(secrets.ANTHROPIC_API_KEY) \
            else secrets.ANTHROPIC_API_KEY.reason()

        return (
            ActionSpec(
                id='claude_prompt', label='Ask Claude Code', category='ai',
                icon=('fas', 'robot'), action_type='claude_prompt',
                runs_on=RUNS_BACKEND, long_running=True,
                description='Run a prompt through the Claude Code CLI in your '
                            'project and return the answer.',
                keywords=('claude', 'ai', 'cli', 'prompt', 'anthropic'),
                default_config={'model': DEFAULT_MODEL, 'output': 'notify'},
                config_fields=(
                    _PROMPT_FIELD, _CWD_FIELD, _MODEL_FIELD, _OUTPUT_FIELD,
                    ConfigField('continue_session', 'Continue last session',
                                'boolean', default=False,
                                help='Reuse the most recent session in this '
                                     'directory instead of starting fresh.'),
                ),
                unavailable_reason=cli_missing,
            ),
            ActionSpec(
                id='claude_slash', label='Claude Slash Command', category='ai',
                icon=('fas', 'terminal'), action_type='claude_slash',
                runs_on=RUNS_BACKEND, long_running=True,
                description='Run a Claude Code slash command, such as '
                            '/code-review or /commit.',
                keywords=('claude', 'slash', 'review', 'commit', 'command'),
                default_config={'command': '/code-review', 'output': 'notify'},
                config_fields=(
                    ConfigField('command', 'Slash command', 'text',
                                required=True, default='/code-review',
                                placeholder='/code-review'),
                    ConfigField('args', 'Arguments', 'text',
                                placeholder='Optional extra text'),
                    _CWD_FIELD, _MODEL_FIELD, _OUTPUT_FIELD,
                ),
                unavailable_reason=cli_missing,
            ),
            ActionSpec(
                id='claude_continue', label='Open Claude Code', category='ai',
                icon=('fas', 'window-maximize'), action_type='claude_continue',
                runs_on=RUNS_BACKEND,
                description='Open an interactive Claude Code session in a new '
                            'terminal, optionally resuming the last one.',
                keywords=('claude', 'resume', 'continue', 'terminal', 'session'),
                default_config={'resume': True},
                config_fields=(
                    _CWD_FIELD,
                    ConfigField('resume', 'Resume last session', 'boolean',
                                default=True),
                ),
                unavailable_reason=cli_missing,
            ),
            ActionSpec(
                id='claude_api_prompt', label='Ask Claude (API)', category='ai',
                icon=('fas', 'comment-dots'), action_type='claude_api_prompt',
                runs_on=RUNS_BACKEND, long_running=True,
                description='Send a one-shot prompt to the Messages API and put '
                            'the answer on the clipboard.',
                keywords=('claude', 'api', 'anthropic', 'prompt', 'ask'),
                default_config={
                    'model': DEFAULT_MODEL, 'output': 'both',
                    'max_tokens': 2048, 'effort': 'low',
                },
                config_fields=(
                    _PROMPT_FIELD,
                    ConfigField('system', 'System prompt', 'textarea',
                                placeholder='Answer in one short paragraph.'),
                    _MODEL_FIELD,
                    ConfigField('max_tokens', 'Max response tokens', 'number',
                                default=2048),
                    ConfigField(
                        'effort', 'Effort', 'select', default='low',
                        options=(
                            {'value': 'low', 'label': 'Low (fastest)'},
                            {'value': 'medium', 'label': 'Medium'},
                            {'value': 'high', 'label': 'High'},
                        ),
                        help='Low keeps a deck button snappy.',
                    ),
                    _OUTPUT_FIELD,
                ),
                unavailable_reason=api_missing,
            ),
            ActionSpec(
                id='claude_open', label='Open Claude', category='ai',
                icon=('fas', 'external-link-alt'), action_type='claude_open',
                runs_on=RUNS_BACKEND,
                description='Open the Claude desktop app or claude.ai.',
                keywords=('claude', 'app', 'web', 'chat', 'anthropic'),
                default_config={'target': 'web'},
                config_fields=(
                    ConfigField('target', 'Open', 'select', default='web',
                                options=(
                                    {'value': 'web', 'label': 'claude.ai'},
                                    {'value': 'new_chat', 'label': 'claude.ai (new chat)'},
                                    {'value': 'desktop', 'label': 'Claude desktop app'},
                                )),
                ),
            ),
        )

    def get_action_schema(self, action_id: str) -> Dict[str, Any]:
        # get_action_specs() is authoritative; this stays for the BasePlugin
        # contract and any caller that still asks for JSON schema.
        for spec in self.get_action_specs():
            if spec.id == action_id:
                return {
                    'type': 'object',
                    'properties': {
                        f.name: {'type': 'string', 'title': f.label}
                        for f in spec.config_fields
                    },
                    'required': [f.name for f in spec.config_fields if f.required],
                }
        return {}

    # --- dispatch ------------------------------------------------------------

    def execute_action(self, action_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        handlers = {
            'claude_prompt': self._prompt,
            'claude_slash': self._slash,
            'claude_continue': self._continue,
            'claude_api_prompt': self._api_prompt,
            'claude_open': self._open,
        }
        handler = handlers.get(action_id)
        if handler is None:
            return {'success': False, 'message': f'Unknown action: {action_id}'}
        return handler(config)

    def _require_cli(self) -> Optional[Dict[str, Any]]:
        if self.cli_path:
            return None
        return {
            'success': False,
            'message': 'Claude Code CLI not found',
            'details': (
                "The 'claude' command is not on PATH. Install Claude Code, or "
                'use the "Ask Claude (API)" action instead.'
            ),
        }

    def _run_cli(
        self, argv: List[str], cwd: str, output_mode: str, timeout: int = 600
    ) -> Dict[str, Any]:
        """Run the CLI and shape the result for the frontend."""
        try:
            result = sr.run(argv, cwd=cwd, timeout=timeout)
        except sr.BinaryNotFoundError as e:
            return {'success': False, 'message': str(e)}

        text = secrets.redact(result.output)

        if not result.ok:
            return {
                'success': False,
                'message': (
                    'Claude Code timed out' if result.timed_out
                    else 'Claude Code failed'
                ),
                'details': text or f'exit code {result.exit_code}',
                'data': {'exit_code': result.exit_code, 'cwd': cwd},
            }

        data = _deliver(text, output_mode)
        data['cwd'] = cwd
        return {
            'success': True,
            'message': result.summary() or 'Claude Code finished',
            'data': data,
        }

    def _prompt(self, config: Dict[str, Any]) -> Dict[str, Any]:
        missing = self._require_cli()
        if missing:
            return missing

        prompt = (config.get('prompt') or '').strip()
        if not prompt:
            return {'success': False, 'message': 'No prompt configured'}

        cwd = context.resolve_cwd(config.get('cwd'))
        prompt = context.expand_placeholders(prompt, cwd)

        argv = [CLAUDE_BINARY]
        if config.get('continue_session'):
            argv.append('--continue')
        model = config.get('model') or DEFAULT_MODEL
        argv += ['--model', model, '-p', prompt]

        return self._run_cli(argv, cwd, config.get('output', 'notify'))

    def _slash(self, config: Dict[str, Any]) -> Dict[str, Any]:
        missing = self._require_cli()
        if missing:
            return missing

        command = (config.get('command') or '').strip()
        if not command:
            return {'success': False, 'message': 'No slash command configured'}
        if not command.startswith('/'):
            command = f'/{command}'

        args = (config.get('args') or '').strip()
        cwd = context.resolve_cwd(config.get('cwd'))
        full = f'{command} {args}'.strip()
        full = context.expand_placeholders(full, cwd)

        argv = [CLAUDE_BINARY, '--model',
                config.get('model') or DEFAULT_MODEL, '-p', full]
        return self._run_cli(argv, cwd, config.get('output', 'notify'))

    def _continue(self, config: Dict[str, Any]) -> Dict[str, Any]:
        missing = self._require_cli()
        if missing:
            return missing

        cwd = context.resolve_cwd(config.get('cwd'))
        argv = [CLAUDE_BINARY]
        if config.get('resume', True):
            argv.append('--continue')

        try:
            sr.spawn(argv, cwd=cwd)
        except (sr.BinaryNotFoundError, OSError) as e:
            return {'success': False, 'message': f'Could not start Claude Code: {e}'}

        return {
            'success': True,
            'message': f'Claude Code opened in {cwd}',
            'data': {'cwd': cwd},
        }

    def _api_prompt(self, config: Dict[str, Any]) -> Dict[str, Any]:
        api_key = secrets.get(secrets.ANTHROPIC_API_KEY)
        if not api_key:
            return {
                'success': False,
                'message': 'ANTHROPIC_API_KEY is not set',
                'details': secrets.ANTHROPIC_API_KEY.reason(),
            }

        try:
            import anthropic
        except ImportError:
            return {
                'success': False,
                'message': 'The anthropic package is not installed',
                'details': 'Run: pip install anthropic',
            }

        prompt = (config.get('prompt') or '').strip()
        if not prompt:
            return {'success': False, 'message': 'No prompt configured'}
        prompt = context.expand_placeholders(prompt)

        request: Dict[str, Any] = {
            'model': config.get('model') or DEFAULT_MODEL,
            'max_tokens': int(config.get('max_tokens') or 2048),
            'messages': [{'role': 'user', 'content': prompt}],
            # Effort keeps a deck button responsive. Note that `budget_tokens`
            # is rejected on current models -- thinking is adaptive.
            'output_config': {'effort': config.get('effort') or 'low'},
        }
        system = (config.get('system') or '').strip()
        if system:
            request['system'] = system

        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(**request)
        except anthropic.RateLimitError:
            return {'success': False, 'message': 'Rate limited by the Anthropic API'}
        except anthropic.AuthenticationError:
            return {'success': False, 'message': 'ANTHROPIC_API_KEY was rejected'}
        except anthropic.APIStatusError as e:
            return {
                'success': False,
                'message': f'Anthropic API error ({e.status_code})',
                'details': secrets.redact(str(e)),
            }
        except anthropic.APIConnectionError:
            return {'success': False, 'message': 'Could not reach the Anthropic API'}
        except Exception as e:  # pragma: no cover - defensive
            return {
                'success': False,
                'message': 'Anthropic request failed',
                'details': secrets.redact(str(e)),
            }

        # Always check stop_reason before reading content.
        if getattr(response, 'stop_reason', None) == 'refusal':
            details = getattr(response, 'stop_details', None)
            return {
                'success': False,
                'message': 'Claude declined this request',
                'details': getattr(details, 'explanation', '') or '',
            }

        text = '\n'.join(
            block.text for block in response.content
            if getattr(block, 'type', None) == 'text'
        ).strip()

        if not text:
            return {'success': False, 'message': 'Claude returned no text'}

        data = _deliver(text, config.get('output', 'both'))
        usage = getattr(response, 'usage', None)
        if usage is not None:
            data['usage'] = {
                'input_tokens': getattr(usage, 'input_tokens', None),
                'output_tokens': getattr(usage, 'output_tokens', None),
            }

        return {
            'success': True,
            'message': text if len(text) <= 200 else text[:199] + '…',
            'data': data,
        }

    def _open(self, config: Dict[str, Any]) -> Dict[str, Any]:
        from actions.cross_platform_action import CrossPlatformAction

        target = config.get('target') or 'web'
        if target == 'desktop':
            action = CrossPlatformAction({'action': 'open_app', 'app': 'Claude'})
        else:
            url = ('https://claude.ai/new' if target == 'new_chat'
                   else 'https://claude.ai')
            action = CrossPlatformAction({'action': 'open_url', 'url': url})

        result = action.execute()
        return {
            'success': result.success,
            'message': result.message,
            'data': result.data,
        }
