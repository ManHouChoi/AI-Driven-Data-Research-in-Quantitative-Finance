"""Logging setup helpers for long-running research scripts."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union


PathLike = Union[str, Path]


def configure_logging(name: str, log_file: Optional[PathLike] = None, level: int = logging.INFO) -> logging.Logger:
    """Return a logger with a console handler and optional file handler."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file is not None:
        path = Path(log_file).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
