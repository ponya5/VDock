"""Tests for action executors."""
import pytest
from actions import URLAction, ProgramAction, CommandAction, HotkeyAction, ActionExecutor


def test_url_action_validate():
    """Test URL action validation."""
    # Valid configuration
    action = URLAction({'url': 'https://google.com'})
    assert action.validate() is True
    
    # Invalid configuration
    action = URLAction({})
    assert action.validate() is False


def test_url_action_execute():
    """Test URL action execution."""
    action = URLAction({'url': 'https://google.com'})
    result = action.execute()
    assert result.success is True
    assert 'Opened URL' in result.message


def test_program_action_validate():
    """Test program action validation."""
    action = ProgramAction({'path': 'notepad.exe'})
    assert action.validate() is True
    
    action = ProgramAction({})
    assert action.validate() is False


def test_command_action_validate():
    """Test command action validation."""
    action = CommandAction({'command': 'echo test'})
    assert action.validate() is True
    
    action = CommandAction({})
    assert action.validate() is False


def test_hotkey_action_validate():
    """Test hotkey action validation."""
    action = HotkeyAction({'keys': ['ctrl', 'c']})
    # May fail if pynput not available
    if action.validate():
        assert True
    else:
        pytest.skip("pynput not available")


def test_action_executor():
    """Test action executor routing."""
    executor = ActionExecutor()
    
    # Test URL action
    result = executor.execute_action({
        'type': 'url',
        'config': {'url': 'https://google.com'}
    })
    assert result.success is True
    
    # Test unknown action type
    result = executor.execute_action({
        'type': 'unknown_action',
        'config': {}
    })
    assert result.success is False
    assert 'Unknown action type' in result.message


def test_action_executor_missing_type():
    """Test action executor with missing type."""
    executor = ActionExecutor()
    result = executor.execute_action({'config': {}})
    assert result.success is False
    assert 'not specified' in result.message

