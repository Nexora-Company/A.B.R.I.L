"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from abril.config import PROJECT_ROOT, Settings
from abril.services.actions import ActionsService
from abril.services.chat import ChatService
from tests.helpers import FakeProvider, RecordingUI


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        project_root=PROJECT_ROOT,
        ollama_url="http://127.0.0.1:11434",
        ollama_model="fake-model",
        data_dir=tmp_path,
    )


@pytest.fixture
def chat(settings: Settings, fake_provider: FakeProvider) -> ChatService:
    return ChatService(fake_provider, settings)


@pytest.fixture
def actions(settings: Settings, chat: ChatService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ActionsService:
    monkeypatch.setattr(
        ActionsService,
        "_discover_apps",
        staticmethod(lambda: {"discord.desktop": {"id": "discord.desktop", "name": "Discord"}}),
    )
    monkeypatch.setattr(ActionsService, "_roots", staticmethod(lambda: {"Home": tmp_path}))
    return ActionsService(settings, chat)


@pytest.fixture
def ui() -> RecordingUI:
    return RecordingUI()
