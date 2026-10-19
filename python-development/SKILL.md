---
name: python-development
description: "Guide Python development with greenfield defaults and brownfield flexibility. Apply when writing, maintaining, or reviewing Python code to ensure consistency with modern tooling (uv, ruff, ty, pytest, pre-commit) and patterns (CLI separation, type safety, error handling)."
allowed-tools: "Read, Grep, Glob, Edit, Write"
argument-hint: ""
user-invocable: false
---

# Python Development

Personal tooling defaults and non-obvious patterns. Generic Python knowledge is assumed.

## Supporting Files

- **[tooling.md](tooling.md)** — read when setting up a greenfield project: `pyproject.toml`, `Makefile`,
  `.pre-commit-config.yaml` templates (use them verbatim)
- **[patterns.md](patterns.md)** — read when structuring a CLI, defining exceptions, or writing tests that touch
  module-level state

## Toolchain

`uv` (`uv sync`, `uv run`), `ruff` (check + format), `ty` (or `mypy` if the repo uses it), `pytest`, `pre-commit`;
`make` targets `install`, `test`, `lint`, `fmt`/`format`, `typecheck`, `check`. Older repos may use other tools
(e.g. `poetry`): read the `Makefile` first.

## Greenfield Defaults

- Python 3.12 (`.python-version`), hatchling, `src/` layout with `cli.py`, `commands/`, `core/`; `tests/conftest.py`.
- Modern type hints on every function (`str | None`, `list[str]`, `collections.abc`), no `from __future__`.
- One-line docstring per function and module; no `Args:`/`Returns:` sections.
- Absolute imports only; `pathlib.Path` only; `@dataclass` for models with 2+ fields.
- Output via `typer.echo`; add Rich + logging only when a `--verbose` flag is requested.
- Config: `tomllib` + TOML file; Pydantic only for nested config needing validation. Env vars only for secrets or CI
  overrides.
- `__init__.py` empty, or just `__version__` when the CLI has `--version`.
- `TYPE_CHECKING` guard only after hitting a real circular import.
- Done when `make install && make check` passes and `pre-commit install` is enabled.

## Brownfield

Read the existing code and tooling first and match it; don't retrofit greenfield defaults or change tooling unless
asked.

- Keep the existing build system; missing → hatchling.
- Python ≤3.11 → keep it.
- Type checking: 80%+ hint coverage → `ty check`; less → `ruff check` only; none → tests only.
- Keep a flat `tests/` under ~50 tests.
- Refactor argparse/custom CLIs to Typer only when actively developing them.

## Review Checklist

### Blockers

- Bare `except:` or `except Exception` without re-raising
- Unused imports or dead code
- Hardcoded secrets

### Nits

- Missing type hints or docstrings; `os.path`; mutable default arguments
- Re-raise without `from e`; raising base `Exception` instead of a domain error
- Tests touching real filesystem or env without `tmp_path` / `monkeypatch`
- Module-level mutable state not isolated by an `autouse` fixture — see [patterns.md](patterns.md#testing)

When a blocker is found, grep for the same pattern across the codebase and report every instance.
