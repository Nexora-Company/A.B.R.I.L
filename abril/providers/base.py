"""Shared provider interface and normalized provider errors."""

from __future__ import annotations

from typing import Protocol


class ProviderError(RuntimeError):
    """An expected error while contacting or using an AI provider."""


class AIProvider(Protocol):
    name: str
    model: str

    def complete(self, messages: list[dict[str, str]]) -> str: ...

    def status(self) -> dict[str, str | bool]: ...
