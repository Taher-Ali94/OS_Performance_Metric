"""Full metrics route module."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_scanner_service
from api.models.metrics import MetricsResponse
from scanner.service import SystemScannerService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
async def all_metrics(
    service: SystemScannerService = Depends(get_scanner_service),
) -> MetricsResponse:
    try:
        data = await asyncio.to_thread(service.metrics)
        return MetricsResponse(**data)
    except Exception as exc:
        logger.exception("Failed to collect complete metrics")
        raise HTTPException(status_code=500, detail="Failed to collect complete metrics") from exc
