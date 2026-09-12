"""Plugin management system."""
import importlib
import importlib.util
import logging
import pkgutil
import sys
from pathlib import Path
from dataclasses import replace
from typing import Dict, List, Optional, Any
from .base_plugin import BasePlugin, PluginInfo
from config import Config

logger = logging.getLogger('vdock')


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
                logger.error("Error loading plugin %s: %s", plugin_file.name, e)
        
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
                logger.warning("Plugin file %s has no Plugin class", plugin_file.name)
                return None
            
            # Instantiate plugin
            plugin_class = getattr(module, 'Plugin')
            plugin = plugin_class()
            
            if not isinstance(plugin, BasePlugin):
                logger.warning("Plugin class in %s does not inherit from BasePlugin",
                               plugin_file.name)
                return None
            
            # Initialize plugin
            if not plugin.initialize():
                logger.warning("Plugin %s failed to initialize", plugin_file.name)
                return None
            
            # Register plugin
            info = plugin.get_info()
            self.plugins[info.id] = plugin
            
            # Register plugin actions
            for action_id in info.actions:
                self.plugin_actions[action_id] = info.id
            
            plugin.enable()
            logger.info("Loaded plugin: %s v%s", info.name, info.version)
            return info.id
        except Exception as e:
            logger.error("Error loading plugin from %s: %s", plugin_file, e)
            return None
    
    def load_builtin_packs(self) -> List[str]:
        """Load the integration packs shipped inside ``backend/integrations``.

        ``load_plugins()`` only scans ``Config.PLUGINS_DIR`` (the user drop-in
        folder), so packs that ship with VDock were never discovered. Each
        module in the package exposing a ``Plugin`` class is registered exactly
        like a drop-in plugin.
        """
        if not Config.ENABLE_PLUGINS:
            return []

        loaded: List[str] = []
        try:
            import integrations
        except ImportError:
            return loaded

        for module_info in pkgutil.iter_modules(integrations.__path__):
            if module_info.name.startswith('_'):
                continue
            try:
                module = importlib.import_module(
                    f'integrations.{module_info.name}'
                )
                plugin_id = self._register_module(module, module_info.name)
                if plugin_id:
                    loaded.append(plugin_id)
            except Exception as e:
                logger.error(
                    "Error loading integration pack %s: %s", module_info.name, e
                )

        return loaded

    def _register_module(self, module: Any, source: str) -> Optional[str]:
        """Instantiate and register the ``Plugin`` class in a loaded module."""
        if not hasattr(module, 'Plugin'):
            logger.warning("Plugin module %s has no Plugin class", source)
            return None

        plugin = module.Plugin()
        if not isinstance(plugin, BasePlugin):
            logger.warning(
                "Plugin class in %s does not inherit from BasePlugin", source
            )
            return None

        if not plugin.initialize():
            logger.warning("Plugin %s failed to initialize", source)
            return None

        info = plugin.get_info()
        self.plugins[info.id] = plugin
        for action_id in info.actions:
            self.plugin_actions[action_id] = info.id

        plugin.enable()
        available, reason = plugin.is_available()
        if available:
            logger.info("Loaded plugin: %s v%s", info.name, info.version)
        else:
            logger.info(
                "Loaded plugin: %s v%s (unavailable: %s)",
                info.name, info.version, reason
            )
        return info.id

    def get_action_specs(self) -> List[Any]:
        """Collect catalog entries for every action every plugin provides.

        A pack that implements ``get_action_specs()`` describes itself fully.
        Anything else is derived from its PluginInfo and JSON schema so that
        third-party plugins still show up in the picker.
        """
        from actions.catalog import ActionSpec, ConfigField

        specs: List[Any] = []
        for plugin in self.plugins.values():
            info = plugin.get_info()
            available, reason = plugin.is_available()

            declared = plugin.get_action_specs()
            if declared is not None:
                for spec in declared:
                    if not available and not spec.unavailable_reason:
                        spec = replace(spec, unavailable_reason=reason)
                    specs.append(spec)
                continue

            for action_id in info.actions:
                schema = {}
                try:
                    schema = plugin.get_action_schema(action_id) or {}
                except Exception as e:
                    logger.error(
                        "Plugin %s failed to describe %s: %s",
                        info.id, action_id, e
                    )

                specs.append(ActionSpec(
                    id=action_id,
                    label=_humanise(action_id),
                    category='custom',
                    icon=('fas', 'puzzle-piece'),
                    action_type=action_id,
                    description=info.description,
                    config_fields=_fields_from_schema(schema),
                    keywords=(info.name.lower(),),
                    unavailable_reason=None if available else reason,
                ))

        return specs

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
    
    def handles(self, action_id: str) -> bool:
        """True when some loaded plugin provides ``action_id``."""
        return action_id in self.plugin_actions

    def cleanup(self):
        """Clean up all plugins."""
        for plugin in self.plugins.values():
            try:
                plugin.cleanup()
            except Exception as e:
                logger.error("Error cleaning up plugin: %s", e)


def _humanise(action_id: str) -> str:
    """'obs_start_recording' -> 'Obs Start Recording'."""
    return action_id.replace('_', ' ').title()


def _fields_from_schema(schema: Dict[str, Any]) -> tuple:
    """Convert a JSON-schema object into catalog ConfigFields."""
    from actions.catalog import ConfigField

    properties = (schema or {}).get('properties') or {}
    required = set((schema or {}).get('required') or ())

    type_map = {
        'string': 'text',
        'number': 'number',
        'integer': 'number',
        'boolean': 'boolean',
    }

    fields = []
    for name, prop in properties.items():
        prop = prop or {}
        fields.append(ConfigField(
            name=name,
            label=prop.get('title') or _humanise(name),
            type='select' if prop.get('enum') else type_map.get(
                prop.get('type'), 'text'
            ),
            required=name in required,
            default=prop.get('default'),
            options=tuple(
                {'value': v, 'label': str(v)} for v in prop.get('enum', ())
            ),
            help=prop.get('description', ''),
        ))
    return tuple(fields)
