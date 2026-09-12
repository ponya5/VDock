"""Tests for the toggle and random composite actions.

Feature: ai-dev-integration-packs, Property 3.2: Stream Deck parity for
composite buttons.

A toggle is one button doing an on/off pair -- mute/unmute, start/stop -- which
otherwise costs two keys on a grid where space is the scarce resource. Random
is the basis of a soundboard shuffle key.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from actions.action_executor import ActionExecutor  # noqa: E402
from actions.base_action import ActionResult  # noqa: E402
from actions import toggle_action  # noqa: E402
from actions.random_action import RandomAction  # noqa: E402
from actions.toggle_action import ToggleAction  # noqa: E402


class RecordingExecutor:
    """Stands in for ActionExecutor, recording what it was asked to run."""

    def __init__(self, succeed=True):
        self.calls = []
        self.succeed = succeed

    def execute_action(self, action):
        self.calls.append(action)
        return ActionResult(self.succeed, f"ran {action['type']}")


@pytest.fixture(autouse=True)
def clear_toggle_state():
    toggle_action.reset_all()
    yield
    toggle_action.reset_all()


def make_toggle(**overrides):
    config = {
        'toggle_id': 'btn_test',
        'on_action': {'type': 'url', 'config': {'url': 'https://on'}},
        'off_action': {'type': 'url', 'config': {'url': 'https://off'}},
        'on_label': 'Muted',
        'off_label': 'Unmuted',
    }
    config.update(overrides)
    action = ToggleAction(config)
    action.executor = RecordingExecutor()
    return action


# --- toggle ------------------------------------------------------------------

def test_toggle_alternates_between_its_two_actions():
    action = make_toggle()

    action.execute()
    action.execute()
    action.execute()

    urls = [c['config']['url'] for c in action.executor.calls]
    assert urls == ['https://on', 'https://off', 'https://on']


def test_toggle_reports_the_side_it_moved_to():
    action = make_toggle()

    first = action.execute()
    second = action.execute()

    assert first.data['side'] == 1
    assert second.data['side'] == 0


def test_toggle_surfaces_the_side_label_for_the_button_face():
    action = make_toggle()

    first = action.execute()

    assert 'Muted' in first.message
    assert first.data['sublabel'] == 'Unmuted'  # what the next press will do


def test_a_failed_action_does_not_flip_the_switch():
    """A failed action did not change the world; the button must not claim it."""
    action = make_toggle()
    action.executor = RecordingExecutor(succeed=False)

    first = action.execute()
    action.execute()

    assert first.success is False
    # Both presses ran the *same* side, because the first never took effect.
    assert [c['config']['url'] for c in action.executor.calls] == [
        'https://on', 'https://on'
    ]


def test_two_toggles_keep_separate_state():
    a = make_toggle(toggle_id='btn_a')
    b = make_toggle(toggle_id='btn_b')

    a.execute()  # a -> off side next
    b_result = b.execute()

    assert b_result.data['side'] == 1
    assert b.executor.calls[0]['config']['url'] == 'https://on'


def test_toggle_state_survives_a_new_action_instance():
    """Each press builds a fresh action, so the state cannot live on it."""
    make_toggle().execute()

    second = make_toggle()
    second.execute()

    assert second.executor.calls[0]['config']['url'] == 'https://off'


@pytest.mark.parametrize('config', [
    {},
    {'on_action': {'type': 'url'}},
    {'on_action': {'type': 'url'}, 'off_action': {}},
    {'on_action': 'not a dict', 'off_action': {'type': 'url'}},
])
def test_toggle_rejects_incomplete_configuration(config):
    assert ToggleAction(config).validate() is False


def test_toggle_without_an_executor_fails_cleanly():
    action = ToggleAction({
        'on_action': {'type': 'url'}, 'off_action': {'type': 'url'}
    })

    result = action.execute()

    assert result.success is False
    assert 'executor' in result.message


# --- random ------------------------------------------------------------------

def make_random(count=3, **overrides):
    config = {
        'actions': [
            {'type': 'url', 'config': {'url': f'https://{i}'}}
            for i in range(count)
        ]
    }
    config.update(overrides)
    action = RandomAction(config)
    action.executor = RecordingExecutor()
    return action


def test_random_runs_one_of_the_configured_actions():
    action = make_random()

    result = action.execute()

    assert result.success is True
    assert len(action.executor.calls) == 1
    assert action.executor.calls[0]['config']['url'].startswith('https://')


def test_random_reports_which_one_it_picked():
    action = make_random()

    result = action.execute()

    assert 0 <= result.data['chosen_index'] < 3


def test_random_avoids_repeating_the_previous_pick():
    action = make_random(count=2)

    picks = [action.execute().data['chosen_index'] for _ in range(6)]

    # With two options and avoid_repeat on, it must alternate.
    assert all(a != b for a, b in zip(picks, picks[1:]))


def test_a_single_action_still_runs_despite_avoid_repeat():
    action = make_random(count=1)

    for _ in range(3):
        assert action.execute().success is True

    assert len(action.executor.calls) == 3


def test_random_can_repeat_when_asked():
    action = make_random(count=2, avoid_repeat=False)

    picks = {action.execute().data['chosen_index'] for _ in range(20)}

    assert picks == {0, 1}


@pytest.mark.parametrize('config', [
    {},
    {'actions': []},
    {'actions': 'not a list'},
    {'actions': [{'no_type': True}]},
])
def test_random_rejects_incomplete_configuration(config):
    assert RandomAction(config).validate() is False


# --- dispatch ----------------------------------------------------------------

def test_both_are_reachable_through_the_executor():
    executor = ActionExecutor()

    toggle = executor.execute_action({
        'type': 'toggle',
        'config': {
            'toggle_id': 'e2e',
            'on_action': {'type': 'url', 'config': {'url': ''}},
            'off_action': {'type': 'url', 'config': {'url': ''}},
        },
    })
    rand = executor.execute_action({
        'type': 'random',
        'config': {'actions': [{'type': 'url', 'config': {'url': ''}}]},
    })

    # The nested url action fails on an empty URL; what matters is that the
    # composite dispatched it rather than reporting "unknown action type".
    assert 'Unknown action type' not in toggle.message
    assert 'Unknown action type' not in rand.message
