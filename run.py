#!/usr/bin/env python3
"""Abril application entry point."""

from abril.config import Settings
from abril.web.server import serve


def main() -> None:
    settings = Settings.load()
    serve(settings)


if __name__ == "__main__":
    main()
