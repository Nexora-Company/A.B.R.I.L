"""Environment and .env configuration loading. Immutable identity constants."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"

# ===== IDENTIDAD INMUTABLE (nadie puede cambiar esto) =====
CREATOR_COMPANY = "Nexora"
CREATOR_DEVELOPER = "Santiago Sarmiento"
ASSISTANT_NAME = "Abril"


def _read_env_file(path: Path) -> dict[str, str]:
    """Read simple KEY=VALUE entries without expanding variables or executing shell code."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key or not key.replace("_", "").isalnum():
            raise ValueError(f"Entrada inválida en {path.name}, línea {line_number}.")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        elif " #" in value:
            value = value.partition(" #")[0].rstrip()
        values[key] = value
    return values


def _get(source: dict[str, str], key: str, default: str) -> str:
    return source.get(key, default).strip()


@dataclass(frozen=True)
class Settings:
    project_root: Path
    ollama_url: str
    ollama_model: str
    max_request_bytes: int = 1_500_000
    max_history_messages: int = 30
    max_message_chars: int = 100_000
    data_dir: Path = PROJECT_ROOT / "data"

    @classmethod
    def load(cls, env_file: Path = DEFAULT_ENV_FILE) -> "Settings":
        values = {**_read_env_file(env_file), **os.environ}
        return cls(
            project_root=PROJECT_ROOT,
            ollama_url=_get(values, "OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
            ollama_model=_get(values, "OLLAMA_MODEL", "qwen2.5:3b"),
        )
