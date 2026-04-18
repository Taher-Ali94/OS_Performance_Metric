"""FastAPI entrypoint for OS Performance Metrics Scanner."""

from fastapi import FastAPI

from api.routes.cpu import router as cpu_router
from api.routes.disk import router as disk_router
from api.routes.memory import router as memory_router
from api.routes.metrics import router as metrics_router
from api.routes.network import router as network_router
from api.routes.processes import router as processes_router
from scanner.logger import configure_logging

from fastapi.middleware.cors import CORSMiddleware




configure_logging()

app = FastAPI(title="OS Performance Metrics Scanner", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your specific preview URL
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics_router)
app.include_router(cpu_router)
app.include_router(memory_router)
app.include_router(disk_router)
app.include_router(network_router)
app.include_router(processes_router)


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok", "message": "OS Performance Metrics Scanner API"}
