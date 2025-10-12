"""Tests for plugin system."""
import pytest
from plugins import PluginManager, BasePlugin, PluginInfo


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""
    
    def get_info(self):
        return PluginInfo(
            id='mock_plugin',
            name='Mock Plugin',
            version='1.0.0',
            author='Test',
            description='Test plugin',
            actions=['test_action']
        )
    
    def initialize(self):
        return True
    
    def cleanup(self):
        pass
    
    def execute_action(self, action_id, config):
        if action_id == 'test_action':
            return {'success': True, 'message': 'Action executed'}
        return {'success': False, 'message': 'Unknown action'}
    
    def get_action_schema(self, action_id):
        return {
            'type': 'object',
            'properties': {}
        }


def test_plugin_info():
    """Test PluginInfo creation."""
    info = PluginInfo(
        id='test',
        name='Test Plugin',
        version='1.0.0',
        author='Author',
        description='Description',
        actions=['action1']
    )
    assert info.id == 'test'
    assert info.name == 'Test Plugin'


def test_plugin_manager_init():
    """Test PluginManager initialization."""
    manager = PluginManager()
    assert len(manager.plugins) == 0


def test_mock_plugin():
    """Test mock plugin functionality."""
    plugin = MockPlugin()
    
    # Test initialization
    assert plugin.initialize() is True
    
    # Test info
    info = plugin.get_info()
    assert info.id == 'mock_plugin'
    
    # Test action execution
    result = plugin.execute_action('test_action', {})
    assert result['success'] is True
    
    # Test unknown action
    result = plugin.execute_action('unknown', {})
    assert result['success'] is False


def test_plugin_enable_disable():
    """Test plugin enable/disable."""
    plugin = MockPlugin()
    assert plugin.enabled is False
    
    plugin.enable()
    assert plugin.enabled is True
    
    plugin.disable()
    assert plugin.enabled is False

