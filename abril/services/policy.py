"""Política de permisos por niveles para acciones sensibles.

Define qué acciones requieren confirmación, cuáles están permitidas
y cuáles denegadas según el nivel de confianza. Integra con NEXO-BRACE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PermissionLevel(Enum):
    DENY = 0      # Nunca permitido
    ASK = 1       # Requiere confirmación explícita
    ALLOW = 2     # Permitido sin confirmación (si confianza alta)


class ActionKind(Enum):
    OPEN = "open"
    SEARCH = "search"
    SUMMARIZE = "summarize"
    EXECUTE = "execute"
    READ = "read"
    WRITE = "write"
    LIST = "list"
    DELETE = "delete"
    INSTALL = "install"
    SYSTEM = "system"
    NETWORK = "network"


@dataclass
class PolicyRule:
    action: ActionKind
    level: PermissionLevel
    # Condiciones opcionales
    paths: list[str] = field(default_factory=list)      # Rutas permitidas/denegadas (globs)
    args_patterns: list[str] = field(default_factory=list)  # Patrones en argumentos
    max_risk: int = 0  # 0-10, umbral de riesgo


# ── Política por defecto (conservadora) ────────────────────────────

_DEFAULT_RULES: list[PolicyRule] = [
    PolicyRule(ActionKind.OPEN, PermissionLevel.ALLOW),
    PolicyRule(ActionKind.SEARCH, PermissionLevel.ALLOW),
    PolicyRule(ActionKind.SUMMARIZE, PermissionLevel.ALLOW),
    PolicyRule(ActionKind.READ, PermissionLevel.ASK, paths=["**/*"]),
    PolicyRule(ActionKind.WRITE, PermissionLevel.ASK, paths=["**/*"]),
    PolicyRule(ActionKind.LIST, PermissionLevel.ALLOW),
    PolicyRule(ActionKind.EXECUTE, PermissionLevel.ASK, max_risk=5),
    PolicyRule(ActionKind.DELETE, PermissionLevel.DENY),
    PolicyRule(ActionKind.INSTALL, PermissionLevel.DENY),
    PolicyRule(ActionKind.SYSTEM, PermissionLevel.DENY),
    PolicyRule(ActionKind.NETWORK, PermissionLevel.ASK),
]


@dataclass
class PolicyDecision:
    allowed: bool
    level: PermissionLevel
    reason: str
    rule: PolicyRule | None = None
    requires_confirmation: bool = False


class PermissionPolicy:
    """Motor de políticas evaluable en tiempo de ejecución."""

    def __init__(self, rules: list[PolicyRule] | None = None) -> None:
        self._rules = {rule.action: rule for rule in (rules or _DEFAULT_RULES)}

    def get_rule(self, action: ActionKind) -> PolicyRule:
        return self._rules.get(action, PolicyRule(action, PermissionLevel.ASK))

    def evaluate(
        self,
        action: ActionKind,
        *,
        detail: str = "",
        args: dict[str, Any] | None = None,
        risk_score: int = 0,
    ) -> PolicyDecision:
        rule = self.get_rule(action)
        effective_level = rule.level

        # Evaluar condiciones de paths
        if rule.paths and args and "path" in args:
            path = args["path"]
            if not self._match_paths(path, rule.paths):
                return PolicyDecision(
                    allowed=False,
                    level=PermissionLevel.DENY,
                    reason=f"Ruta fuera de alcance permitido: {path}",
                    rule=rule,
                )

        # Evaluar riesgo
        if risk_score > rule.max_risk and rule.max_risk > 0:
            return PolicyDecision(
                allowed=False,
                level=PermissionLevel.DENY,
                reason=f"Riesgo {risk_score} supera umbral {rule.max_risk}",
                rule=rule,
            )

        allowed = effective_level != PermissionLevel.DENY
        requires_confirmation = effective_level == PermissionLevel.ASK

        return PolicyDecision(
            allowed=allowed,
            level=effective_level,
            reason=f"Política: {effective_level.name.lower()}",
            rule=rule,
            requires_confirmation=requires_confirmation,
        )

    def _match_paths(self, path: str, patterns: list[str]) -> bool:
        import fnmatch
        for pat in patterns:
            if fnmatch.fnmatch(path, pat):
                return True
        return False

    def set_rule(self, action: ActionKind, level: PermissionLevel, **kwargs) -> None:
        self._rules[action] = PolicyRule(action, level, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return {
            action.value: {
                "level": rule.level.name,
                "paths": rule.paths,
                "args_patterns": rule.args_patterns,
                "max_risk": rule.max_risk,
            }
            for action, rule in self._rules.items()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PermissionPolicy":
        rules = []
        for action_str, rule_data in data.items():
            try:
                action = ActionKind(action_str)
                level = PermissionLevel[rule_data["level"]]
                rules.append(PolicyRule(
                    action=action,
                    level=level,
                    paths=rule_data.get("paths", []),
                    args_patterns=rule_data.get("args_patterns", []),
                    max_risk=rule_data.get("max_risk", 0),
                ))
            except (KeyError, ValueError):
                continue
        return cls(rules)


# Instancia global por defecto (se sobrescribe en bootstrap si flag policy)
_default_policy = PermissionPolicy()


def get_default_policy() -> PermissionPolicy:
    return _default_policy


__all__ = [
    "PermissionLevel",
    "ActionKind",
    "PolicyRule",
    "PolicyDecision",
    "PermissionPolicy",
    "get_default_policy",
]