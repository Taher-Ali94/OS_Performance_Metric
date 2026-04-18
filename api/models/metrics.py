"""Pydantic models for API responses."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CPUResponse(BaseModel):
    overall_percent: float
    per_core_percent: List[float]
    physical_cores: Optional[int]
    logical_cores: Optional[int]
    load_avg: Optional[List[float]]


class MemoryResponse(BaseModel):
    total: int
    used: int
    free: int
    percent: float
    swap_total: int
    swap_used: int
    swap_percent: float


class DiskPartition(BaseModel):
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float


class DiskResponse(BaseModel):
    overall: Dict[str, Any]
    partitions: List[DiskPartition]
    io: Dict[str, Any]


class NetworkResponse(BaseModel):
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errors_in: int
    errors_out: int
    bytes_sent_per_sec: float
    bytes_recv_per_sec: float


class ProcessInfo(BaseModel):
    pid: int
    name: str
    username: str
    cpu_percent: float
    memory_percent: float
    status: str


class ProcessesResponse(BaseModel):
    top_processes: List[ProcessInfo]


class MetricsResponse(BaseModel):
    cpu: CPUResponse
    memory: MemoryResponse
    disk: DiskResponse
    network: NetworkResponse
    uptime: Dict[str, Any]
    processes: List[ProcessInfo]
    gpu: Dict[str, Any]
    os: Dict[str, Any]
    hardware: Dict[str, Any]
