from __future__ import annotations

import logging
import os
from contextlib import suppress
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(path: Path, *, verbose: bool = False) -> logging.Logger:
    path.parent.mkdir(parents=True, exist_ok=True)
    with suppress(OSError):
        path.parent.chmod(0o700)

    logger = logging.getLogger("dictator")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger

    handler = RotatingFileHandler(path, maxBytes=5 * 1024 * 1024, backupCount=2)
    os.chmod(path, 0o600)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s.%(msecs)03d %(levelname)s [%(threadName)s] %(message)s", "%H:%M:%S"
        )
    )
    logger.addHandler(handler)
    return logger


def transcript_metadata(text: str, *, include_text: bool = False) -> str:
    metadata = f"characters={len(text)} words={len(text.split())}"
    return f"{metadata} text={text!r}" if include_text else metadata
