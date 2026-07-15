from __future__ import annotations

from dataclasses import dataclass
from os import environ
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    model: str = "mlx-community/whisper-large-v3-turbo-q4"
    language: str | None = "en"
    sample_rate: int = 16_000
    block_size: int = 1_024
    minimum_seconds: float = 0.3
    maximum_seconds: float = 60.0
    silence_peak: float = 0.005
    mlx_cache_limit_mb: int = 128
    debug_keys: bool = False
    log_transcripts: bool = False
    log_path: Path = Path.home() / "Library/Logs/Whisper Dictate/app.log"

    @classmethod
    def from_environment(cls) -> AppConfig:
        language = environ.get("DICTATE_LANG", "en") or None
        return cls(
            model=environ.get("DICTATE_MODEL", cls.model),
            language=language,
            maximum_seconds=float(environ.get("DICTATE_MAX_SECONDS", "60")),
            mlx_cache_limit_mb=int(environ.get("DICTATE_MLX_CACHE_MB", "128")),
            debug_keys=environ.get("DICTATE_DEBUG", "0") == "1",
            log_transcripts=environ.get("DICTATE_LOG_TRANSCRIPTS", "0") == "1",
        )

