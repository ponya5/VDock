"""Tests for data models."""
import pytest
from models import Button, ButtonAction, Page, Profile, ActionType, ButtonShape


def test_button_action_creation():
    """Test ButtonAction model creation."""
    action = ButtonAction(
        type=ActionType.URL,
        config={'url': 'https://google.com'}
    )
    assert action.type == ActionType.URL
    assert action.config['url'] == 'https://google.com'


def test_button_action_to_dict():
    """Test ButtonAction serialization."""
    action = ButtonAction(
        type=ActionType.URL,
        config={'url': 'https://google.com'}
    )
    data = action.to_dict()
    assert data['type'] == 'url'
    assert data['config']['url'] == 'https://google.com'


def test_button_action_from_dict():
    """Test ButtonAction deserialization."""
    data = {
        'type': 'url',
        'config': {'url': 'https://google.com'}
    }
    action = ButtonAction.from_dict(data)
    assert action.type == ActionType.URL
    assert action.config['url'] == 'https://google.com'


def test_button_creation():
    """Test Button model creation."""
    button = Button(
        id='btn1',
        label='Test Button',
        shape=ButtonShape.ROUNDED,
        position={'row': 0, 'col': 0},
        size={'rows': 1, 'cols': 1},
        enabled=True
    )
    assert button.id == 'btn1'
    assert button.label == 'Test Button'
    assert button.shape == ButtonShape.ROUNDED


def test_button_to_dict():
    """Test Button serialization."""
    button = Button(
        id='btn1',
        label='Test',
        shape=ButtonShape.ROUNDED,
        position={'row': 0, 'col': 0},
        size={'rows': 1, 'cols': 1},
        enabled=True
    )
    data = button.to_dict()
    assert data['id'] == 'btn1'
    assert data['label'] == 'Test'
    assert data['shape'] == 'rounded'


def test_page_creation():
    """Test Page model creation."""
    page = Page(
        id='page1',
        name='Page 1',
        buttons=[],
        grid_config={'rows': 3, 'cols': 5}
    )
    assert page.id == 'page1'
    assert page.name == 'Page 1'
    assert page.grid_config['rows'] == 3


def test_profile_creation():
    """Test Profile model creation."""
    page = Page(
        id='page1',
        name='Page 1',
        buttons=[],
        grid_config={'rows': 3, 'cols': 5}
    )
    profile = Profile(
        id='profile1',
        name='Test Profile',
        description='Test',
        pages=[page],
        theme='dark'
    )
    assert profile.id == 'profile1'
    assert profile.name == 'Test Profile'
    assert len(profile.pages) == 1


def test_profile_to_dict():
    """Test Profile serialization."""
    page = Page(
        id='page1',
        name='Page 1',
        buttons=[],
        grid_config={'rows': 3, 'cols': 5}
    )
    profile = Profile(
        id='profile1',
        name='Test Profile',
        description='Test',
        pages=[page],
        theme='dark'
    )
    data = profile.to_dict()
    assert data['id'] == 'profile1'
    assert data['name'] == 'Test Profile'
    assert len(data['pages']) == 1


def test_profile_from_dict():
    """Test Profile deserialization."""
    data = {
        'id': 'profile1',
        'name': 'Test Profile',
        'description': 'Test',
        'pages': [{
            'id': 'page1',
            'name': 'Page 1',
            'buttons': [],
            'grid_config': {'rows': 3, 'cols': 5}
        }],
        'theme': 'dark'
    }
    profile = Profile.from_dict(data)
    assert profile.id == 'profile1'
    assert profile.name == 'Test Profile'
    assert len(profile.pages) == 1

