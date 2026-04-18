"""Memory route module."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_scanner_service
from api.models.metrics import MemoryResponse
from scanner.service import SystemScannerService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["metrics"])


@router.get("/memory", response_model=MemoryResponse)
async def memory_metrics(
    service: SystemScannerService = Depends(get_scanner_service),
) -> MemoryResponse:
    try:
        data = await asyncio.to_thread(service.memory)
        return MemoryResponse(**data)
    except Exception as exc:
        logger.exception("Failed to collect memory metrics")
        raise HTTPException(status_code=500, detail="Failed to collect memory metrics") from exc
