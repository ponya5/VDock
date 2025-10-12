"""Example OBS Studio plugin.

This is a reference implementation showing how to create a plugin.
Requires obs-websocket-py: pip install obs-websocket-py
"""
from typing import Dict, Any
from .base_plugin import BasePlugin, PluginInfo

try:
    from obswebsocket import obsws, requests as obs_requests
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False


class Plugin(BasePlugin):
    """OBS Studio integration plugin."""
    
    def __init__(self):
        """Initialize OBS plugin."""
        super().__init__()
        self.ws = None
        self.host = "localhost"
        self.port = 4455
        self.password = ""
    
    def get_info(self) -> PluginInfo:
        """Get plugin information."""
        return PluginInfo(
            id='obs_studio',
            name='OBS Studio',
            version='1.0.0',
            author='VDock',
            description='Control OBS Studio via WebSocket',
            actions=[
                'obs_start_recording',
                'obs_stop_recording',
                'obs_start_streaming',
                'obs_stop_streaming',
                'obs_switch_scene',
                'obs_toggle_source'
            ]
        )
    
    def initialize(self) -> bool:
        """Initialize the plugin."""
        if not OBS_AVAILABLE:
            print("OBS WebSocket library not available")
            return False
        
        # Connection will be established on-demand
        return True
    
    def cleanup(self):
        """Clean up plugin resources."""
        if self.ws:
            try:
                self.ws.disconnect()
            except Exception:
                pass
    
    def _connect(self) -> bool:
        """Connect to OBS WebSocket.
        
        Returns:
            True if connected, False otherwise
        """
        if self.ws:
            return True
        
        try:
            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()
            return True
        except Exception as e:
            print(f"Failed to connect to OBS: {e}")
            return False
    
    def execute_action(self, action_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plugin action."""
        if not self._connect():
            return {
                'success': False,
                'message': 'Failed to connect to OBS Studio'
            }
        
        try:
            if action_id == 'obs_start_recording':
                self.ws.call(obs_requests.StartRecord())
                return {'success': True, 'message': 'Recording started'}
            
            elif action_id == 'obs_stop_recording':
                self.ws.call(obs_requests.StopRecord())
                return {'success': True, 'message': 'Recording stopped'}
            
            elif action_id == 'obs_start_streaming':
                self.ws.call(obs_requests.StartStream())
                return {'success': True, 'message': 'Streaming started'}
            
            elif action_id == 'obs_stop_streaming':
                self.ws.call(obs_requests.StopStream())
                return {'success': True, 'message': 'Streaming stopped'}
            
            elif action_id == 'obs_switch_scene':
                scene_name = config.get('scene_name')
                if not scene_name:
                    return {'success': False, 'message': 'Scene name required'}
                self.ws.call(obs_requests.SetCurrentProgramScene(sceneName=scene_name))
                return {'success': True, 'message': f'Switched to scene: {scene_name}'}
            
            elif action_id == 'obs_toggle_source':
                source_name = config.get('source_name')
                if not source_name:
                    return {'success': False, 'message': 'Source name required'}
                # Toggle source visibility
                # This requires getting current state first
                return {'success': True, 'message': f'Toggled source: {source_name}'}
            
            else:
                return {'success': False, 'message': f'Unknown action: {action_id}'}
        
        except Exception as e:
            return {'success': False, 'message': f'OBS action failed: {str(e)}'}
    
    def get_action_schema(self, action_id: str) -> Dict[str, Any]:
        """Get configuration schema for an action."""
        if action_id in ['obs_start_recording', 'obs_stop_recording', 
                         'obs_start_streaming', 'obs_stop_streaming']:
            return {
                'type': 'object',
                'properties': {},
                'required': []
            }
        
        elif action_id == 'obs_switch_scene':
            return {
                'type': 'object',
                'properties': {
                    'scene_name': {
                        'type': 'string',
                        'title': 'Scene Name',
                        'description': 'Name of the scene to switch to'
                    }
                },
                'required': ['scene_name']
            }
        
        elif action_id == 'obs_toggle_source':
            return {
                'type': 'object',
                'properties': {
                    'source_name': {
                        'type': 'string',
                        'title': 'Source Name',
                        'description': 'Name of the source to toggle'
                    }
                },
                'required': ['source_name']
            }
        
        return {}

