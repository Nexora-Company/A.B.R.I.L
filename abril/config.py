"""Environment and .env configuration loading. Immutable identity constants."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"

# ===== IDENTIDAD INMUTABLE (nadie puede cambiar esto) =====
CREATOR_COMPANY = "Nexora"
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
        values[key] = _clean_value(value)
    return values


def _clean_value(raw: str) -> str:
    """Strip surrounding quotes and inline comments without touching quoted text."""
    value = raw.strip()
    if not value:
        return value
    if value[0] in {"'", '"'}:
        closing = value.find(value[0], 1)
        if closing != -1:
            return value[1:closing]
    if " #" in value:
        value = value.partition(" #")[0].rstrip()
    return value


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
    host: str = "127.0.0.1"
    port: int = 8765

    @property
    def config_file(self) -> Path:
        """Feature-flag file colocated with the rest of the local data."""
        return self.data_dir / "config.json"

    @classmethod
    def load(cls, env_file: Path = DEFAULT_ENV_FILE) -> "Settings":
        values = {**_read_env_file(env_file), **os.environ}
        raw_port = _get(values, "ABRIL_PORT", "8765")
        try:
            port = int(raw_port)
        except ValueError as error:
            raise ValueError("ABRIL_PORT debe ser un número entero.") from error
        if not 1 <= port <= 65535:
            raise ValueError("ABRIL_PORT debe estar entre 1 y 65535.")
        return cls(
            project_root=PROJECT_ROOT,
            ollama_url=_get(values, "OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
            ollama_model=_get(values, "OLLAMA_MODEL", "qwen2.5:3b"),
            host=_get(values, "ABRIL_HOST", "127.0.0.1"),
            port=port,
        )
