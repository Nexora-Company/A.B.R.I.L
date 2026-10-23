"""Privacidad local-strict tests."""

from __future__ import annotations

from abril.services.privacy import (
    enable_local_strict,
    is_local_strict,
    sanitize_ollama_env,
    activate_network_block,
    deactivate_network_block,
)


def test_local_strict_default_enabled():
    enable_local_strict(True)
    assert is_local_strict() is True


def test_local_strict_can_disable():
    enable_local_strict(False)
    assert is_local_strict() is False
    enable_local_strict(True)  # restaurar


def test_sanitize_ollama_env_forces_localhost():
    enable_local_strict(True)
    env = sanitize_ollama_env()
    assert env["OLLAMA_HOST"] == "127.0.0.1:11434"
    assert env["OLLAMA_TELEMETRY"] == "false"
    enable_local_strict(False)


def test_sanitize_ollama_env_no_change_when_disabled():
    enable_local_strict(False)
    env = sanitize_ollama_env()
    assert "OLLAMA_HOST" not in env or env.get("OLLAMA_HOST") != "127.0.0.1:11434"
    enable_local_strict(True)


def test_network_block_activation():
    # Solo testeamos que no lanza error
    activate_network_block()
    deactivate_network_block()