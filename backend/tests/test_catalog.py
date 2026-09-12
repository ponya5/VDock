"""Consistency tests for the action catalog.

Feature: ai-dev-integration-packs, Property 1.1: everything the picker offers
is something the backend can actually run.

This is the test that kills the drift. The catalog, the ActionType enum, the
ActionExecutor dispatch table, CrossPlatformAction.VALID_ACTIONS and the
frontend ActionType union all have to agree, and before the catalog existed they
did not: 22 of the 46 entries ButtonActionsSidebar.vue offered dispatched to an
action type with no handler and failed on press.

If you add a catalog entry and one of these fails, the entry is not wired up --
fix the wiring rather than the assertion.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from actions.action_executor import ActionExecutor  # noqa: E402
from actions.catalog import (  # noqa: E402
    ACTION_CATALOG,
    CATALOG_BY_ID,
    CATEGORIES,
    RUNS_BACKEND,
    RUNS_FRONTEND,
    RUNS_WIDGET,
    catalog_to_dict,
    dispatched_action_types,
)
from actions.cross_platform_action import CrossPlatformAction  # noqa: E402
from models.button import ActionType  # noqa: E402

FRONTEND = Path(__file__).resolve().parents[2] / 'frontend'


# --- internal coherence ------------------------------------------------------

def test_catalog_ids_are_unique():
    ids = [spec.id for spec in ACTION_CATALOG]
    assert len(ids) == len(set(ids)), 'duplicate catalog id'


def test_catalog_is_not_empty():
    assert len(ACTION_CATALOG) > 20


@pytest.mark.parametrize('spec', ACTION_CATALOG, ids=lambda s: s.id)
def test_every_entry_uses_a_declared_category(spec):
    assert spec.category in {c.id for c in CATEGORIES}


@pytest.mark.parametrize('spec', ACTION_CATALOG, ids=lambda s: s.id)
def test_every_entry_has_a_valid_runs_on(spec):
    assert spec.runs_on in {RUNS_BACKEND, RUNS_FRONTEND, RUNS_WIDGET}


@pytest.mark.parametrize('spec', ACTION_CATALOG, ids=lambda s: s.id)
def test_every_entry_has_a_label_and_icon(spec):
    assert spec.label.strip()
    assert len(spec.icon) == 2 and all(spec.icon)


# --- the catalog must agree with the backend ---------------------------------

@pytest.mark.parametrize('action_type', sorted(dispatched_action_types()))
def test_every_dispatched_type_has_an_executor_handler(action_type):
    """The defect this whole catalog exists to prevent."""
    assert action_type in ActionExecutor.ACTION_CLASSES, (
        f'{action_type!r} is offered in the picker but ActionExecutor cannot '
        f'dispatch it, so the button fails on press'
    )


@pytest.mark.parametrize('spec', ACTION_CATALOG, ids=lambda s: s.id)
def test_every_action_type_is_persistable(spec):
    """Unknown types no longer 500, but known ones should be real enum members."""
    assert spec.action_type in {member.value for member in ActionType}, (
        f'{spec.action_type!r} is missing from the ActionType enum in '
        f'models/button.py'
    )


_CROSS_PLATFORM = [s for s in ACTION_CATALOG if s.action_type == 'cross_platform']


@pytest.mark.parametrize('spec', _CROSS_PLATFORM, ids=lambda s: s.id)
def test_cross_platform_entries_name_a_real_action(spec):
    """`volume_up` and friends are cross_platform configs, not action types.

    Emitting them as bare action types is exactly what the old sidebar did.
    """
    if spec.id == 'cross_platform':
        return  # the generic escape hatch; the user supplies the action
    action = spec.default_config.get('action')
    assert action, f'{spec.id} must set default_config["action"]'
    assert action in CrossPlatformAction.VALID_ACTIONS, (
        f'{action!r} is not in CrossPlatformAction.VALID_ACTIONS'
    )


_MACRO = [s for s in ACTION_CATALOG if s.action_type == 'macro' and s.default_config]


@pytest.mark.parametrize('spec', _MACRO, ids=lambda s: s.id)
def test_macro_entries_use_supported_step_types(spec):
    supported = {
        'hotkey', 'delay', 'text', 'click',
        'clipboard_copy', 'clipboard_paste', 'clipboard_set',
    }
    for step in spec.default_config.get('steps', []):
        assert step['type'] in supported, (
            f'{spec.id} uses unsupported macro step {step["type"]!r}'
        )


# --- widgets and frontend actions must not need a backend handler ------------

@pytest.mark.parametrize(
    'spec', [s for s in ACTION_CATALOG if s.runs_on == RUNS_WIDGET],
    ids=lambda s: s.id,
)
def test_widgets_are_marked_display_only(spec):
    """Widgets render live data; pressing them must not dispatch."""
    assert spec.display_only is True


def test_widget_types_are_excluded_from_dispatch():
    widget_types = {s.action_type for s in ACTION_CATALOG if s.runs_on == RUNS_WIDGET}
    assert not (widget_types & dispatched_action_types())


# --- the catalog must agree with the frontend --------------------------------

def _ts_action_type_union() -> set:
    src = (FRONTEND / 'src' / 'types' / 'index.ts').read_text(encoding='utf-8')
    block = src[src.index('export type ActionType'):]
    block = block[:block.index('export type ButtonShape')]
    return set(re.findall(r"'([a-z_]+)'", block))


@pytest.mark.parametrize('spec', ACTION_CATALOG, ids=lambda s: s.id)
def test_every_action_type_is_in_the_frontend_union(spec):
    assert spec.action_type in _ts_action_type_union(), (
        f'{spec.action_type!r} is missing from the ActionType union in '
        f'frontend/src/types/index.ts'
    )


def test_sidebar_no_longer_hardcodes_action_strings():
    """The picker must be generated from the catalog, not hand-written.

    Every hardcoded selectAction('...') string was a chance for the sidebar to
    offer something the backend could not run.
    """
    src = (FRONTEND / 'src' / 'components' / 'ButtonActionsSidebar.vue').read_text(
        encoding='utf-8'
    )
    hardcoded = re.findall(r"selectAction\('([a-z_]+)'\)", src)
    assert not hardcoded, (
        f'{len(hardcoded)} hardcoded action strings remain in the sidebar: '
        f'{sorted(set(hardcoded))}'
    )


# --- serialisation -----------------------------------------------------------

def test_catalog_serialises_cleanly():
    import json

    payload = catalog_to_dict()
    json.dumps(payload)  # must not raise

    assert payload['actions']
    assert payload['categories']
    served = {c['id'] for c in payload['categories']}
    used = {a['category'] for a in payload['actions']}
    assert used <= served, 'an action references a category that is not served'


def test_serialised_entry_shape():
    spec = CATALOG_BY_ID['volume_up'].to_dict()
    assert spec['action_type'] == 'cross_platform'
    assert spec['default_config'] == {'action': 'volume_up'}
    assert spec['display_only'] is False


def test_frontend_fallback_covers_every_widget_type():
    """The store's offline fallback must classify every real widget correctly.

    If the catalog request fails, useButtonActions falls back to a naming
    convention to decide what not to dispatch. A widget type that the fallback
    misses would pop an error toast on every press while the backend is down.
    """
    prefixes = ('metric_', 'time_')
    exact = {'weather', 'calendar'}

    widget_types = {
        spec.action_type for spec in ACTION_CATALOG if spec.runs_on == RUNS_WIDGET
    }

    uncovered = {
        t for t in widget_types
        if t not in exact and not t.startswith(prefixes)
    }
    assert not uncovered, (
        f'these widget types are not covered by the frontend fallback in '
        f'stores/actionCatalog.ts: {sorted(uncovered)}'
    )


def test_fallback_does_not_swallow_dispatched_types():
    """The fallback must not stop a real action from dispatching."""
    prefixes = ('metric_', 'time_')
    exact = {'weather', 'calendar'}

    wrongly_caught = {
        t for t in dispatched_action_types()
        if t in exact or t.startswith(prefixes)
    }
    assert not wrongly_caught


# --- shipped scene templates -------------------------------------------------

def _shipped_templates():
    import json
    templates_dir = Path(__file__).resolve().parents[1] / 'data' / 'templates'
    for path in sorted(templates_dir.glob('*.json')):
        yield path.name, json.loads(path.read_text(encoding='utf-8'))


def _runnable_action_types():
    """Catalog types plus everything the integration packs provide."""
    from plugins.plugin_manager import PluginManager

    types = {spec.action_type for spec in ACTION_CATALOG}
    manager = PluginManager()
    manager.load_builtin_packs()
    types |= {spec.action_type for spec in manager.get_action_specs()}
    return types


@pytest.mark.parametrize('name,template', list(_shipped_templates()),
                         ids=lambda v: v if isinstance(v, str) else '')
def test_shipped_templates_only_use_runnable_actions(name, template):
    """A template button with an unknown action type fails on press."""
    runnable = _runnable_action_types()

    unknown = set()
    for page in template.get('pages', []):
        for button in page.get('buttons', []):
            action = button.get('action')
            if action and action.get('type') not in runnable:
                unknown.add(action['type'])

    assert not unknown, f'{name} uses unrunnable action types: {sorted(unknown)}'


@pytest.mark.parametrize('name,template', list(_shipped_templates()),
                         ids=lambda v: v if isinstance(v, str) else '')
def test_shipped_template_buttons_fit_their_grid(name, template):
    for page in template.get('pages', []):
        grid = page.get('grid_config', {'rows': 4, 'cols': 5})
        occupied = set()
        for button in page.get('buttons', []):
            row = button['position']['row']
            col = button['position']['col']
            assert 0 <= row < grid['rows'], f'{name}: row {row} out of range'
            assert 0 <= col < grid['cols'], f'{name}: col {col} out of range'
            assert (row, col) not in occupied, f'{name}: overlap at {row},{col}'
            occupied.add((row, col))


# --- config field names must match what the handler reads --------------------

def _keys_read_by(method_name: str) -> set:
    """Config keys a CrossPlatformAction handler actually reads."""
    import inspect
    source = inspect.getsource(getattr(CrossPlatformAction, method_name))
    return set(re.findall(r"config\.get\(\s*'([a-z_]+)'", source))


_XP_HANDLER_FOR = {
    'open_app': '_open_app',
    'close_app': '_close_app',
    'open_folder': '_open_folder',
    'open_file': '_open_file',
    'screenshot': '_screenshot',
    'run_command': '_run_command_action',
}


@pytest.mark.parametrize(
    'spec',
    [s for s in _CROSS_PLATFORM
     if s.config_fields and s.default_config.get('action') in _XP_HANDLER_FOR],
    ids=lambda s: s.id,
)
def test_cross_platform_config_fields_match_the_handler(spec):
    """A field the handler never reads silently does nothing.

    Caught a real one: the picker offered "Open Application" with a field named
    'app', but CrossPlatformAction._open_app reads 'path' -- so configuring it
    from the UI produced a button that failed with "Application path/name not
    specified". Same for 'close_app', which reads 'app_name'.
    """
    handler = _XP_HANDLER_FOR[spec.default_config['action']]
    try:
        accepted = _keys_read_by(handler)
    except AttributeError:
        pytest.skip(f'{handler} is not a method on CrossPlatformAction')

    if not accepted:
        pytest.skip(f'{handler} reads no config keys')

    for field in spec.config_fields:
        assert field.name in accepted, (
            f'{spec.id} offers a field {field.name!r} that '
            f'CrossPlatformAction.{handler} never reads; it accepts '
            f'{sorted(accepted)}'
        )
