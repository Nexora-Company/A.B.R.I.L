"""Feature flags persisted under the local data directory.

Flags exist so every new capability can be disabled without touching the
working code path. Missing or malformed values fall back to these defaults,
which reproduce the behaviour of A.B.R.I.L before the roadmap work started.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path


@dataclass
class FeatureFlags:
    """Toggleable capabilities. All defaults preserve current behaviour."""

    # Fase 1: núcleo y blindaje
    routing: bool = False
    hardware_profiles: bool = False
    prompt_cache: bool = False
    policy: bool = False
    local_strict: bool = True
    untrusted_content: bool = False
    personality_templates: bool = False
    predictive: bool = False
    sqlite_memory: bool = False

    # Fase 2: multitarea y nube
    background_tasks: bool = False
    multi_model: bool = False
    web_search: bool = False
    cloud_providers: bool = False
    quota_failover: bool = False

    # Fase 3: experiencia
    voice: bool = False
    protocols: bool = False
    proactive: bool = False
    integrations: bool = False
    hud: bool = False

    @classmethod
    def load(cls, path: Path) -> "FeatureFlags":
        """Load flags from ``path``; return defaults when absent or invalid."""
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureFlags":
        """Build flags ignoring unknown keys and non-boolean values."""
        known = {field.name for field in fields(cls)}
        values = {
            key: value
            for key, value in data.items()
            if key in known and isinstance(value, bool)
        }
        return cls(**values)

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)

    def save(self, path: Path) -> None:
        """Write flags atomically so a crash never leaves a partial file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    def set(self, name: str, value: bool) -> None:
        if name not in self.to_dict():
            raise KeyError(name)
        setattr(self, name, bool(value))

    def reset(self) -> None:
        for field in fields(self):
            setattr(self, field.name, field.default)

    @property
    def names(self) -> list[str]:
        return [field.name for field in fields(self)]
