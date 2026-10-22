"""Environment and .env configuration loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


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
    host: str
    port: int
    provider: str
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    ollama_url: str
    ollama_model: str
    max_request_bytes: int = 1_500_000
    max_history_messages: int = 30
    max_message_chars: int = 100_000

    @classmethod
    def load(cls, env_file: Path = DEFAULT_ENV_FILE) -> "Settings":
        # Real process environment wins over the local .env file.
        values = {**_read_env_file(env_file), **os.environ}
        provider = _get(values, "ABRIL_PROVIDER", "openai").lower()
        if provider not in {"openai", "ollama"}:
            raise ValueError("ABRIL_PROVIDER debe ser 'openai' o 'ollama'.")
        try:
            port = int(_get(values, "ABRIL_PORT", "8765"))
        except ValueError as error:
            raise ValueError("ABRIL_PORT debe ser un número entero.") from error
        if not 1 <= port <= 65535:
            raise ValueError("ABRIL_PORT debe estar entre 1 y 65535.")

        return cls(
            project_root=PROJECT_ROOT,
            host=_get(values, "ABRIL_HOST", "127.0.0.1"),
            port=port,
            provider=provider,
            openai_api_key=_get(values, "OPENAI_API_KEY", ""),
            openai_base_url=_get(values, "OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            openai_model=_get(values, "OPENAI_MODEL", "gpt-5.6-terra"),
            ollama_url=_get(values, "OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
            ollama_model=_get(values, "OLLAMA_MODEL", "qwen3:4b"),
        )
