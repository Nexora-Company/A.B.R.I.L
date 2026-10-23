"""Shared terminal UI contract.

The concrete terminal renderer lives in ``main.py`` today. Modules that only
need to print or animate a spinner depend on this Protocol instead of importing
``main``, which avoids circular imports while the UI is migrated.
"""

from __future__ import annotations

from typing import Protocol


class UIPort(Protocol):
    def print_system(self, text: str) -> None: ...

    def print_warning(self, text: str) -> None: ...

    def print_error(self, text: str) -> None: ...

    def print_success(self, text: str) -> None: ...

    def print_assistant(self, text: str) -> None: ...

    def start_typing(self) -> None: ...

    def stop_typing(self) -> None: ...
