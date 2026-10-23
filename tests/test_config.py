"""Configuration loading and immutable identity tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from abril.config import ASSISTANT_NAME, CREATOR_COMPANY, PROJECT_ROOT, Settings
from abril.services.chat import SYSTEM_PROMPT


def _clear_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("ABRIL_HOST", "ABRIL_PORT", "OLLAMA_URL", "OLLAMA_MODEL"):
        monkeypatch.delenv(key, raising=False)


def test_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_environment(monkeypatch)
    settings = Settings.load(tmp_path / ".env")

    assert settings.project_root == PROJECT_ROOT
    assert settings.host == "127.0.0.1"
    assert settings.port == 8765
    assert settings.ollama_url == "http://127.0.0.1:11434"
    assert settings.config_file == settings.data_dir / "config.json"


def test_reads_host_and_port(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_environment(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("ABRIL_HOST=0.0.0.0\nABRIL_PORT=9000\n", encoding="utf-8")

    settings = Settings.load(env_file)

    assert settings.host == "0.0.0.0"
    assert settings.port == 9000


def test_rejects_invalid_port(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_environment(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("ABRIL_PORT=no-es-numero\n", encoding="utf-8")

    with pytest.raises(ValueError, match="ABRIL_PORT"):
        Settings.load(env_file)


def test_rejects_out_of_range_port(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_environment(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("ABRIL_PORT=70000\n", encoding="utf-8")

    with pytest.raises(ValueError, match="ABRIL_PORT"):
        Settings.load(env_file)


def test_quoted_values_and_inline_comments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_environment(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text('OLLAMA_MODEL="modelo:1b" # comentario\nABRIL_HOST=localhost\n', encoding="utf-8")

    settings = Settings.load(env_file)

    assert settings.ollama_model == "modelo:1b"
    assert settings.host == "localhost"


def test_identity_constants_are_immutable() -> None:
    assert CREATOR_COMPANY == "Nexora"
    assert ASSISTANT_NAME == "Abril"
    assert "Nexora" in SYSTEM_PROMPT
    assert "Abril" in SYSTEM_PROMPT
    assert "creado por Nexora" in SYSTEM_PROMPT
