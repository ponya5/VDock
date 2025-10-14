"""
Macro Action Handler
Executes a sequence of actions with delays
"""
import time
import logging
from typing import List, Dict, Any
from .base_action import BaseAction
from .hotkey_action import HotkeyAction
from .command_action import CommandAction

logger = logging.getLogger(__name__)


class MacroAction(BaseAction):
    """
    Execute a macro (sequence of actions) with timing control
    """
    
    def __init__(self):
        super().__init__()
        self.hotkey_action = HotkeyAction()
        self.command_action = CommandAction()
    
    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute macro steps in sequence
        
        Config format:
        {
            "steps": [
                {"type": "hotkey", "keys": ["ctrl", "c"]},
                {"type": "delay", "delay": 500},
                {"type": "hotkey", "keys": ["ctrl", "v"]},
                {"type": "text", "text": "Hello World"},
                {"type": "delay", "delay": 1000}
            ]
        }
        """
        try:
            steps = config.get('steps', [])
            if not steps:
                return {
                    'success': False,
                    'message': 'No macro steps defined'
                }
            
            results = []
            for i, step in enumerate(steps):
                step_type = step.get('type')
                
                try:
                    if step_type == 'hotkey':
                        result = self._execute_hotkey(step)
                    elif step_type == 'delay':
                        result = self._execute_delay(step)
                    elif step_type == 'text':
                        result = self._execute_text(step)
                    elif step_type == 'click':
                        result = self._execute_click(step)
                    else:
                        result = {
                            'success': False,
                            'message': f'Unknown step type: {step_type}'
                        }
                    
                    results.append({
                        'step': i + 1,
                        'type': step_type,
                        'result': result
                    })
                    
                    # If any step fails, log it but continue
                    if not result.get('success'):
                        logger.warning(f"Macro step {i + 1} failed: {result.get('message')}")
                    
                except Exception as e:
                    logger.error(f"Error executing macro step {i + 1}: {e}")
                    results.append({
                        'step': i + 1,
                        'type': step_type,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'message': f'Macro executed with {len(results)} steps',
                'steps_executed': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Macro execution error: {e}")
            return {
                'success': False,
                'message': f'Macro execution failed: {str(e)}'
            }
    
    def _execute_hotkey(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a hotkey step"""
        keys = step.get('keys', [])
        if not keys:
            return {'success': False, 'message': 'No keys specified'}
        
        # Convert keys list to combo string for HotkeyAction
        combo = '+'.join(keys)
        return self.hotkey_action.execute({'combo': combo})
    
    def _execute_delay(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a delay step"""
        delay_ms = step.get('delay', 100)
        time.sleep(delay_ms / 1000.0)  # Convert ms to seconds
        return {
            'success': True,
            'message': f'Delayed {delay_ms}ms'
        }
    
    def _execute_text(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a text typing step"""
        text = step.get('text', '')
        if not text:
            return {'success': False, 'message': 'No text specified'}
        
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=0.05)
            return {
                'success': True,
                'message': f'Typed text: {text[:50]}...' if len(text) > 50 else f'Typed text: {text}'
            }
        except Exception as e:
            logger.error(f"Text typing error: {e}")
            return {
                'success': False,
                'message': f'Text typing failed: {str(e)}'
            }
    
    def _execute_click(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a mouse click step"""
        position = step.get('position', {})
        x = position.get('x')
        y = position.get('y')
        
        try:
            import pyautogui
            if x is not None and y is not None:
                pyautogui.click(x, y)
                return {
                    'success': True,
                    'message': f'Clicked at ({x}, {y})'
                }
            else:
                pyautogui.click()
                return {
                    'success': True,
                    'message': 'Clicked at current position'
                }
        except Exception as e:
            logger.error(f"Click error: {e}")
            return {
                'success': False,
                'message': f'Click failed: {str(e)}'
            }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate macro configuration"""
        if 'steps' not in config:
            return False
        
        steps = config['steps']
        if not isinstance(steps, list) or len(steps) == 0:
            return False
        
        valid_step_types = ['hotkey', 'delay', 'text', 'click']
        for step in steps:
            if 'type' not in step:
                return False
            if step['type'] not in valid_step_types:
                return False
        
        return True

