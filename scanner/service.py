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
        memory = self.memory()
        disk = self.disk()
        uptime_raw = get_system_uptime()
        uptime_seconds = int(uptime_raw.get("uptime_seconds", 0))
        days, remaining_after_days = divmod(uptime_seconds, 86_400)
        hours, remaining_after_hours = divmod(remaining_after_days, 3_600)
        minutes, seconds = divmod(remaining_after_hours, 60)

        os_info = get_os_info()
        hardware_info = get_hardware_info()
        disk_io = disk.get("io", {}).copy()
        disk_io.setdefault("read_time", 0)
        disk_io.setdefault("write_time", 0)
        disk["io"] = disk_io

        os_info.setdefault("node", os_info.get("hostname", "unknown"))
        os_info.setdefault("machine", os_info.get("architecture", "unknown"))
        os_info.setdefault("processor", hardware_info.get("cpu_model", "unknown"))

        hardware_info.setdefault("total_memory", memory.get("total", 0))

        uptime = {
            **uptime_raw,
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "total_seconds": uptime_seconds,
        }

        return {
            "cpu": self.cpu(),
            "memory": memory,
            "disk": disk,
            "network": self.network(),
            "uptime": uptime,
            "processes": self.processes()["top_processes"],
            "gpu": get_gpu_metrics(),
            "os": os_info,
            "hardware": hardware_info,
        }
