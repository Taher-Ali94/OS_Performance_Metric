"""Disk route module."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_scanner_service
from api.models.metrics import DiskResponse
from scanner.service import SystemScannerService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["metrics"])


@router.get("/disk", response_model=DiskResponse)
async def disk_metrics(service: SystemScannerService = Depends(get_scanner_service)) -> DiskResponse:
    try:
        data = await asyncio.to_thread(service.disk)
        return DiskResponse(**data)
    except Exception as exc:
        logger.exception("Failed to collect disk metrics")
        raise HTTPException(status_code=500, detail="Failed to collect disk metrics") from exc
