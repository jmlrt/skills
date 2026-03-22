---
name: python-development
description: Production patterns for Python projects - greenfield defaults + brownfield flexibility
allowed-tools: Read, Grep
---

# Python Development: Greenfield & Brownfield

Two-tier guidance: **Greenfield defaults for new projects** (consistent, modern), **Brownfield flexibility for legacy projects** (pragmatic, non-blocking).

**Python**: 3.12+ (greenfield default) | **Status**: Proven in clipmd, englog, spotfm

---

## Quick Start: New Project (Greenfield)?

Follow [greenfield defaults](#greenfield-defaults) to stay consistent with clipmd/englog:

```bash
# 1. Read the greenfield template
# 2. Copy pyproject.toml + Makefile + .pre-commit-config.yaml templates
# 3. Run: make install && make check
# Done.
```

**Or inheriting legacy code?** → Jump to [Brownfield Projects](#brownfield-projects)

---

## Greenfield Defaults

Use this **by default for all new projects**. These ensure consistency across clipmd and englog:

### Python Version
- **Minimum**: 3.12 (3.13 preferred if all dependencies support)
- **Pin in 2 places**:
  - `pyproject.toml`: `requires-python = ">=3.12"`
  - `.python-version`: `3.12` (for uv Python management)

### Build System
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Tooling Stack (Exact)
- **uv**: Package management (replaces pip/pipenv/poetry)
- **ruff**: Linting + formatting (line-length: 100)
- **ty**: Type checking (strict mode)
- **pytest**: Testing
- **pre-commit**: Git hooks
- **make**: Task automation

All specified in `pyproject.toml` under `[dependency-groups] dev = [...]`

### Project Structure
```
my-project/
├── src/
│   └── my_project/
│       ├── cli.py              (thin CLI wrapper)
│       ├── commands/           (command submodules)
│       │   └── example.py
│       └── core/               (pure business logic)
│           └── processor.py
├── tests/
│   ├── test_cli.py            (CLI interface tests)
│   └── test_processor.py       (core logic tests)
├── pyproject.toml
├── Makefile
├── .pre-commit-config.yaml
├── .python-version            (pin minor version)
└── README.md
```

### Use Cases (Flat or Structured Tests?)

**If CLI tool** (like englog, clipmd):
- All tests in `tests/` directory, flat structure
- Use `conftest.py` for shared fixtures
- No artificial unit/integration split (organize by concern, not by tier)

**If library** (like spotfm):
- No `cli.py` unless you offer a CLI too
- All tests in `tests/`, name by feature: `test_api.py`, `test_utils.py`
- Use fixtures for mocking external dependencies

See templates in [tooling.md](tooling.md).

---

## Brownfield Projects

Working with legacy code? **Don't retrofit the greenfield defaults.** Instead, make **pragmatic choices**:

### Decision Tree

**Q: Does the project already use a build system?**
- ✅ Yes → Keep it (setup.cfg, Poetry, etc.)
- ❌ No → Migrate to hatchling (one-time effort worth it)

**Q: Which Python version?**
- 3.11 or older → Keep it, update when dependencies support it
- 3.12+ → Align with greenfield default (3.12+)

**Q: Which CLI framework?**
- Click (clipmd pattern) → Already greenfield-aligned
- Typer (englog pattern) → Already greenfield-aligned
- argparse or custom → Refactor only if actively developing
- No CLI (library) → Leave as-is

**Q: Does code use type hints?**
- 80%+ coverage → Run `ty check --strict`
- <80% coverage → Use `ruff check` for lint only, don't enforce `ty`
- 0% coverage (like spotfm) → Run tests only, skip type checking

**Q: Test organization?**
- Complex project with 50+ tests → Consider unit/integration split
- <50 tests → Keep flat `test_*.py`

### Brownfield Minimal Setup

If working on legacy code, ensure **just these**:

```makefile
make install    # Install dependencies
make test       # Run tests
make lint       # Check code style
make check      # All of above
```

Don't force the full greenfield stack if:
- It's unmaintained code you're patching
- The project was greenfield when started but has diverged
- You're fixing a bug in 30 minutes and moving on

---

## Templates

See [tooling.md](tooling.md) for:
- **Greenfield pyproject.toml** (hatchling + dependency-groups)
- **Greenfield Makefile** (all targets)
- **Greenfield .pre-commit-config.yaml** (hooks)
- **Brownfield quick Makefile** (minimal targets)

See [cli-patterns.md](cli-patterns.md) for:
- Separation of concerns (CLI thin wrapper)
- TYPE_CHECKING guard pattern (for circular imports)
- Testing both core logic + CLI

See [error-handling.md](error-handling.md) for:
- Result dataclasses (expected failures)
- Exception hierarchy (bugs)

---

## When to Deviate from Greenfield Defaults

**Don't use greenfield defaults if**:
- Project dependencies don't support Python 3.12+
- Team standardized on different tooling (respect existing choice)
- Inheriting unmaintained brownfield code (minimize changes)

**Do use greenfield defaults if**:
- Starting a new project
- Modernizing an active project
- Adding new modules to existing greenfield project

---

## Checklist: New Greenfield Project

- [ ] Python 3.12+ in `.python-version` and `pyproject.toml`
- [ ] hatchling build system configured
- [ ] Makefile with: install, test, test-cov, lint, format, check, clean
- [ ] pyproject.toml with `[dependency-groups] dev = [...]` (not `[project.optional-dependencies]`)
- [ ] `.pre-commit-config.yaml` with ruff + ty hooks
- [ ] `src/my_project/` structure with `cli.py`, `commands/`, `core/`
- [ ] `tests/` with `conftest.py` and `test_*.py` files
- [ ] Run `make install && make check` before first commit
- [ ] `pre-commit install` to enable git hooks

---

**Python**: 3.12+ (greenfield) | **Status**: Reference
