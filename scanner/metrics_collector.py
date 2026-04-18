"""System metrics collection layer."""

from __future__ import annotations

import platform
import socket
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import psutil

try:
    import GPUtil  # type: ignore
except Exception:  # pragma: no cover - optional dependency behavior
    GPUtil = None


class NetworkSampler:
    """Computes network transfer speed based on consecutive samples."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_bytes_sent = 0
        self._last_bytes_recv = 0
        self._last_ts = 0.0

    def sample(self) -> Dict[str, float]:
        with self._lock:
            counters = psutil.net_io_counters()
            now = time.time()

            sent_rate = 0.0
            recv_rate = 0.0
            if self._last_ts > 0:
                elapsed = max(now - self._last_ts, 1e-6)
                sent_rate = (counters.bytes_sent - self._last_bytes_sent) / elapsed
                recv_rate = (counters.bytes_recv - self._last_bytes_recv) / elapsed

            self._last_bytes_sent = counters.bytes_sent
            self._last_bytes_recv = counters.bytes_recv
            self._last_ts = now

            return {
                "bytes_sent_per_sec": max(sent_rate, 0.0),
                "bytes_recv_per_sec": max(recv_rate, 0.0),
            }


_NETWORK_SAMPLER = NetworkSampler()


def get_cpu_metrics() -> Dict[str, Any]:
    """Return overall and per-core CPU usage."""

    per_core = psutil.cpu_percent(interval=0.1, percpu=True)
    return {
        "overall_percent": sum(per_core) / max(len(per_core), 1),
        "per_core_percent": per_core,
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "load_avg": list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else None,
    }


def get_memory_metrics() -> Dict[str, Any]:
    """Return memory and swap usage details."""

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total": mem.total,
        "used": mem.used,
        "free": mem.available,
        "percent": mem.percent,
        "swap_total": swap.total,
        "swap_used": swap.used,
        "swap_percent": swap.percent,
    }


def get_disk_metrics() -> Dict[str, Any]:
    """Return overall and per-partition disk usage."""

    partitions: List[Dict[str, Any]] = []
    for partition in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            continue
        partitions.append(
            {
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            }
        )

    root_mount = "C:\\" if platform.system().lower().startswith("win") else "/"
    overall_usage = psutil.disk_usage(root_mount)
    io = psutil.disk_io_counters()

    return {
        "overall": {
            "total": overall_usage.total,
            "used": overall_usage.used,
            "free": overall_usage.free,
            "percent": overall_usage.percent,
        },
        "partitions": partitions,
        "io": {
            "read_bytes": getattr(io, "read_bytes", 0),
            "write_bytes": getattr(io, "write_bytes", 0),
            "read_count": getattr(io, "read_count", 0),
            "write_count": getattr(io, "write_count", 0),
        },
    }


def get_network_metrics() -> Dict[str, Any]:
    """Return network counters and estimated transfer speed."""

    counters = psutil.net_io_counters()
    speed = _NETWORK_SAMPLER.sample()

    return {
        "bytes_sent": counters.bytes_sent,
        "bytes_recv": counters.bytes_recv,
        "packets_sent": counters.packets_sent,
        "packets_recv": counters.packets_recv,
        "errors_in": counters.errin,
        "errors_out": counters.errout,
        **speed,
    }


def get_system_uptime() -> Dict[str, Any]:
    """Return boot timestamp and uptime in seconds."""

    boot_ts = psutil.boot_time()
    now = time.time()
    return {
        "boot_time": datetime.fromtimestamp(boot_ts, tz=timezone.utc).isoformat(),
        "uptime_seconds": int(now - boot_ts),
    }


def get_top_processes(limit: int = 10) -> List[Dict[str, Any]]:
    """Return top processes sorted by CPU then memory consumption."""

    processes = []
    for proc in psutil.process_iter(
        attrs=["pid", "name", "username", "cpu_percent", "memory_percent", "status"]
    ):
        try:
            info = proc.info
            processes.append(
                {
                    "pid": info.get("pid"),
                    "name": info.get("name") or "unknown",
                    "username": info.get("username") or "unknown",
                    "cpu_percent": float(info.get("cpu_percent") or 0.0),
                    "memory_percent": float(info.get("memory_percent") or 0.0),
                    "status": info.get("status") or "unknown",
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return sorted(
        processes,
        key=lambda item: (item["cpu_percent"], item["memory_percent"]),
        reverse=True,
    )[:limit]


def get_gpu_metrics() -> Dict[str, Any]:
    """Return GPU metrics if GPUtil is installed and GPUs are present."""

    if GPUtil is None:
        return {"available": False, "message": "GPUtil not installed"}

    gpus = GPUtil.getGPUs()
    if not gpus:
        return {"available": False, "message": "No GPU detected"}

    return {
        "available": True,
        "gpus": [
            {
                "id": gpu.id,
                "name": gpu.name,
                "load_percent": gpu.load * 100,
                "memory_total_mb": gpu.memoryTotal,
                "memory_used_mb": gpu.memoryUsed,
                "memory_util_percent": gpu.memoryUtil * 100,
                "temperature_c": gpu.temperature,
            }
            for gpu in gpus
        ],
    }


def get_os_info() -> Dict[str, Any]:
    """Return operating system details."""

    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "hostname": socket.gethostname(),
        "python_version": platform.python_version(),
    }


def get_hardware_info() -> Dict[str, Any]:
    """Return hardware details about CPU and host."""

    return {
        "cpu_model": platform.processor() or "unknown",
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "cpu_freq_mhz": (
            {
                "current": psutil.cpu_freq().current,
                "min": psutil.cpu_freq().min,
                "max": psutil.cpu_freq().max,
            }
            if psutil.cpu_freq()
            else None
        ),
    }
