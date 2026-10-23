"""Bootstrap wiring tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from abril.app.bootstrap import build_core
from abril.config import Settings
from abril.services.actions import ActionsService
from tests.helpers import FakeProvider


@pytest.fixture(autouse=True)
def _isolate_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ActionsService, "_discover_apps", staticmethod(lambda: {}))
    monkeypatch.setattr(ActionsService, "_roots", staticmethod(lambda: {}))


def test_build_core_wires_services(settings: Settings, fake_provider: FakeProvider) -> None:
    core = build_core(settings=settings, provider=fake_provider)

    assert core.settings is settings
    assert core.provider is fake_provider
    assert core.chat.provider is fake_provider
    assert core.flags.local_strict is True
    assert core.flags.routing is False


def test_build_core_loads_flags_from_data_dir(settings: Settings, fake_provider: FakeProvider, tmp_path: Path) -> None:
    settings.config_file.write_text('{"routing": true}\n', encoding="utf-8")

    core = build_core(settings=settings, provider=fake_provider)

    assert core.flags.routing is True
