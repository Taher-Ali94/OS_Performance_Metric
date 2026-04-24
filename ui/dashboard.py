"""Streamlit dashboard for visualizing system performance metrics."""

from __future__ import annotations

import logging
import sys
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict


def _bootstrap_path() -> None:
    """Ensure the project root is on sys.path so scanner package is importable.

    Streamlit adds the current working directory to sys.path, which works when
    launching from the project root but fails when run from any other directory
    (e.g. ``cd ui && streamlit run dashboard.py`` or from an IDE).  Walking up
    from this file's location guarantees the correct root is found regardless of
    the working directory.
    """
    script_path = Path(__file__).resolve()
    for directory in script_path.parents:
        if (directory / "scanner").is_dir():
            root = str(directory)
            if root not in sys.path:
                sys.path.insert(0, root)
            return
    raise RuntimeError(
        f"Could not locate project root containing 'scanner' directory from {script_path}."
    )


_bootstrap_path()

import pandas as pd  # noqa: E402
import requests  # noqa: E402
import streamlit as st  # noqa: E402
from streamlit_autorefresh import st_autorefresh  # noqa: E402

from scanner.config import get_settings  # noqa: E402
from scanner.logger import configure_logging  # noqa: E402

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


st.set_page_config(page_title="OS Performance Metrics", layout="wide")

# Prevent the UI from dimming during auto-refresh reruns.
# Streamlit reduces the opacity of stale elements to 0.33 while a rerun is
# in progress, which causes a visible darkening effect every refresh cycle.
st.markdown(
    "<style>[data-stale='true'] { opacity: 1 !important; }</style>",
    unsafe_allow_html=True,
)

st.title("🖥️ OS Performance Metrics Scanner")

refresh_interval_ms = settings.refresh_interval_seconds * 1000
st_autorefresh(interval=refresh_interval_ms, key="metrics_refresh")

api_base_url = st.sidebar.text_input("API Base URL", value=settings.api_base_url)
st.sidebar.caption(f"Refresh interval: {settings.refresh_interval_seconds}s")


def fetch_metrics(url: str) -> Dict[str, Any]:
    normalized_url = url.rstrip("/")
    response = requests.get(
        f"{normalized_url}/metrics",
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


try:
    metrics = fetch_metrics(api_base_url)
    st.session_state["last_metrics"] = metrics
except requests.Timeout:
    logger.exception("Timed out while loading metrics from API")
    cached_metrics = st.session_state.get("last_metrics")
    if cached_metrics:
        st.warning("API request timed out. Displaying the last successful snapshot.")
        metrics = cached_metrics
    else:
        st.error("Connection to API timed out. Check API availability and network latency.")
        st.stop()
except requests.RequestException as exc:
    logger.exception("Failed to load metrics from API")
    cached_metrics = st.session_state.get("last_metrics")
    if cached_metrics:
        st.warning("API request failed. Displaying the last successful snapshot.")
        metrics = cached_metrics
    else:
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
st.dataframe(process_df, width="stretch")

st.subheader("Disk Partitions")
partitions_df = pd.DataFrame(metrics["disk"]["partitions"])
st.dataframe(partitions_df, width="stretch")

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
