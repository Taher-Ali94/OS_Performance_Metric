# OS Performance Metric Scanner

A Python-based OS performance monitoring solution with:
- **FastAPI backend** for structured REST metrics
- **Streamlit dashboard** for real-time visualization
- **Scanner service layer** for clean metric collection logic

## Project Structure

```text
/api
  /models
  /routes
/scanner
/ui
```

- `scanner/`: data collection and service orchestration
- `api/`: FastAPI app, routes, and response models
- `ui/`: Streamlit dashboard

## Features

- CPU (overall + per-core)
- Memory (total/used/free/percent + swap)
- Disk (overall + per partition + disk IO)
- Network (totals + estimated real-time speed)
- System uptime
- Top processes by CPU/memory
- Optional GPU metrics (via GPUtil)
- OS and hardware details
- Logging + JSON API responses + modular endpoints

## API Endpoints

- `GET /metrics` → full metrics snapshot
- `GET /cpu`
- `GET /memory`
- `GET /disk`
- `GET /network`
- `GET /processes`

## Run Instructions

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Start FastAPI server

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3) Start Streamlit dashboard

```bash
streamlit run ui/dashboard.py
```

## Configuration

Default configuration is in `config.json`:
- `refresh_interval_seconds`
- `top_process_count`
- `network_sample_seconds`
- API host/port/base URL

You can override values using environment variables:
- `CONFIG_PATH`
- `REFRESH_INTERVAL_SECONDS`
- `TOP_PROCESS_COUNT`
- `NETWORK_SAMPLE_SECONDS`
- `API_HOST`, `API_PORT`, `API_BASE_URL`

## Cross-platform Notes

The scanner uses `psutil`, `platform`, and `socket`, so it supports Linux, macOS, and Windows (subject to OS-level permission differences on process/partition visibility).
