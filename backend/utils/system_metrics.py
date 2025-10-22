"""
System Metrics Utility
Collects real-time system metrics (CPU, RAM, Disk, Network, etc.)
"""
import psutil
import platform
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SystemMetrics:
    """Collect and format system metrics"""
    
    @staticmethod
    def get_cpu_metrics() -> Dict[str, Any]:
        """Get CPU usage and information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            
            per_cpu = psutil.cpu_percent(interval=1, percpu=True)
            
            return {
                'usage_percent': round(cpu_percent, 1),
                'cores_physical': cpu_count,
                'cores_logical': cpu_count_logical,
                'frequency_current': round(cpu_freq.current, 2) if cpu_freq else 0,
                'frequency_min': round(cpu_freq.min, 2) if cpu_freq else 0,
                'frequency_max': round(cpu_freq.max, 2) if cpu_freq else 0,
                'per_cpu_percent': [round(p, 1) for p in per_cpu],
                'status': 'normal' if cpu_percent < 80 else 'warning' if cpu_percent < 95 else 'critical'
            }
        except Exception as e:
            logger.error(f"Error getting CPU metrics: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_memory_metrics() -> Dict[str, Any]:
        """Get RAM usage and information"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total_gb': round(mem.total / (1024**3), 2),
                'available_gb': round(mem.available / (1024**3), 2),
                'used_gb': round(mem.used / (1024**3), 2),
                'free_gb': round(mem.free / (1024**3), 2),
                'usage_percent': round(mem.percent, 1),
                'swap_total_gb': round(swap.total / (1024**3), 2),
                'swap_used_gb': round(swap.used / (1024**3), 2),
                'swap_percent': round(swap.percent, 1),
                'status': 'normal' if mem.percent < 80 else 'warning' if mem.percent < 95 else 'critical'
            }
        except Exception as e:
            logger.error(f"Error getting memory metrics: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_disk_metrics() -> Dict[str, Any]:
        """Get disk usage for all partitions"""
        try:
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'usage_percent': round(usage.percent, 1),
                        'status': 'normal' if usage.percent < 80 else 'warning' if usage.percent < 95 else 'critical'
                    })
                except PermissionError:
                    continue
            
            # Get IO stats
            io_counters = psutil.disk_io_counters()
            
            return {
                'partitions': partitions,
                'io_read_mb': round(io_counters.read_bytes / (1024**2), 2) if io_counters else 0,
                'io_write_mb': round(io_counters.write_bytes / (1024**2), 2) if io_counters else 0,
                'io_read_count': io_counters.read_count if io_counters else 0,
                'io_write_count': io_counters.write_count if io_counters else 0
            }
        except Exception as e:
            logger.error(f"Error getting disk metrics: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_network_metrics() -> Dict[str, Any]:
        """Get network statistics"""
        try:
            net_io = psutil.net_io_counters()
            net_if_stats = psutil.net_if_stats()
            
            # Get per-interface stats
            interfaces = []
            for interface_name, stats in net_if_stats.items():
                interfaces.append({
                    'name': interface_name,
                    'is_up': stats.isup,
                    'speed_mbps': stats.speed,
                    'mtu': stats.mtu
                })
            
            return {
                'bytes_sent_mb': round(net_io.bytes_sent / (1024**2), 2),
                'bytes_recv_mb': round(net_io.bytes_recv / (1024**2), 2),
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errors_in': net_io.errin,
                'errors_out': net_io.errout,
                'drops_in': net_io.dropin,
                'drops_out': net_io.dropout,
                'interfaces': interfaces,
                'status': 'normal' if net_io.errin + net_io.errout < 100 else 'warning'
            }
        except Exception as e:
            logger.error(f"Error getting network metrics: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_temperature_metrics() -> Dict[str, Any]:
        """Get system temperature (if available)"""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                # Return empty sensors array for platforms without temperature support
                return {
                    'available': False,
                    'message': 'Temperature sensors not available',
                    'sensors': []
                }
            
            temp_data = []
            for name, entries in temps.items():
                for entry in entries:
                    temp_data.append({
                        'sensor': name,
                        'label': entry.label or 'N/A',
                        'current': round(entry.current, 1),
                        'high': round(entry.high, 1) if entry.high else None,
                        'critical': round(entry.critical, 1) if entry.critical else None
                    })
            
            return {
                'available': True,
                'sensors': temp_data
            }
        except AttributeError:
            # Temperature monitoring not supported on this platform
            return {
                'available': False,
                'message': 'Temperature monitoring not supported on this platform',
                'sensors': []
            }
        except Exception as e:
            logger.error(f"Error getting temperature metrics: {e}")
            return {
                'available': False,
                'error': str(e),
                'sensors': []
            }
    
    @staticmethod
    def get_battery_metrics() -> Dict[str, Any]:
        """Get battery information (for laptops)"""
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return {'available': False, 'message': 'No battery detected'}
            
            return {
                'available': True,
                'percent': round(battery.percent, 1),
                'is_charging': battery.power_plugged,
                'time_left_minutes': round(battery.secsleft / 60) if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
                'status': 'charging' if battery.power_plugged else 'discharging',
                'health': 'good' if battery.percent > 20 else 'low' if battery.percent > 10 else 'critical'
            }
        except Exception as e:
            logger.error(f"Error getting battery metrics: {e}")
            return {'available': False, 'error': str(e)}
    
    @staticmethod
    def get_process_metrics(limit: int = 10) -> Dict[str, Any]:
        """Get top processes by CPU and memory usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': round(proc.info['cpu_percent'] or 0, 1),
                        'memory_percent': round(proc.info['memory_percent'] or 0, 1),
                        'memory_mb': round(proc.info['memory_info'].rss / (1024**2), 2) if proc.info['memory_info'] else 0
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:limit]
            # Sort by memory usage
            top_memory = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:limit]
            
            return {
                'total_processes': len(processes),
                'top_cpu': top_cpu,
                'top_memory': top_memory
            }
        except Exception as e:
            logger.error(f"Error getting process metrics: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get general system information"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime_seconds = (datetime.now() - boot_time).total_seconds()
            
            return {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'boot_time': boot_time.isoformat(),
                'uptime_hours': round(uptime_seconds / 3600, 1),
                'python_version': platform.python_version()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_all_metrics() -> Dict[str, Any]:
        """Get all system metrics at once"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': SystemMetrics.get_cpu_metrics(),
            'memory': SystemMetrics.get_memory_metrics(),
            'disk': SystemMetrics.get_disk_metrics(),
            'network': SystemMetrics.get_network_metrics(),
            'temperature': SystemMetrics.get_temperature_metrics(),
            'battery': SystemMetrics.get_battery_metrics(),
            'processes': SystemMetrics.get_process_metrics(),
            'system_info': SystemMetrics.get_system_info()
        }
    
    @staticmethod
    def get_metric_by_type(metric_type: str) -> Dict[str, Any]:
        """Get specific metric by type"""
        metric_map = {
            'cpu': SystemMetrics.get_cpu_metrics,
            'memory': SystemMetrics.get_memory_metrics,
            'ram': SystemMetrics.get_memory_metrics,
            'disk': SystemMetrics.get_disk_metrics,
            'network': SystemMetrics.get_network_metrics,
            'temperature': SystemMetrics.get_temperature_metrics,
            'battery': SystemMetrics.get_battery_metrics,
            'processes': SystemMetrics.get_process_metrics,
            'system': SystemMetrics.get_system_info,
            'all': SystemMetrics.get_all_metrics
        }
        
        if metric_type.lower() in metric_map:
            return metric_map[metric_type.lower()]()
        else:
            return {'error': f'Unknown metric type: {metric_type}'}

