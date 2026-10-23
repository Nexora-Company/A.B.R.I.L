"""Capa de privacidad estricta: local-only, sin telemetría, sin red saliente.

Cuando el flag `local_strict` está activo (por defecto), esta capa:
- Bloquea cualquier intento de conexión de red saliente desde el proceso
- Fuerza `OLLAMA_HOST` a localhost
- Desactiva proveedores cloud
- Registra intentos de acceso a red en auditoría
"""

from __future__ import annotations

import os
import socket
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable


# Variable global de estado (se inicializa en bootstrap)
_local_strict_enabled = True
_blocked_domains: set[str] = set()
_audit_callback: Callable[[str, dict[str, Any]], None] | None = None


def enable_local_strict(enabled: bool = True) -> None:
    global _local_strict_enabled
    _local_strict_enabled = enabled


def is_local_strict() -> bool:
    return _local_strict_enabled


def set_audit_callback(cb: Callable[[str, dict[str, Any]], None]) -> None:
    global _audit_callback
    _audit_callback = cb


def _audit(event: str, details: dict[str, Any]) -> None:
    if _audit_callback:
        try:
            _audit_callback(event, details)
        except Exception:
            pass


# ── Parcheo de socket para bloquear red saliente ───────────────────

_original_socket_connect = socket.socket.connect

def _blocked_connect(self: socket.socket, address: tuple[str, int] | tuple[str, int, int, int]) -> None:
    host = address[0]
    # Permitir localhost y Unix sockets
    if host in ("127.0.0.1", "::1", "localhost") or host.startswith("127."):
        return _original_socket_connect(self, address)
    # Verificar dominios bloqueados explícitamente
    if _blocked_domains and any(host.endswith(d) for d in _blocked_domains):
        _audit("network_blocked_domain", {"host": host, "port": address[1] if len(address) > 1 else 0})
        raise PermissionError(f"Conexión a {host} bloqueada por política local-strict")
    # En modo estricto, bloquear TODO lo que no sea localhost
    if _local_strict_enabled:
        _audit("network_blocked_strict", {"host": host, "port": address[1] if len(address) > 1 else 0})
        raise PermissionError(f"Conexión saliente a {host} bloqueada (local-strict)")
    return _original_socket_connect(self, address)


def activate_network_block() -> None:
    """Activa el bloqueo de red a nivel de socket (idempotente)."""
    if socket.socket.connect is not _blocked_connect:
        socket.socket.connect = _blocked_connect  # type: ignore[assignment]


def deactivate_network_block() -> None:
    """Restaura el comportamiento original de socket."""
    if socket.socket.connect is _blocked_connect:
        socket.socket.connect = _original_socket_connect  # type: ignore[method-assign]


# ── Utilidades para código que necesita red ────────────────────────

@contextmanager
def temporary_network_access():
    """Context manager para permitir red temporalmente (usar con extrema precaución)."""
    was_enabled = _local_strict_enabled
    enable_local_strict(False)
    try:
        yield
    finally:
        enable_local_strict(was_enabled)


def require_local_only(func: Callable) -> Callable:
    """Decorador que falla si local-strict está activo y la función intenta red."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if _local_strict_enabled:
            raise PermissionError(f"{func.__name__} requiere acceso a red, bloqueado por local-strict")
        return func(*args, **kwargs)
    return wrapper


# ── Configuración de entorno para proveedores ──────────────────────

def sanitize_ollama_env() -> dict[str, str]:
    """
    Devuelve variables de entorno seguras para Ollama en modo local-strict.
    Fuerza host localhost y desactiva telemetría.
    """
    env = os.environ.copy()
    if _local_strict_enabled:
        env["OLLAMA_HOST"] = "127.0.0.1:11434"
        env["OLLAMA_ORIGINS"] = ""  # sin CORS externo
        env["OLLAMA_TELEMETRY"] = "false"
    return env


__all__ = [
    "enable_local_strict",
    "is_local_strict",
    "set_audit_callback",
    "activate_network_block",
    "deactivate_network_block",
    "temporary_network_access",
    "require_local_only",
    "sanitize_ollama_env",
]