"""Metric action for displaying system metrics on buttons."""
from typing import Dict, Any
from .base_action import BaseAction, ActionResult
from utils.system_metrics import SystemMetrics


class MetricAction(BaseAction):
    """Action for fetching and displaying system metrics."""

    VALID_METRICS = [
        'cpu_usage', 'memory', 'disk', 'network', 'temperature', 
        'battery', 'processes', 'system_info', 'all'
    ]

    def __init__(self, config: Dict[str, Any]):
        """Initialize metric action."""
        super().__init__(config)

    def validate(self) -> bool:
        """Validate that metric type is provided and valid."""
        metric_type = self.config.get('metric_type')
        if not metric_type:
            return False
        
        # Extract base metric type (remove prefixes like 'metric_')
        base_type = metric_type.replace('metric_', '')
        return base_type in self.VALID_METRICS

    def execute(self) -> ActionResult:
        """Execute the metric fetch action."""
        if not self.validate():
            return ActionResult(
                False,
                'Invalid configuration: Valid metric type required'
            )

        metric_type = self.config.get('metric_type')
        refresh_interval = self.config.get('refresh_interval', 2)
        
        # Extract base metric type (remove prefixes like 'metric_')
        base_type = metric_type.replace('metric_', '')
        
        try:
            if base_type == 'cpu_usage':
                data = SystemMetrics.get_cpu_metrics()
                if 'error' in data:
                    return ActionResult(False, f'CPU metrics error: {data["error"]}')
                
                return ActionResult(
                    True,
                    f'CPU: {data.get("usage_percent", 0)}%',
                    {
                        'metric_type': 'cpu',
                        'value': data.get('usage_percent', 0),
                        'unit': '%',
                        'status': data.get('status', 'normal'),
                        'details': data,
                        'refresh_interval': refresh_interval
                    }
                )
            
            elif base_type == 'memory':
                data = SystemMetrics.get_memory_metrics()
                if 'error' in data:
                    return ActionResult(False, f'Memory metrics error: {data["error"]}')
                
                return ActionResult(
                    True,
                    f'RAM: {data.get("usage_percent", 0)}%',
                    {
                        'metric_type': 'memory',
                        'value': data.get('usage_percent', 0),
                        'unit': '%',
                        'status': data.get('status', 'normal'),
                        'details': data,
                        'refresh_interval': refresh_interval
                    }
                )
            
            elif base_type == 'disk':
                data = SystemMetrics.get_disk_metrics()
                if 'error' in data:
                    return ActionResult(False, f'Disk metrics error: {data["error"]}')
                
                # Get primary partition usage
                primary_usage = 0
                if data.get('partitions'):
                    primary_usage = data['partitions'][0].get('usage_percent', 0)
                
                return ActionResult(
                    True,
                    f'Disk: {primary_usage}%',
                    {
                        'metric_type': 'disk',
                        'value': primary_usage,
                        'unit': '%',
                        'status': 'normal' if primary_usage < 80 else 'warning' if primary_usage < 95 else 'critical',
                        'details': data,
                        'refresh_interval': refresh_interval
                    }
                )
            
            elif base_type == 'network':
                data = SystemMetrics.get_network_metrics()
                if 'error' in data:
                    return ActionResult(False, f'Network metrics error: {data["error"]}')
                
                return ActionResult(
                    True,
                    f'Net: {data.get("bytes_recv_mb", 0):.1f}MB',
                    {
                        'metric_type': 'network',
                        'value': data.get('bytes_recv_mb', 0),
                        'unit': 'MB',
                        'status': data.get('status', 'normal'),
                        'details': data,
                        'refresh_interval': refresh_interval
                    }
                )
            
            elif base_type == 'temperature':
                data = SystemMetrics.get_temperature_metrics()
                if not data.get('available', False):
                    return ActionResult(False, 'Temperature sensors not available')
                
                avg_temp = 0
                if data.get('sensors'):
                    temps = [s['current'] for s in data['sensors']]
                    avg_temp = sum(temps) / len(temps)
                
                return ActionResult(
                    True,
                    f'Temp: {avg_temp:.1f}°C',
                    {
                        'metric_type': 'temperature',
                        'value': avg_temp,
                        'unit': '°C',
                        'status': 'normal' if avg_temp < 70 else 'warning' if avg_temp < 85 else 'critical',
                        'details': data,
                        'refresh_interval': refresh_interval
                    }
                )
            
            elif base_type == 'battery':
                data = SystemMetrics.get_battery_metrics()
                if not data.get('available', False):
                    return ActionResult(False, 'Battery not available')
                
                return ActionResult(
                    True,
                    f'Battery: {data.get("percent", 0)}%',
                    {
                        'metric_type': 'battery',
                        'value': data.get('percent', 0),
                        'unit': '%',
                        'status': data.get('health', 'good'),
                        'details': data,
                        'refresh_interval': refresh_interval
                    }
                )
            
            else:
                return ActionResult(False, f'Unknown metric type: {base_type}')
                
        except Exception as e:
            return ActionResult(False, f'Error fetching {base_type} metrics: {str(e)}')

    def get_description(self) -> str:
        """Get action description."""
        metric_type = self.config.get('metric_type', 'unknown')
        return f"Metric: {metric_type.replace('_', ' ').title()}"
