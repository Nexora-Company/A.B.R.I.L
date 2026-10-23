"""Feature flag persistence and safety tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from abril.app.flags import FeatureFlags


def test_defaults_preserve_current_behaviour(tmp_path: Path) -> None:
    flags = FeatureFlags.load(tmp_path / "config.json")

    assert flags.local_strict is True
    assert flags.routing is False
    assert flags.policy is False
    assert flags.cloud_providers is False


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    flags = FeatureFlags()
    flags.set("routing", True)
    flags.set("policy", True)
    flags.save(path)

    loaded = FeatureFlags.load(path)

    assert loaded.routing is True
    assert loaded.policy is True
    assert loaded.local_strict is True


def test_malformed_file_falls_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{no-es-json", encoding="utf-8")

    flags = FeatureFlags.load(path)

    assert flags.local_strict is True
    assert flags.routing is False


def test_unknown_and_non_boolean_values_are_ignored() -> None:
    flags = FeatureFlags.from_dict({"routing": "sí", "inventado": True, "policy": True})

    assert flags.routing is False
    assert flags.policy is True
    assert not hasattr(flags, "inventado")


def test_set_unknown_flag_raises() -> None:
    with pytest.raises(KeyError):
        FeatureFlags().set("no-existe", True)


def test_reset_restores_defaults() -> None:
    flags = FeatureFlags()
    flags.set("routing", True)

    flags.reset()

    assert flags.routing is False
    assert flags.local_strict is True
