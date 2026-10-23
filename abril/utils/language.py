"""Programming-language detection shared by the terminal commands."""

from __future__ import annotations

from pathlib import Path

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "jsx",
    ".tsx": "tsx",
    ".html": "html",
    ".css": "css",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".json": "json",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".txt": "text",
    ".csv": "csv",
    ".log": "log",
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "conf",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".dart": "dart",
    ".lua": "lua",
    ".r": "r",
    ".sql": "sql",
    ".dockerfile": "dockerfile",
    ".gitignore": "gitignore",
    ".env": "env",
}


def detect_language(path: str) -> str:
    """Return a language name for ``path`` based on its suffix."""
    return LANGUAGE_MAP.get(Path(path).suffix.lower(), "text")
