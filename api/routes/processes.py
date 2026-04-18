"""Processes route module."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_scanner_service
from api.models.metrics import ProcessesResponse
from scanner.service import SystemScannerService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["metrics"])


@router.get("/processes", response_model=ProcessesResponse)
async def process_metrics(
    service: SystemScannerService = Depends(get_scanner_service),
) -> ProcessesResponse:
    try:
        data = await asyncio.to_thread(service.processes)
        return ProcessesResponse(**data)
    except Exception as exc:
        logger.exception("Failed to collect process metrics")
        raise HTTPException(status_code=500, detail="Failed to collect process metrics") from exc
