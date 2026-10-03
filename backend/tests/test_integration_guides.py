"""Starter scenes in Settings → Accounts & keys must only use real action ids.

The scene definitions live in the frontend (``data/integrationGuides.ts``); a
typo there would ship a dead button, so every action type is checked against
the backend's own catalog.
"""
import re
from pathlib import Path

import pytest

GUIDES = Path(__file__).resolve().parents[2] / 'frontend' / 'src' / 'data' / 'integrationGuides.ts'


def _scene_action_types(source: str) -> dict:
    """{guide id: set(action types)} read from the TypeScript source."""
    out = {}
    for block in re.split(r"\n  (?=[A-Z_]+: \{\n    id: ')", source):
        m = re.match(r"([A-Z_]+): \{\n    id: '([A-Z_]+)'", block)
        if not m:
            continue
        types = set(re.findall(r"\bgh\('([a-z_]+)'", block))
        types |= set(re.findall(r"type: '([a-z_]+)'", block))
        out[m.group(2)] = types
    return out


def _backend_action_ids() -> set:
    from integrations import github_pack, claude_pack

    ids = set()
    for pack in (github_pack, claude_pack):
        ids |= {spec.id for spec in pack.Plugin().get_action_specs()}
    return ids


@pytest.fixture(scope='module')
def scene_types():
    return _scene_action_types(GUIDES.read_text(encoding='utf-8'))


def test_every_integration_has_a_guide_with_a_scene(scene_types):
    assert set(scene_types) == {'GITHUB_TOKEN', 'ANTHROPIC_API_KEY', 'WEATHERAPI_KEY'}
    assert all(scene_types.values())


def test_github_scene_uses_real_github_actions(scene_types):
    assert scene_types['GITHUB_TOKEN'] <= _backend_action_ids()


def test_claude_scene_uses_the_real_api_action(scene_types):
    assert scene_types['ANTHROPIC_API_KEY'] == {'claude_api_prompt'}
    assert 'claude_api_prompt' in _backend_action_ids()


def test_weather_scene_uses_the_weather_action(scene_types):
    from actions import catalog
    assert scene_types['WEATHERAPI_KEY'] == {'weather'}
    assert 'weather' in {spec.id for spec in catalog._WEATHER}
