"""CPU route module."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_scanner_service
from api.models.metrics import CPUResponse
from scanner.service import SystemScannerService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["metrics"])


@router.get("/cpu", response_model=CPUResponse)
async def cpu_metrics(service: SystemScannerService = Depends(get_scanner_service)) -> CPUResponse:
    try:
        data = await asyncio.to_thread(service.cpu)
        return CPUResponse(**data)
    except Exception as exc:
        logger.exception("Failed to collect CPU metrics")
        raise HTTPException(status_code=500, detail="Failed to collect CPU metrics") from exc
