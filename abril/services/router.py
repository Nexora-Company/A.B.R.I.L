"""Router de tres carriles: reglas → modelo ligero → modelo pesado.

Este módulo clasifica la entrada del usuario y decide qué carril usar.
Si el flag `routing` está apagado, todo va al carril 3 (comportamiento actual).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Lane(Enum):
    RULES = 1      # Comandos directos, aliases, coincidencia exacta
    LIGHT = 2      # Intención simple, respuestas cortas
    HEAVY = 3      # Código, análisis, razonamiento complejo


@dataclass
class RouteDecision:
    lane: Lane
    intent: str
    confidence: float
    model: str | None = None
    reason: str = ""
    metadata: dict[str, Any] | None = None


# ── Patrones de carril 1 (reglas) ──────────────────────────────────
_DIRECT_COMMANDS = {
    "/ayuda", "/limpiar", "/estado", "/historial", "/acciones",
    "/confirmar", "/cancelar", "/version", "/config", "/flags",
    "/programar", "/ejecutar", "/revisar",
    "/analizar", "/ideas", "/pensar",
}

_ALIASES = {
    "hola": "saludo",
    "qué tal": "saludo",
    "buenos días": "saludo",
    "buenas tardes": "saludo",
    "adiós": "despedida",
    "chao": "despedida",
    "gracias": "agradecimiento",
    "status": "/estado",
    "ayuda": "/ayuda",
    "limpiar": "/limpiar",
    "ver acciones": "/acciones",
    "ver historial": "/historial",
}

# Patrones que indican carril 2 (intención simple)
_LIGHT_PATTERNS = [
    (re.compile(r"^(qué|que|cuál|cual|cómo|como|dónde|donde|cuándo|cuando|por qué|porque)\s", re.I), "pregunta_corta"),
    (re.compile(r"^(resume|resumen|define|explica|traduce)\s", re.I), "tarea_simple"),
    (re.compile(r"^\w+\?$"), "pregunta_una_palabra"),
]

# Patrones que fuerzan carril 3 (complejo)
_HEAVY_PATTERNS = [
    (re.compile(r"(código|code|script|función|clase|algorithm|debug|refactor|optimiza)", re.I), "programación"),
    (re.compile(r"(analiza|analizar|estudia|investiga|profundo|piensa|razona)", re.I), "análisis_profundo"),
    (re.compile(r"(escribe|crea|genera).*(artículo|ensayo|email|documento|algoritmo|script|código)", re.I), "redacción_larga"),
    (re.compile(r"^(escribe|crea|genera)\s", re.I), "generación"),
]


def _match_aliases(text: str) -> str | None:
    """Devuelve el comando/alias si coincide exactamente o como prefijo (sin IA)."""
    low = text.strip().lower()
    if low in _DIRECT_COMMANDS:
        return low
    # Prefijos de comandos (ej: "/analizar memoria" -> "/analizar")
    for cmd in _DIRECT_COMMANDS:
        if low.startswith(cmd + " "):
            return cmd
    if low in _ALIASES:
        return _ALIASES[low]
    return None


def _classify_light(text: str) -> tuple[str, float] | None:
    """Intenta clasificar como intención simple (carril 2)."""
    for pattern, intent in _LIGHT_PATTERNS:
        if pattern.search(text):
            return intent, 0.75
    return None


def _classify_heavy(text: str) -> tuple[str, float] | None:
    """Detecta si requiere modelo pesado (carril 3)."""
    for pattern, intent in _HEAVY_PATTERNS:
        if pattern.search(text):
            return intent, 0.85
    return None


def route(
    text: str,
    *,
    routing_enabled: bool = False,
    light_model: str = "qwen2.5:1.5b",
    heavy_model: str = "qwen2.5:3b",
) -> RouteDecision:
    """
    Clasifica `text` y devuelve la decisión de enrutamiento.

    Args:
        text: Entrada del usuario.
        routing_enabled: Si False, siempre devuelve carril 3 (compatibilidad).
        light_model: Modelo para carril 2.
        heavy_model: Modelo para carril 3.

    Returns:
        RouteDecision con lane, intent, confidence, model sugerido y razón.
    """
    if not routing_enabled:
        return RouteDecision(
            lane=Lane.HEAVY,
            intent="compatibilidad",
            confidence=1.0,
            model=heavy_model,
            reason="routing desactivado → carril 3 (comportamiento legacy)",
        )

    text = text.strip()
    if not text:
        return RouteDecision(
            lane=Lane.RULES,
            intent="vacío",
            confidence=1.0,
            reason="entrada vacía",
        )

    # Carril 1: comandos directos y aliases exactos
    direct = _match_aliases(text)
    if direct:
        return RouteDecision(
            lane=Lane.RULES,
            intent=direct,
            confidence=1.0,
            reason="comando directo o alias exacto",
            metadata={"direct_command": direct},
        )

    # Carril 2: intención simple
    light = _classify_light(text)
    if light:
        intent, conf = light
        return RouteDecision(
            lane=Lane.LIGHT,
            intent=intent,
            confidence=conf,
            model=light_model,
            reason=f"patrón ligero: {intent}",
        )

    # Carril 3: complejo o fallback
    heavy = _classify_heavy(text)
    if heavy:
        intent, conf = heavy
        return RouteDecision(
            lane=Lane.HEAVY,
            intent=intent,
            confidence=conf,
            model=heavy_model,
            reason=f"patrón pesado: {intent}",
        )

    # Fallback: carril 3 por longitud o defecto
    if len(text) > 200:
        return RouteDecision(
            lane=Lane.HEAVY,
            intent="texto_largo",
            confidence=0.6,
            model=heavy_model,
            reason="entrada larga → carril 3",
        )

    return RouteDecision(
        lane=Lane.LIGHT,
        intent="chat_general",
        confidence=0.55,
        model=light_model,
        reason="fallback a carril 2",
    )


__all__ = ["Lane", "RouteDecision", "route"]