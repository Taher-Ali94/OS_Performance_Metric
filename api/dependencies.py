"""Shared API dependencies."""

from functools import lru_cache

from scanner.config import get_settings
from scanner.service import SystemScannerService


@lru_cache(maxsize=1)
def get_scanner_service() -> SystemScannerService:
    return SystemScannerService(settings=get_settings())
