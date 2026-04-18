"""Shared logging configuration for API and UI."""

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging once for the application."""

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
