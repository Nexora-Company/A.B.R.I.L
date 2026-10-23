# Contributing to A.B.R.I.L

Thanks for wanting to improve A.B.R.I.L. This document covers workflow, standards and rules.

## Reporting bugs and proposing features

- Search existing issues first.
- For large changes, open an issue before coding.
- Bugs: include version (`abril/__init__.py`), Python version, OS, provider/model, minimal reproduction, expected vs. actual, relevant logs (no API keys).

## Development environment

Detected from the repo: no `pyproject.toml` or `requirements.txt` (stdlib only).

- Minimum gate: `python3 -m py_compile main.py abril/**/*.py`
- Optional: `mypy` (`python3 -m mypy main.py abril/`), `ruff` (`ruff check`, `ruff format`).
- Style: 4 spaces, 88 columns, absolute imports from `abril.`, Google-style docstrings.

`{{TODO: add a pyproject.toml or requirements-dev.txt to pin tooling}}`

## Code style

- Type hints on all public functions.
- `@dataclass(frozen=True)` for immutable settings/DTOs.
- `typing.Protocol` for interfaces (providers).
- Stdlib first: no external dependencies without discussion.
- Specific exceptions; chain with `raise ... from err`.

## Commit convention

Conventional Commits. Scopes: `providers`, `services`, `config`, `chat`, `terminal`, `memory`, `actions`.

```text
feat(providers): add Anthropic provider
fix(chat): avoid index error when truncating history
```

Rules: one logical change per commit; explicit paths (no `git add .`); imperative, lowercase, max 72 chars first line; Spanish messages.

## Branch and PR flow

Branches: `feature/`, `fix/`, `refactor/`, `docs/`, `style/`, `build/`, `ci/`, `test/` + kebab-case.

PR must include: Conventional Commits title, description (what/why/how tested), issue reference, checklist.

## PR checklist

- [ ] `main` updated and rebased/merged
- [ ] Atomic commits + Conventional Commits
- [ ] `python3 -m py_compile main.py abril/**/*.py` passes
- [ ] `mypy` and `ruff` pass (if used)
- [ ] Docstrings updated (Google style)
- [ ] README updated if config/usage/architecture changed
- [ ] No `.env`, `__pycache__`, `*.pyc`, logs in diff
- [ ] PR explains what and why

## CLA

Contributors must sign the CLA before a PR is accepted. This grants Nexora the rights needed to offer the commercial license alongside the AGPL edition.

## AI-generated code

Allowed if the contributor understands, reviews and takes responsibility for it.

## Questions

Use GitHub Discussions for design/architecture. Discord `saaarmyx` or @saaarmyx on GitHub for quick questions.