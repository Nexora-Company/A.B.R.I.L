"""Protocolo NEXO-BRACE: capa de limitación de capacidades de Abril.

NEXO-BRACE (Boundary Restriction And Capability Enforcement) actúa como
un "freno de mano" que impide que Abril desbloquee todas sus funciones
a menos que se cumplan condiciones estrictas (hardware, política, consentimiento).

Estados:
- LOCKED: Solo funciones básicas (chat, memoria, comandos directos)
- PARTIAL: Funciones ampliadas según perfil hardware y políticas
- FULL: Todas las capacidades (requiere NEXUS-LOCK desbloqueado + consentimiento)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NEXOBraceState(Enum):
    LOCKED = "locked"
    PARTIAL = "partial"
    FULL = "full"


@dataclass
class CapabilityGate:
    """Define una capacidad y sus requisitos para desbloqueo."""
    name: str
    description: str
    required_state: NEXOBraceState
    # Condiciones adicionales
    min_hardware_tier: str = "low"
    required_flags: list[str] = field(default_factory=list)
    required_policy_level: str = "ask"
    user_consent: bool = False


# ── Capacidades gestionadas por NEXO-BRACE ─────────────────────────

_CAPABILITIES: dict[str, CapabilityGate] = {
    "router": CapabilityGate(
        name="router",
        description="Router de tres carriles (reglas/ligero/pesado)",
        required_state=NEXOBraceState.PARTIAL,
        min_hardware_tier="low",
        required_flags=["routing"],
        required_policy_level="allow",
    ),
    "hardware_profiles": CapabilityGate(
        name="hardware_profiles",
        description="Detección y perfiles de hardware automáticos",
        required_state=NEXOBraceState.PARTIAL,
        min_hardware_tier="low",
        required_flags=["hardware_profiles"],
    ),
    "policy": CapabilityGate(
        name="policy",
        description="Motor de permisos por niveles",
        required_state=NEXOBraceState.PARTIAL,
        min_hardware_tier="mid",
        required_flags=["policy"],
        required_policy_level="allow",
    ),
    "sqlite_memory": CapabilityGate(
        name="sqlite_memory",
        description="Memoria persistente en SQLite",
        required_state=NEXOBraceState.PARTIAL,
        min_hardware_tier="mid",
        required_flags=["sqlite_memory"],
    ),
    "predictive": CapabilityGate(
        name="predictive",
        description="Alias y diálogo predictivo",
        required_state=NEXOBraceState.PARTIAL,
        min_hardware_tier="mid",
        required_flags=["predictive"],
    ),
    "voice": CapabilityGate(
        name="voice",
        description="Voz local (STT/TTS/wake word)",
        required_state=NEXOBraceState.FULL,
        min_hardware_tier="high",
        required_flags=["voice"],
        required_policy_level="allow",
        user_consent=True,
    ),
    "cloud_providers": CapabilityGate(
        name="cloud_providers",
        description="Proveedores cloud (OpenAI, Anthropic, etc.)",
        required_state=NEXOBraceState.FULL,
        min_hardware_tier="low",
        required_flags=["cloud_providers"],
        required_policy_level="allow",
        user_consent=True,
    ),
    "domotics": CapabilityGate(
        name="domotics",
        description="Integración domótica (NEXUS-LOCK)",
        required_state=NEXOBraceState.FULL,
        min_hardware_tier="mid",
        required_flags=["nexus_lock"],
        required_policy_level="allow",
        user_consent=True,
    ),
}


class NEXOBrace:
    """Evaluador de estado NEXO-BRACE y guardián de capacidades."""

    def __init__(
        self,
        hardware_tier: str = "low",
        flags: dict[str, bool] | None = None,
        policy_level: str = "ask",
        user_consent: bool = False,
        nexus_locked: bool = True,
    ) -> None:
        self.hardware_tier = hardware_tier
        self.flags = flags or {}
        self.policy_level = policy_level
        self.user_consent = user_consent
        self.nexus_locked = nexus_locked
        self._state = self._compute_state()

    def _compute_state(self) -> NEXOBraceState:
        if self.nexus_locked and not self.user_consent:
            return NEXOBraceState.LOCKED
        # Si NEXUS-LOCK desbloqueado y consentimiento, FULL
        if not self.nexus_locked and self.user_consent:
            return NEXOBraceState.FULL
        # Intermedio: PARTIAL
        return NEXOBraceState.PARTIAL

    @property
    def state(self) -> NEXOBraceState:
        return self._state

    def refresh(self) -> None:
        self._state = self._compute_state()

    def is_unlocked(self, capability: str) -> bool:
        """Verifica si una capacidad está desbloqueada en el estado actual."""
        gate = _CAPABILITIES.get(capability)
        if not gate:
            return True  # capacidad desconocida = permitida por defecto
        if self._state.value == "locked" and gate.required_state != NEXOBraceState.LOCKED:
            return False
        if self._state == NEXOBraceState.PARTIAL and gate.required_state == NEXOBraceState.FULL:
            return False
        # Verificar flag correspondiente
        if gate.required_flags:
            for flag in gate.required_flags:
                if not self.flags.get(flag, False):
                    return False
        # Verificar tier hardware
        tier_order = {"low": 0, "mid": 1, "high": 2, "gpu": 3}
        if tier_order.get(self.hardware_tier, 0) < tier_order.get(gate.min_hardware_tier, 0):
            return False
        # Verificar política
        if gate.required_policy_level == "allow" and self.policy_level != "allow":
            return False
        # Verificar consentimiento
        if gate.user_consent and not self.user_consent:
            return False
        return True

    def get_status(self) -> dict[str, Any]:
        return {
            "state": self._state.value,
            "hardware_tier": self.hardware_tier,
            "policy_level": self.policy_level,
            "user_consent": self.user_consent,
            "nexus_locked": self.nexus_locked,
            "capabilities": {
                name: {
                    "unlocked": self.is_unlocked(name),
                    "description": gate.description,
                    "required_state": gate.required_state.value,
                }
                for name, gate in _CAPABILITIES.items()
            },
        }


def build_nexo_brace(
    hardware_tier: str,
    flags: dict[str, bool],
    policy_level: str = "ask",
    user_consent: bool = False,
    nexus_locked: bool = True,
) -> NEXOBrace:
    return NEXOBrace(hardware_tier, flags, policy_level, user_consent, nexus_locked)


__all__ = [
    "NEXOBraceState",
    "CapabilityGate",
    "NEXOBrace",
    "build_nexo_brace",
]