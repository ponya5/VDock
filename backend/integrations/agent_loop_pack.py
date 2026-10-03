"""Agent loop actions: prompts, change review, usage, dictation (DL-145).

Thin catalog entries over services (``services.agent_prompt``,
``services.turn_baseline``, ``services.agent_dictate``...) that Mission
Control uses too.
"""
from datetime import date
from typing import Any, Dict, List, Optional, Sequence

from actions.catalog import (
    ActionSpec, ConfigField, PRESS_HOLD, PRESS_MENU, RUNS_BACKEND,
)
from plugins.base_plugin import PluginInfo
from services import agent_dictate, agent_prompt, claude_usage, turn_baseline

from . import agent_state
from .live_pack_base import SpecPlugin, live_result

MAX_MENU_FILES = 12


def format_cost(usd: float) -> str:
    """'≈$0.42' under ten dollars, '≈$12' above - short enough for a badge."""
    return f'≈${usd:.2f}' if usd < 10 else f'≈${usd:.0f}'


def format_tokens(count: int) -> str:
    if count >= 1_000_000:
        return f'{count / 1_000_000:.1f}M'
    return f'{round(count / 1000)}k' if count >= 1000 else str(count)

_AGENT_FIELD = ConfigField(
    'agent', 'Agent', 'select', default='auto', advanced=True,
    options=tuple({'value': a, 'label': a.capitalize()}
                  for a in agent_prompt.AGENT_CHOICES),
)
_CWD_FIELD = ConfigField(
    'cwd', 'Session directory', 'path', advanced=True,
    help='Empty: the session that is ready (or pinned).',
)


def _specs() -> Sequence[ActionSpec]:
    presets = tuple(
        {'value': key, 'label': preset['label']}
        for key, preset in agent_prompt.PROMPT_PRESETS.items()
    ) + ({'value': 'custom', 'label': 'Custom…'},)
    return (
        ActionSpec(
            id='agent_prompt', label='Agent Prompt', category='ai',
            icon=('fas', 'paper-plane'), action_type='agent_prompt',
            runs_on=RUNS_BACKEND,
            description='Send a ready-made instruction to your agent session '
                        '(Claude Code, Cursor, Devin, Antigravity).',
            keywords=('agent', 'prompt', 'claude', 'cursor', 'tests', 'error',
                      'commit', 'review', 'preset'),
            default_config={'preset': 'continue'},
            config_fields=(
                ConfigField('preset', 'Prompt', 'select', default='continue',
                            options=presets),
                ConfigField('text', 'Custom prompt', 'textarea',
                            show_when={'preset': 'custom'},
                            help='Supports {clipboard}, {last_failure}, '
                                 '{repo}, {project}, {branch}.'),
                _AGENT_FIELD,
                _CWD_FIELD,
                ConfigField('submit', 'Press Enter after typing', 'boolean',
                            default=True, advanced=True),
            ),
        ),
        ActionSpec(
            id='agent_review_changes', label='Review Changes', category='ai',
            icon=('fas', 'code-compare'), action_type='agent_review_changes',
            runs_on=RUNS_BACKEND,
            description='Files your agent changed this turn. Tap to open one '
                        'as a diff in Cursor or VS Code.',
            keywords=('agent', 'diff', 'changes', 'review', 'files', 'git'),
            poll_seconds=20, poll_config={'op': 'status'}, press=PRESS_MENU,
            config_fields=(_AGENT_FIELD, _CWD_FIELD),
        ),
        ActionSpec(
            id='agent_usage', label='Agent Usage', category='ai',
            icon=('fas', 'gauge-high'), action_type='agent_usage',
            runs_on=RUNS_BACKEND,
            description="Today's Claude Code spend and token use. Tap to open "
                        'Mission Control for per-session cost and context.',
            keywords=('agent', 'usage', 'cost', 'tokens', 'claude', 'spend',
                      'context', 'budget'),
            default_config={'daily_limit_usd': 0},
            poll_seconds=60, poll_config={'op': 'status'},
            config_fields=(
                ConfigField('daily_limit_usd', 'Daily budget (USD)', 'number',
                            default=0,
                            help='0 = no warning colour. API-equivalent spend; '
                                 'subscription plans are not billed per token.'),
                ConfigField('metric', 'Show', 'select', default='cost',
                            advanced=True, options=(
                                {'value': 'cost', 'label': 'Estimated cost'},
                                {'value': 'tokens', 'label': 'Tokens'})),
            ),
        ),
        ActionSpec(
            id='agent_dictate', label='Dictate to Agent', category='ai',
            icon=('fas', 'microphone'), action_type='agent_dictate',
            runs_on=RUNS_BACKEND,
            description='Hold to talk; release to stop. Uses Windows voice '
                        'typing (Win+H) in your agent session. Text is not '
                        'sent until you tap Submit.',
            keywords=('agent', 'dictate', 'voice', 'speak', 'talk', 'speech',
                      'microphone', 'push to talk', 'ptt'),
            press=PRESS_HOLD,
            unavailable_reason=agent_dictate.voice_typing_platform_blocker(),
            config_fields=(_AGENT_FIELD, _CWD_FIELD),
        ),
    )


