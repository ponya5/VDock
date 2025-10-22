"""OBS Studio action handler using obs-websocket-py."""
from typing import Dict, Any
from .base_action import BaseAction, ActionResult

try:
    from obswebsocket import obsws, requests as obs_requests
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False


class OBSAction(BaseAction):
    """OBS Studio integration via WebSocket."""
    
    # Shared connection instance
    _ws_connection = None
    _connection_config = {
        'host': 'localhost',
        'port': 4455,
        'password': ''
    }
    
    VALID_ACTIONS = [
        'obs_start_recording',
        'obs_stop_recording',
        'obs_start_streaming',
        'obs_stop_streaming',
        'obs_switch_scene',
        'obs_toggle_source',
        'obs_toggle_filter'
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OBS action."""
        super().__init__(config)
        
    def validate(self) -> bool:
        """Validate that OBS is available and action is valid."""
        if not OBS_AVAILABLE:
            return False
        
        action = self.config.get('action')
        return action in self.VALID_ACTIONS
    
    def execute(self) -> ActionResult:
        """Execute the OBS action."""
        if not OBS_AVAILABLE:
            return ActionResult(
                False,
                'OBS WebSocket library not installed. '
                'Install with: pip install obs-websocket-py'
            )
        
        if not self.validate():
            return ActionResult(
                False,
                'Invalid OBS action configuration'
            )
        
        action = self.config['action']
        
        # Connect to OBS
        if not self._connect():
            return ActionResult(
                False,
                'Failed to connect to OBS Studio. '
                'Make sure OBS is running and WebSocket server is enabled.'
            )
        
        try:
            if action == 'obs_start_recording':
                return self._start_recording()
            elif action == 'obs_stop_recording':
                return self._stop_recording()
            elif action == 'obs_start_streaming':
                return self._start_streaming()
            elif action == 'obs_stop_streaming':
                return self._stop_streaming()
            elif action == 'obs_switch_scene':
                return self._switch_scene()
            elif action == 'obs_toggle_source':
                return self._toggle_source()
            elif action == 'obs_toggle_filter':
                return self._toggle_filter()
            else:
                return ActionResult(False, f'Unknown OBS action: {action}')
        except Exception as e:
            return ActionResult(False, f'OBS action failed: {str(e)}')
    
    def _connect(self) -> bool:
        """Connect to OBS WebSocket server."""
        if OBSAction._ws_connection:
            try:
                # Test if connection is still alive
                OBSAction._ws_connection.call(obs_requests.GetVersion())
                return True
            except Exception:
                # Connection is dead, reconnect
                OBSAction._ws_connection = None
        
        try:
            config = OBSAction._connection_config
            OBSAction._ws_connection = obsws(
                config['host'],
                config['port'],
                config['password']
            )
            OBSAction._ws_connection.connect()
            return True
        except Exception as e:
            print(f"Failed to connect to OBS: {e}")
            return False
    
    def _start_recording(self) -> ActionResult:
        """Start recording in OBS."""
        try:
            OBSAction._ws_connection.call(obs_requests.StartRecord())
            return ActionResult(True, 'Recording started')
        except Exception as e:
            # Check if already recording
            if 'already recording' in str(e).lower():
                return ActionResult(True, 'Recording already in progress')
            return ActionResult(False, f'Failed to start recording: {str(e)}')
    
    def _stop_recording(self) -> ActionResult:
        """Stop recording in OBS."""
        try:
            OBSAction._ws_connection.call(obs_requests.StopRecord())
            return ActionResult(True, 'Recording stopped')
        except Exception as e:
            # Check if not recording
            if 'not recording' in str(e).lower():
                return ActionResult(True, 'Recording already stopped')
            return ActionResult(False, f'Failed to stop recording: {str(e)}')
    
    def _start_streaming(self) -> ActionResult:
        """Start streaming in OBS."""
        try:
            OBSAction._ws_connection.call(obs_requests.StartStream())
            return ActionResult(True, 'Streaming started')
        except Exception as e:
            # Check if already streaming
            if 'already streaming' in str(e).lower():
                return ActionResult(True, 'Streaming already in progress')
            return ActionResult(False, f'Failed to start streaming: {str(e)}')
    
    def _stop_streaming(self) -> ActionResult:
        """Stop streaming in OBS."""
        try:
            OBSAction._ws_connection.call(obs_requests.StopStream())
            return ActionResult(True, 'Streaming stopped')
        except Exception as e:
            # Check if not streaming
            if 'not streaming' in str(e).lower():
                return ActionResult(True, 'Streaming already stopped')
            return ActionResult(False, f'Failed to stop streaming: {str(e)}')
    
    def _switch_scene(self) -> ActionResult:
        """Switch to a different scene."""
        scene_name = self.config.get('scene_name')
        if not scene_name:
            return ActionResult(False, 'Scene name is required')
        
        try:
            OBSAction._ws_connection.call(
                obs_requests.SetCurrentProgramScene(sceneName=scene_name)
            )
            return ActionResult(True, f'Switched to scene: {scene_name}')
        except Exception as e:
            return ActionResult(
                False,
                f'Failed to switch scene: {str(e)}'
            )
    
    def _toggle_source(self) -> ActionResult:
        """Toggle source visibility."""
        source_name = self.config.get('source_name')
        scene_name = self.config.get('scene_name')
        
        if not source_name:
            return ActionResult(False, 'Source name is required')
        
        try:
            # Get current scene if not specified
            if not scene_name:
                response = OBSAction._ws_connection.call(
                    obs_requests.GetCurrentProgramScene()
                )
                scene_name = response.datain.get('currentProgramSceneName')
            
            # Get current visibility
            response = OBSAction._ws_connection.call(
                obs_requests.GetSceneItemEnabled(
                    sceneName=scene_name,
                    sceneItemId=source_name
                )
            )
            current_enabled = response.datain.get('sceneItemEnabled', False)
            
            # Toggle visibility
            OBSAction._ws_connection.call(
                obs_requests.SetSceneItemEnabled(
                    sceneName=scene_name,
                    sceneItemId=source_name,
                    sceneItemEnabled=not current_enabled
                )
            )
            
            status = 'shown' if not current_enabled else 'hidden'
            return ActionResult(True, f'Source {source_name} {status}')
        except Exception as e:
            return ActionResult(
                False,
                f'Failed to toggle source: {str(e)}'
            )
    
    def _toggle_filter(self) -> ActionResult:
        """Toggle filter on/off."""
        source_name = self.config.get('source_name')
        filter_name = self.config.get('filter_name')
        
        if not source_name or not filter_name:
            return ActionResult(
                False,
                'Source name and filter name are required'
            )
        
        try:
            # Get current filter state
            response = OBSAction._ws_connection.call(
                obs_requests.GetSourceFilterEnabled(
                    sourceName=source_name,
                    filterName=filter_name
                )
            )
            current_enabled = response.datain.get('filterEnabled', False)
            
            # Toggle filter
            OBSAction._ws_connection.call(
                obs_requests.SetSourceFilterEnabled(
                    sourceName=source_name,
                    filterName=filter_name,
                    filterEnabled=not current_enabled
                )
            )
            
            status = 'enabled' if not current_enabled else 'disabled'
            return ActionResult(
                True,
                f'Filter {filter_name} {status}'
            )
        except Exception as e:
            return ActionResult(
                False,
                f'Failed to toggle filter: {str(e)}'
            )
    
    def get_description(self) -> str:
        """Get action description."""
        action = self.config.get('action', 'unknown')
        return f"OBS: {action.replace('obs_', '').replace('_', ' ').title()}"
    
    @classmethod
    def disconnect(cls):
        """Disconnect from OBS WebSocket."""
        if cls._ws_connection:
            try:
                cls._ws_connection.disconnect()
            except Exception:
                pass
            cls._ws_connection = None

