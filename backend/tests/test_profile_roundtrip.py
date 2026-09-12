"""Round-trip tests for the Button / ButtonAction persistence models.

Feature: ai-dev-integration-packs, Property 0.2: saving a profile never loses
button data and never 500s on an unrecognised enum value.

PUT /api/profiles/<id> rebuilds the profile through Profile.from_dict() and
persists Profile.to_dict(). That means from_dict is a lossy gate on every save:
a field it ignores is destroyed, and a value it cannot parse raises and becomes
a 500. Both happened in practice --

  * ActionType(data['type']) raised for action types that exist in
    ActionExecutor.ACTION_CLASSES but not in the enum (ui_control, system,
    metric_disk, metric_network, metric_temperature, metric_battery), and for
    every new type an integration pack adds.
  * ButtonShape(...) raised for 'hexagon', 'diamond' and 'octagon', which the
    frontend ButtonShape union has offered all along.
  * 'layers' -- the whole visual layer model -- was silently dropped.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.button import ActionType, Button, ButtonAction, ButtonShape  # noqa: E402


def _button(**overrides):
    data = {
        'id': 'btn_1',
        'label': 'Test',
        'shape': 'rounded',
        'position': {'row': 0, 'col': 0},
        'size': {'rows': 1, 'cols': 1},
        'enabled': True,
    }
    data.update(overrides)
    return data


# --- unrecognised action types must survive, not raise -----------------------

@pytest.mark.parametrize('action_type', [
    'ui_control', 'system', 'metric_disk', 'metric_network',
    'metric_temperature', 'metric_battery',
])
def test_action_types_in_the_executor_round_trip(action_type):
    """Types ActionExecutor can dispatch must be persistable."""
    button = Button.from_dict(_button(action={'type': action_type, 'config': {}}))
    assert button.to_dict()['action']['type'] == action_type


def test_unknown_action_type_survives_instead_of_raising():
    """A future integration-pack action must not break the profile save."""
    button = Button.from_dict(
        _button(action={'type': 'claude_prompt', 'config': {'prompt': 'hi'}})
    )
    out = button.to_dict()
    assert out['action']['type'] == 'claude_prompt'
    assert out['action']['config'] == {'prompt': 'hi'}


def test_known_action_type_is_still_the_enum():
    """Recognised values stay strongly typed."""
    button = Button.from_dict(_button(action={'type': 'hotkey', 'config': {}}))
    assert button.action.type is ActionType.HOTKEY


# --- shapes the frontend already offers --------------------------------------

@pytest.mark.parametrize('shape', [
    'rectangle', 'rounded', 'circle', 'hexagon', 'diamond', 'octagon',
])
def test_every_frontend_shape_round_trips(shape):
    button = Button.from_dict(_button(shape=shape))
    assert button.to_dict()['shape'] == shape


def test_known_shape_is_still_the_enum():
    assert Button.from_dict(_button(shape='circle')).shape is ButtonShape.CIRCLE


# --- fields that were being dropped ------------------------------------------

def test_layers_survive_the_round_trip():
    layers = {
        'fill': {'type': 'gradient', 'value': 'linear-gradient(#000,#fff)'},
        'effect': {'type': 'aurora', 'tint': 'brand', 'intensity': 60},
        'icon': {'type': 'logo', 'value': '/logos/claude-color.png'},
        'label': {'text': 'Claude', 'secondary': 'Ask'},
        'behaviour': 'breathe',
    }
    button = Button.from_dict(_button(layers=layers))
    assert button.to_dict()['layers'] == layers


def test_button_without_layers_round_trips_cleanly():
    out = Button.from_dict(_button()).to_dict()
    assert out.get('layers') is None


def test_fontawesome_icon_array_survives():
    """Frontend icons are often ['fas', 'home'], not a plain string."""
    out = Button.from_dict(_button(icon=['fas', 'home'])).to_dict()
    assert out['icon'] == ['fas', 'home']


def test_action_to_dict_is_stable_across_two_round_trips():
    """Simulates saving the same profile twice."""
    first = Button.from_dict(
        _button(action={'type': 'claude_prompt', 'config': {'prompt': 'hi'}},
                shape='hexagon')
    ).to_dict()
    second = Button.from_dict(first).to_dict()
    assert first == second