def _pick_session(agent: str, cwd: Optional[str]) -> Optional[Dict[str, Any]]:
    """The ready session (else the newest) that has a directory."""
    sources = [agent] if agent in agent_prompt.PROMPT_SOURCES \
        else list(agent_state.snapshot())
    entries: List[Dict[str, Any]] = []
    for source in sources:
        entries.extend(e for e in agent_state.session_entries(source)
                       if e.get('cwd'))
    if cwd:
        entries = [e for e in entries
                   if agent_prompt.cwd_matches(e['cwd'], cwd)]
    entries.sort(key=lambda e: (e.get('state') != agent_state.STATE_READY,
                                -(e.get('ts') or 0)))
    return entries[0] if entries else None


class Plugin(SpecPlugin):
    """Agent Prompt + Review Changes."""

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            id='agent_loop', name='Agent Loop', version='1.0.0',
            author='VDock',
            description='Prompt presets and a per-turn change review for '
                        'agent sessions.',
            actions=[spec.id for spec in _specs()],
        )

    def is_available(self) -> tuple:
        try:
            from actions.hotkey_action import PYNPUT_AVAILABLE
        except ImportError:
            PYNPUT_AVAILABLE = False
        if not PYNPUT_AVAILABLE:
            return False, ('pynput is not installed, so VDock cannot send '
                           'keystrokes. Run: pip install pynput')
        return True, ''

    def get_action_specs(self) -> Sequence[ActionSpec]:
        return _specs()

    def execute_action(self, action_id: str,
                       config: Dict[str, Any]) -> Dict[str, Any]:
        if action_id == 'agent_prompt':
            return self._prompt(config)
        if action_id == 'agent_review_changes':
            return self._review(config)
        if action_id == 'agent_usage':
            return self._usage(config)
        if action_id == 'agent_dictate':
            return agent_dictate.dictate(
                str(config.get('op') or ''),
                agent=str(config.get('agent') or 'auto'),
                cwd=config.get('cwd') or None)
        return {'success': False, 'message': f'Unknown action: {action_id}'}

    # --- agent_prompt --------------------------------------------------------

    def _prompt(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return agent_prompt.prompt_preset(
            str(config.get('preset') or 'continue'),
            custom_text=str(config.get('text') or ''),
            agent=str(config.get('agent') or 'auto'),
            cwd=config.get('cwd') or None,
            submit=bool(config.get('submit', True)),
        )

    # --- agent_usage ---------------------------------------------------------

    def _usage(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            limit = max(0.0, float(config.get('daily_limit_usd') or 0))
        except (TypeError, ValueError):
            limit = 0.0
        by_tokens = config.get('metric') == 'tokens'
        try:
            today = claude_usage.today_usage(date.today())
        except OSError as error:
            return live_result(f'Could not read Claude Code usage: {error}', '!',
                               success=False)

        tokens, cost = today['tokens']['total'], today['cost_usd']
        if not tokens:
            result = live_result('No Claude Code usage today',
                                 '0' if by_tokens else '$0', sublabel='today')
        else:
            status = 'normal' if by_tokens \
                else claude_usage.limit_status(cost, limit)
            badge = format_tokens(tokens) if by_tokens else format_cost(cost)
            result = live_result(
                f'{format_cost(cost)} today ({format_tokens(tokens)} tokens, '
                'API-equivalent estimate)', badge, status=status,
                sublabel='today')
        result['data']['open_mission_control'] = True
        return result

    # --- agent_review_changes ------------------------------------------------

    def _review(self, config: Dict[str, Any]) -> Dict[str, Any]:
        session = _pick_session(str(config.get('agent') or 'auto'),
                                config.get('cwd') or None)
        if session is None:
            return live_result('No agent session yet', '–',
                               sublabel='no session')

        op = str(config.get('op') or 'status')
        source, session_id, cwd = (session['source'], session['session_id'],
                                   session['cwd'])
        if op.startswith('open:'):
            opened = turn_baseline.open_diff(source, session_id, cwd,
                                             op[len('open:'):])
            return {'success': bool(opened.get('success')),
                    'message': opened.get('message', ''),
                    'details': opened.get('details', '')}

        changes = turn_baseline.changes(source, session_id, cwd)
        if not changes.get('success'):
            return live_result(changes.get('message', 'Not a git repository'),
                               '–', sublabel='no repo')

        totals = changes['totals']
        since = ' since last commit' if changes['base']['kind'] == 'head' else ''
        if not totals['files']:
            return live_result('No changes this turn' + since, '0',
                               sublabel='no changes')

        stats = f"+{totals['added']} −{totals['removed']}"
        menu = [{'id': f"open:{f['path']}",
                 'label': f"{f['path']}  +{f['added']} −{f['removed']}"}
                for f in changes['files'][:MAX_MENU_FILES]]
        return live_result(
            f"{totals['files']} files changed{since}", str(totals['files']),
            status='warning', sublabel=stats + since, menu=menu)
