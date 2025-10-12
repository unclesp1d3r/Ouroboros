---
inclusion: always
---

## Rule Summary

This project uses [`uv`](mdc:https:/github.com/astral-sh/uv) for all Python dependency management.

## DO NOT

- Manually edit `pyproject.toml` or `poetry.lock`
- Add or remove dependencies inline without using the proper command

## DO

- Use `uv add PACKAGE_NAME` to install packages
- Use `uv add --dev PACKAGE_NAME` for dev dependencies
- Use `uv remove PACKAGE_NAME` to uninstall

## Cursor Instructions

- Never suggest editing `[tool.poetry.dependencies]` or `[tool.poetry.dev-dependencies]` directly.
- If asked to install something, always recommend the appropriate `uv add` command.
- Do not generate or propose edits to dependency sections without confirmation from the user.

### Additional Guidelines

- Do NOT generate or use `requirements.txt`.
- Never edit `poetry.lock` manually — always use `uv sync`.
- All dependency changes must be reproducible with `just ci-check`.
