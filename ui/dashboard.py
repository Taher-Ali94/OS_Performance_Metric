"""Streamlit dashboard for visualizing system performance metrics."""

from __future__ import annotations

import logging
import sys
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh


def _ensure_project_root_on_path() -> None:
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent if len(script_path.parents) > 1 else script_path.parent
    for directory in script_path.parents:
        if (directory / "scanner").is_dir():
            project_root = directory
            break
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


_ensure_project_root_on_path()

from scanner.config import get_settings
from scanner.logger import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


st.set_page_config(page_title="OS Performance Metrics", layout="wide")
st.title("🖥️ OS Performance Metrics Scanner")

refresh_interval_ms = settings.refresh_interval_seconds * 1000
st_autorefresh(interval=refresh_interval_ms, key="metrics_refresh")

api_base_url = st.sidebar.text_input("API Base URL", value=settings.api_base_url)
st.sidebar.caption(f"Refresh interval: {settings.refresh_interval_seconds}s")


def fetch_metrics(url: str) -> Dict[str, Any]:
    response = requests.get(f"{url}/metrics", timeout=5)
    response.raise_for_status()
    return response.json()


try:
    metrics = fetch_metrics(api_base_url)
except requests.Timeout:
    logger.exception("Timed out while loading metrics from API")
    st.error("Connection to API timed out. Check API availability and network latency.")
    st.stop()
except Exception as exc:
    logger.exception("Failed to load metrics from API")
    st.error(f"Unable to load metrics from API: {exc}")
    st.stop()

history: Dict[str, Deque[float]] = st.session_state.setdefault(
    "history",
    {
        "cpu": deque(maxlen=30),
        "memory": deque(maxlen=30),
        "net_recv": deque(maxlen=30),
        "net_sent": deque(maxlen=30),
    },
)

history["cpu"].append(metrics["cpu"]["overall_percent"])
history["memory"].append(metrics["memory"]["percent"])
history["net_recv"].append(metrics["network"]["bytes_recv_per_sec"])
history["net_sent"].append(metrics["network"]["bytes_sent_per_sec"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("CPU Usage", f"{metrics['cpu']['overall_percent']:.1f}%")
col2.metric("Memory Usage", f"{metrics['memory']['percent']:.1f}%")
col3.metric("Disk Usage", f"{metrics['disk']['overall']['percent']:.1f}%")
col4.metric("Uptime (s)", f"{metrics['uptime']['uptime_seconds']}")

st.subheader("Resource Utilization")
st.write("CPU")
st.progress(min(max(metrics["cpu"]["overall_percent"] / 100.0, 0.0), 1.0))
st.write("Memory")
st.progress(min(max(metrics["memory"]["percent"] / 100.0, 0.0), 1.0))

trend_col1, trend_col2 = st.columns(2)
with trend_col1:
    st.subheader("CPU & Memory Trend")
    st.line_chart(
        pd.DataFrame(
            {
                "cpu_percent": list(history["cpu"]),
                "memory_percent": list(history["memory"]),
            }
        )
    )

with trend_col2:
    st.subheader("Network Speed Trend (bytes/sec)")
    st.line_chart(
        pd.DataFrame(
            {
                "recv_bps": list(history["net_recv"]),
                "sent_bps": list(history["net_sent"]),
            }
        )
    )

st.subheader("Per-Core CPU")
per_core_df = pd.DataFrame({"core_usage_percent": metrics["cpu"]["per_core_percent"]})
st.bar_chart(per_core_df)

st.subheader("Top Processes")
process_df = pd.DataFrame(metrics["processes"])
st.dataframe(process_df, use_container_width=True)

st.subheader("Disk Partitions")
partitions_df = pd.DataFrame(metrics["disk"]["partitions"])
st.dataframe(partitions_df, use_container_width=True)

st.subheader("System Information")
info_col1, info_col2 = st.columns(2)
with info_col1:
    st.json(metrics["os"])
with info_col2:
    st.json(metrics["hardware"])

if metrics.get("gpu", {}).get("available"):
    st.subheader("GPU")
    st.dataframe(pd.DataFrame(metrics["gpu"]["gpus"]))
else:
    st.info(metrics.get("gpu", {}).get("message", "GPU stats unavailable"))
