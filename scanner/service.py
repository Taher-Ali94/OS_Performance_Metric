"""Service wrapper that aggregates scanner metrics."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Callable, Dict

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

_SECONDS_PER_DAY = 86_400
_SECONDS_PER_HOUR = 3_600
_COLLECTOR_TIMEOUT_SECONDS = 3.0

logger = logging.getLogger(__name__)


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

    @staticmethod
    def _run_with_timeout(
        fn: Callable[[], Dict[str, Any] | list[Dict[str, Any]]],
        fallback: Dict[str, Any] | list[Dict[str, Any]],
        component: str,
        timeout_seconds: float = _COLLECTOR_TIMEOUT_SECONDS,
    ) -> Dict[str, Any] | list[Dict[str, Any]]:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn)
            try:
                return future.result(timeout=timeout_seconds)
            except FutureTimeoutError:
                logger.warning(
                    "Timed out collecting %s metrics after %.1fs",
                    component,
                    timeout_seconds,
                )
            except Exception:
                logger.exception("Failed collecting %s metrics", component)
        return fallback

    def metrics(self) -> Dict[str, Any]:
        cpu = self._run_with_timeout(
            self.cpu,
            {
                "overall_percent": 0.0,
                "per_core_percent": [],
                "physical_cores": None,
                "logical_cores": None,
                "load_avg": None,
            },
            "cpu",
        )
        memory = self._run_with_timeout(
            self.memory,
            {
                "total": 0,
                "used": 0,
                "free": 0,
                "percent": 0.0,
                "swap_total": 0,
                "swap_used": 0,
                "swap_percent": 0.0,
            },
            "memory",
        )
        disk = self._run_with_timeout(
            self.disk,
            {
                "overall": {"total": 0, "used": 0, "free": 0, "percent": 0.0},
                "partitions": [],
                "io": {"read_bytes": 0, "write_bytes": 0, "read_count": 0, "write_count": 0},
            },
            "disk",
        )
        network = self._run_with_timeout(
            self.network,
            {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0,
                "errors_in": 0,
                "errors_out": 0,
                "bytes_sent_per_sec": 0.0,
                "bytes_recv_per_sec": 0.0,
            },
            "network",
        )
        processes_data = self._run_with_timeout(
            self.processes,
            {"top_processes": []},
            "processes",
        )
        top_processes_list = processes_data.get("top_processes", [])
        uptime_raw = self._run_with_timeout(
            get_system_uptime,
            {"boot_time": "", "uptime_seconds": 0},
            "uptime",
        )
        uptime_seconds = int(uptime_raw.get("uptime_seconds", 0))
        days, remaining_after_days = divmod(uptime_seconds, _SECONDS_PER_DAY)
        hours, remaining_after_hours = divmod(remaining_after_days, _SECONDS_PER_HOUR)
        minutes, seconds = divmod(remaining_after_hours, 60)

        os_info = self._run_with_timeout(get_os_info, {}, "os")
        hardware_info = self._run_with_timeout(get_hardware_info, {}, "hardware")
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
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "network": network,
            "uptime": uptime,
            "processes": top_processes_list,
            "gpu": self._run_with_timeout(
                get_gpu_metrics,
                {"available": False, "message": "GPU metrics timed out"},
                "gpu",
            ),
            "os": os_info,
            "hardware": hardware_info,
        }
