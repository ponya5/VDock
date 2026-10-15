"""DL-002: CPU usage must survive psutil.cpu_freq() failing (Apple Silicon)."""
import psutil

from utils.system_metrics import SystemMetrics


def test_cpu_metrics_survive_cpu_freq_failure(monkeypatch):
    def failing_cpu_freq():
        raise RuntimeError("'voltage-states1-sram' property not found")

    monkeypatch.setattr(psutil, 'cpu_freq', failing_cpu_freq)

    metrics = SystemMetrics.get_cpu_metrics()

    assert 'error' not in metrics
    assert metrics['frequency_current'] == 0
    assert 0 <= metrics['usage_percent'] <= 100


def test_cpu_metrics_report_frequency_when_available(monkeypatch):
    frequency = psutil._common.scpufreq(current=3200.0, min=800.0, max=4000.0)
    monkeypatch.setattr(psutil, 'cpu_freq', lambda: frequency)

    metrics = SystemMetrics.get_cpu_metrics()

    assert metrics['frequency_current'] == 3200.0
    assert metrics['frequency_max'] == 4000.0
