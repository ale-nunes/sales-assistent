"""Structured-enough standard logging setup for local development."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure console logging without including secret values."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
