"""Diálogo predictivo y alias: sugerencias contextuales y atajos aprendidos.

Cuando el flag `predictive` está activo:
- Aprende alias de comandos frecuentes (ej: "gh" → "git status")
- Sugiere siguientes acciones basadas en patrones
- Expande alias automáticamente antes del router
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .sqlite_memory import SQLiteMemory


def _utcnow_iso() -> str:
    """Timestamp UTC ISO 8601 sin zona, conservando el formato histórico."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


@dataclass
class Alias:
    trigger: str
    expansion: str
    count: int = 1
    confidence: float = 0.5
    created_at: str = ""
    last_used: str = ""


@dataclass
class Suggestion:
    text: str
    kind: str  # "alias", "next_action", "completion"
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


class PredictiveEngine:
    """Motor de predicción y alias basado en eventos de SQLiteMemory."""

    def __init__(self, memory: SQLiteMemory, min_count: int = 3, min_confidence: float = 0.6) -> None:
        self._memory = memory
        self._min_count = min_count
        self._min_confidence = min_confidence
        self._alias_cache: dict[str, Alias] = {}
        self._load_aliases()

    def _load_aliases(self) -> None:
        events = self._memory.get_events(kind="alias", limit=1000)
        for ev in events:
            payload = ev["payload"]
            trigger = payload.get("trigger")
            expansion = payload.get("expansion")
            if trigger and expansion:
                alias = Alias(
                    trigger=trigger,
                    expansion=expansion,
                    count=payload.get("count", 1),
                    confidence=payload.get("confidence", 0.5),
                    created_at=payload.get("created_at", ""),
                    last_used=payload.get("last_used", ""),
                )
                self._alias_cache[trigger] = alias

    def _save_alias(self, alias: Alias) -> None:
        self._memory.add_event("alias", {
            "trigger": alias.trigger,
            "expansion": alias.expansion,
            "count": alias.count,
            "confidence": alias.confidence,
            "created_at": alias.created_at or _utcnow_iso(),
            "last_used": _utcnow_iso(),
        })

    def learn_from_interaction(self, user_input: str, action_taken: str | None = None) -> None:
        """
        Aprende de la interacción usuario-asistente.

        Si el usuario escribe algo que parece un alias (corto, alfanumérico)
        y luego ejecuta una acción larga, registra el mapeo.
        """
        # Heurística: entrada corta (2-8 chars) seguida de comando largo
        if re.match(r"^[a-z0-9_-]{2,8}$", user_input.strip()) and action_taken:
            if len(action_taken) > len(user_input) * 2:
                self._register_alias(user_input.strip(), action_taken.strip())

    def _register_alias(self, trigger: str, expansion: str) -> None:
        existing = self._alias_cache.get(trigger)
        if existing:
            existing.count += 1
            existing.confidence = min(0.95, existing.confidence + 0.05)
            existing.last_used = ""
            self._save_alias(existing)
        else:
            new_alias = Alias(
                trigger=trigger,
                expansion=expansion,
                count=1,
                confidence=0.5,
                created_at=_utcnow_iso(),
            )
            self._alias_cache[trigger] = new_alias
            self._save_alias(new_alias)

    def expand_alias(self, text: str) -> str:
        """Expande alias si existe y supera umbral de confianza."""
        parts = text.strip().split(maxsplit=1)
        if not parts:
            return text
        trigger = parts[0]
        alias = self._alias_cache.get(trigger)
        if alias and alias.confidence >= self._min_confidence and alias.count >= self._min_count:
            rest = parts[1] if len(parts) > 1 else ""
            return f"{alias.expansion} {rest}".strip()
        return text

    def get_suggestions(self, context: str = "", limit: int = 5) -> list[Suggestion]:
        """Genera sugerencias contextuales basadas en historial y alias."""
        suggestions: list[Suggestion] = []

        # 1. Alias coincidentes con prefijo
        for trigger, alias in self._alias_cache.items():
            if trigger.startswith(context.lower()) and alias.confidence >= self._min_confidence:
                suggestions.append(Suggestion(
                    text=f"{trigger} → {alias.expansion}",
                    kind="alias",
                    confidence=alias.confidence,
                    metadata={"trigger": trigger, "expansion": alias.expansion},
                ))

        # 2. Acciones frecuentes recientes (desde audit_log)
        audit = self._memory.get_audit_log(limit=50)
        action_counter = Counter(entry["action"] for entry in audit if entry["action"])
        for action, count in action_counter.most_common(3):
            if count >= 2:
                suggestions.append(Suggestion(
                    text=f"/{action}",
                    kind="next_action",
                    confidence=min(0.8, 0.4 + count * 0.1),
                    metadata={"action": action, "frequency": count},
                ))

        # 3. Completado de comandos conocidos
        known_commands = [
            "/analizar", "/ideas", "/pensar", "/programar", "/ejecutar", "/revisar",
            "/acciones", "/historial", "/limpiar", "/estado", "/config", "/version",
        ]
        for cmd in known_commands:
            if cmd.startswith(context) or context in cmd:
                suggestions.append(Suggestion(
                    text=cmd,
                    kind="completion",
                    confidence=0.6,
                    metadata={"command": cmd},
                ))

        # Ordenar por confianza y limitar
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions[:limit]

    def list_aliases(self) -> list[Alias]:
        return list(self._alias_cache.values())


def build_predictive_engine(memory: SQLiteMemory) -> PredictiveEngine:
    return PredictiveEngine(memory)


__all__ = ["Alias", "Suggestion", "PredictiveEngine", "build_predictive_engine"]