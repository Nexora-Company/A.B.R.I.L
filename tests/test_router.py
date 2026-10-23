"""Router de tres carriles tests."""

from __future__ import annotations

from abril.services.router import Lane, route


def test_routing_disabled_always_heavy():
    decision = route("hola", routing_enabled=False)
    assert decision.lane == Lane.HEAVY
    assert decision.reason == "routing desactivado → carril 3 (comportamiento legacy)"


def test_direct_commands_lane_rules():
    for cmd in ["/ayuda", "/limpiar", "/estado", "/version", "/config", "/analizar memoria"]:
        decision = route(cmd, routing_enabled=True)
        assert decision.lane == Lane.RULES
        assert decision.confidence == 1.0


def test_aliases_lane_rules():
    decision = route("hola", routing_enabled=True)
    assert decision.lane == Lane.RULES
    assert decision.intent == "saludo"

    decision = route("status", routing_enabled=True)
    assert decision.lane == Lane.RULES
    assert decision.intent == "/estado"


def test_light_patterns_lane_light():
    for text in ["qué es python", "cómo funciona", "resume el archivo", "define clase"]:
        decision = route(text, routing_enabled=True)
        assert decision.lane == Lane.LIGHT
        assert decision.confidence >= 0.7


def test_heavy_patterns_lane_heavy():
    for text in ["escribe un script en python", "analiza este código", "debug este error", "refactor la clase"]:
        decision = route(text, routing_enabled=True)
        assert decision.lane == Lane.HEAVY
        assert decision.confidence >= 0.8


def test_long_text_fallback_heavy():
    long_text = "a " * 150  # > 200 chars
    decision = route(long_text, routing_enabled=True)
    assert decision.lane == Lane.HEAVY


def test_short_text_fallback_light():
    decision = route("hola que tal", routing_enabled=True)
    assert decision.lane == Lane.LIGHT
    assert decision.intent == "chat_general"


def test_model_selection():
    decision = route("qué hora es", routing_enabled=True, light_model="small", heavy_model="large")
    assert decision.model == "small"

    decision = route("escribe un algoritmo complejo", routing_enabled=True, light_model="small", heavy_model="large")
    assert decision.model == "large"