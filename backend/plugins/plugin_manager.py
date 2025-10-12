"""Plugin management system."""
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from .base_plugin import BasePlugin, PluginInfo
from config import Config


class PluginManager:
    """Manages plugin loading and execution."""
    
    def __init__(self):
        """Initialize plugin manager."""
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_actions: Dict[str, str] = {}  # Maps action_id to plugin_id
    
    def load_plugins(self) -> List[str]:
        """Load all plugins from the plugins directory.
        
        Returns:
            List of successfully loaded plugin IDs
        """
        if not Config.ENABLE_PLUGINS:
            return []
        
        loaded = []
        plugins_dir = Config.PLUGINS_DIR
        
        if not plugins_dir.exists():
            return loaded
        
        # Look for Python files in plugins directory
        for plugin_file in plugins_dir.glob('*.py'):
            if plugin_file.name.startswith('_'):
                continue
            
            try:
                plugin_id = self._load_plugin_file(plugin_file)
                if plugin_id:
                    loaded.append(plugin_id)
            except Exception as e:
                print(f"Error loading plugin {plugin_file.name}: {e}")
        
        return loaded
    
    def _load_plugin_file(self, plugin_file: Path) -> Optional[str]:
        """Load a single plugin file.
        
        Args:
            plugin_file: Path to the plugin file
            
        Returns:
            Plugin ID if successful, None otherwise
        """
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(
                f"vdock.plugins.{plugin_file.stem}",
                plugin_file
            )
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Find plugin class (should be named Plugin)
            if not hasattr(module, 'Plugin'):
                print(f"Plugin file {plugin_file.name} does not have a Plugin class")
                return None
            
            # Instantiate plugin
            plugin_class = getattr(module, 'Plugin')
            plugin = plugin_class()
            
            if not isinstance(plugin, BasePlugin):
                print(f"Plugin class in {plugin_file.name} does not inherit from BasePlugin")
                return None
            
            # Initialize plugin
            if not plugin.initialize():
                print(f"Plugin {plugin_file.name} failed to initialize")
                return None
            
            # Register plugin
            info = plugin.get_info()
            self.plugins[info.id] = plugin
            
            # Register plugin actions
            for action_id in info.actions:
                self.plugin_actions[action_id] = info.id
            
            plugin.enable()
            print(f"Loaded plugin: {info.name} v{info.version}")
            return info.id
        except Exception as e:
            print(f"Error loading plugin from {plugin_file}: {e}")
            return None
    
    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """Get a plugin by ID.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Plugin instance or None
        """
        return self.plugins.get(plugin_id)
    
    def get_all_plugins(self) -> List[PluginInfo]:
        """Get information about all loaded plugins.
        
        Returns:
            List of PluginInfo objects
        """
        return [plugin.get_info() for plugin in self.plugins.values()]
    
    def execute_plugin_action(self, action_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plugin action.
        
        Args:
            action_id: Action ID
            config: Action configuration
            
        Returns:
            Result dictionary
        """
        if action_id not in self.plugin_actions:
            return {
                'success': False,
                'message': f'Unknown plugin action: {action_id}'
            }
        
        plugin_id = self.plugin_actions[action_id]
        plugin = self.plugins.get(plugin_id)
        
        if not plugin:
            return {
                'success': False,
                'message': f'Plugin not found: {plugin_id}'
            }
        
        if not plugin.enabled:
            return {
                'success': False,
                'message': f'Plugin is disabled: {plugin_id}'
            }
        
        try:
            return plugin.execute_action(action_id, config)
        except Exception as e:
            return {
                'success': False,
                'message': f'Plugin action error: {str(e)}'
            }
    
    def get_action_schema(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration schema for a plugin action.
        
        Args:
            action_id: Action ID
            
        Returns:
            JSON schema or None
        """
        if action_id not in self.plugin_actions:
            return None
        
        plugin_id = self.plugin_actions[action_id]
        plugin = self.plugins.get(plugin_id)
        
        if not plugin:
            return None
        
        try:
            return plugin.get_action_schema(action_id)
        except Exception:
            return None
    
    def cleanup(self):
        """Clean up all plugins."""
        for plugin in self.plugins.values():
            try:
                plugin.cleanup()
            except Exception as e:
                print(f"Error cleaning up plugin: {e}")

