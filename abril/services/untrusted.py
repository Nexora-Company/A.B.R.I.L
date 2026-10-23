"""Manejo de contenido no confiable: sanitización, aislamiento y etiquetado.

Cuando el flag `untrusted_content` está activo, cualquier entrada que
provenza de fuentes externas (archivos, portapapeles, red, APIs) se
marca y procesa con precauciones extra.
"""

from __future__ import annotations

import html
import re
import shlex
from dataclasses import dataclass
from enum import Enum
from typing import Any


class TrustLevel(Enum):
    TRUSTED = 0      # Generado por el usuario directamente en la terminal
    USER_FILE = 1    # Archivo del usuario en directorios permitidos
    EXTERNAL = 2     # Portapapeles, descargas, APIs, web
    UNKNOWN = 3      # Origen indeterminado


@dataclass
class ContentInfo:
    text: str
    trust: TrustLevel
    source: str
    metadata: dict[str, Any] = None  # type: ignore

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# ── Patrones de riesgo ──────────────────────────────────────────────

_INJECTION_PATTERNS = [
    (re.compile(r"(?i)ignore\s+(previous|above|all)\s+(instructions|prompts?)"), "prompt_injection"),
    (re.compile(r"(?i)ignora\s+(las\s+)?(instrucciones|instrucciones\s+anteriores|prompts?)"), "prompt_injection"),
    (re.compile(r"(?i)system\s*:"), "system_prompt_leak"),
    (re.compile(r"(?i)sistema\s*:"), "system_prompt_leak"),
    (re.compile(r"(?i)<\|.*?\|>"), "special_tokens"),
    (re.compile(r"(?i)```\w*\n.*?```", re.DOTALL), "code_block"),
    (re.compile(r"(?i)(rm\s+-rf|dd\s+if=|mkfs|:\(\)\{:;\}\|&)"), "dangerous_command"),
    (re.compile(r"(?i)(password|secret|token|api[_-]?key)\s*[:=]\s*\S+"), "credential_leak"),
    (re.compile(r"(?i)(contraseña|clave|secreto|token|password)\s*[:=]\s*\S+"), "credential_leak"),
    (re.compile(r"(?i)(password|contraseña)\s+(es|es:)\s+\S+"), "credential_leak"),
]


def _detect_risks(text: str) -> list[str]:
    risks = []
    for pattern, risk_type in _INJECTION_PATTERNS:
        if pattern.search(text):
            risks.append(risk_type)
    return risks


def _sanitize_html(text: str) -> str:
    return html.escape(text)


def _sanitize_shell(text: str) -> str:
    """Escapa para uso seguro en shell (shlex.quote)."""
    return shlex.quote(text)


def _strip_control_chars(text: str) -> str:
    # Mantener \n \t \r, eliminar demás controles
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


# ── API pública ─────────────────────────────────────────────────────

@dataclass
class ProcessedContent:
    original: str
    sanitized: str
    trust: TrustLevel
    risks: list[str]
    source: str
    metadata: dict[str, Any]


def process_content(
    text: str,
    *,
    trust: TrustLevel = TrustLevel.UNKNOWN,
    source: str = "unknown",
    metadata: dict[str, Any] | None = None,
    sanitize_html_flag: bool = True,
    sanitize_shell_flag: bool = False,
    strip_controls: bool = True,
) -> ProcessedContent:
    """
    Procesa contenido según nivel de confianza y flags.

    En modo `untrusted_content` activo, se aplican todas las sanitizaciones.
    """
    risks = _detect_risks(text)
    sanitized = text

    if strip_controls:
        sanitized = _strip_control_chars(sanitized)
    if sanitize_html_flag:
        sanitized = _sanitize_html(sanitized)
    if sanitize_shell_flag:
        sanitized = _sanitize_shell(sanitized)

    # Marcar contenido externo en metadata
    meta = metadata or {}
    meta["trust_level"] = trust.name
    meta["risk_flags"] = risks

    return ProcessedContent(
        original=text,
        sanitized=sanitized,
        trust=trust,
        risks=risks,
        source=source,
        metadata=meta,
    )


def is_safe_for_model(content: ProcessedContent, strict: bool = False) -> bool:
    """
    Determina si el contenido procesado es seguro para enviar al modelo.

    En modo estricto, cualquier riesgo bloquea el envío.
    """
    if not content.risks:
        return True
    if strict:
        return False
    # En modo no estricto, solo bloquear inyección de prompt y credenciales
    dangerous = {"prompt_injection", "system_prompt_leak", "credential_leak"}
    return not any(r in dangerous for r in content.risks)


def tag_untrusted_in_prompt(content: ProcessedContent) -> str:
    """Añade etiqueta visible al prompt si el contenido no es de confianza."""
    if content.trust in (TrustLevel.TRUSTED, TrustLevel.USER_FILE):
        return content.sanitized
    tag = f"[CONTENIDO EXTERNO: {content.source}]"
    if content.risks:
        tag += f" ⚠️ {', '.join(content.risks)}"
    return f"{tag}\n{content.sanitized}"


__all__ = [
    "TrustLevel",
    "ContentInfo",
    "ProcessedContent",
    "process_content",
    "is_safe_for_model",
    "tag_untrusted_in_prompt",
]