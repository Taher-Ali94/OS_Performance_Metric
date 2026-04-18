"""Service wrapper that aggregates scanner metrics."""

from __future__ import annotations

from typing import Any, Dict

from scanner.config import Settings
from scanner.metrics_collector import (
    get_cpu_metrics,
    get_disk_metrics,
    get_gpu_metrics,
    get_hardware_info,
    get_memory_metrics,
    get_network_metrics,
    get_os_info,
    get_system_uptime,
    get_top_processes,
)


class SystemScannerService:
    """High-level service that provides modular and full metric snapshots."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def cpu(self) -> Dict[str, Any]:
        return get_cpu_metrics()

    def memory(self) -> Dict[str, Any]:
        return get_memory_metrics()

    def disk(self) -> Dict[str, Any]:
        return get_disk_metrics()

    def network(self) -> Dict[str, Any]:
        return get_network_metrics()

    def processes(self) -> Dict[str, Any]:
        return {"top_processes": get_top_processes(limit=self.settings.top_process_count)}

    def metrics(self) -> Dict[str, Any]:
        return {
            "cpu": self.cpu(),
            "memory": self.memory(),
            "disk": self.disk(),
            "network": self.network(),
            "uptime": get_system_uptime(),
            "processes": self.processes()["top_processes"],
            "gpu": get_gpu_metrics(),
            "os": get_os_info(),
            "hardware": get_hardware_info(),
        }
