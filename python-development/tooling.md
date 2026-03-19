# Python Development Tooling

Complete reference for modern Python development: uv, ruff, ty, make, pre-commit.

**Why these tools**: Each has one responsibility, works independently, proven in production.

---

## Table of Contents

1. [Tool Selection](#tool-selection)
2. [uv: Package Management](#uv-package-management)
3. [ruff: Linting & Formatting](#ruff-linting--formatting)
4. [ty: Type Checking](#ty-type-checking)
5. [make: Automation](#make-automation)
6. [pre-commit: Git Hooks](#pre-commit-git-hooks)
7. [Configuration Templates](#configuration-templates)
8. [Development Workflow](#development-workflow)
9. [Integration Flow](#integration-flow)
10. [Troubleshooting](#troubleshooting)

---

## Tool Selection

| Tool | Purpose | Why? |
|------|---------|------|
| **uv** | Package mgmt + builds + publishing | Faster than pip, Astral (ruff creators) |
| **ruff** | Linting + formatting (unified) | Replaces black, isort, flake8 - 100x faster |
| **ty** | Type checking | Faster than mypy, Astral |
| **make** | Task automation | Universal, portable, simple |
| **pre-commit** | Git hooks | Prevents bad commits, standard in OSS |

**Principle**: Unified Tooling - each tool handles one job, can be replaced independently.

---

## uv: Package Management

### Installation

```bash
# macOS
brew install uv

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

### Key Commands

```bash
# Setup
uv sync                          # Install from pyproject.toml
uv sync --all-extras             # Include all optional deps

# Running in venv
uv run pytest                    # Run tests in project venv
uv run ruff check src/           # Run linter in venv
uv run my-cli --help             # Run CLI tool in venv

# Building & publishing
uv build                         # Create dist/project-0.1.0.tar.gz + .whl
uv publish                       # Upload to PyPI

# Python management
uv python list                   # List installed Python versions
uv python install 3.13           # Install specific Python version
uv python pin 3.13               # Pin project to Python 3.13
```

### pyproject.toml Setup

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "My Python project"
requires-python = ">=3.13"

dependencies = [
    "click>=8.1",
    "pydantic>=2.10",
    "rich>=13.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-cov>=6.0",
    "ruff>=0.9",
    "ty>=0.0.1a6",
    "pre-commit>=4.0",
]
all = ["my-project[dev]"]

[project.scripts]
my-cli = "my_project.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### uv.lock

Commit `uv.lock` to git for reproducible builds:

```bash
uv sync                          # Uses exact versions from lock
# ... edit pyproject.toml ...
uv sync                          # Updates lock and reinstalls
git add uv.lock && git commit
```

**Benefits**: Single tool, 10-100x faster, deterministic builds, built-in Python management.

---

## ruff: Linting & Formatting

### Installation

```bash
uv add --group dev ruff>=0.9
```

### Key Commands

```bash
ruff check src/                  # Find violations
ruff check --fix src/            # Auto-fix violations
ruff format src/                 # Auto-format code
ruff format --check src/         # Verify formatting (no changes)
```

### Configuration

```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = [
    "E", "W",    # pycodestyle
    "F",         # Pyflakes
    "I",         # isort
    "B",         # flake8-bugbear
    "C4",        # comprehensions
    "UP",        # pyupgrade
    "ARG",       # unused args
    "SIM",       # simplify
]
ignore = ["E501"]  # Line too long (formatter handles)

[tool.ruff.lint.isort]
known-first-party = ["my_project"]
```

### Rule Reference

| Rule | Purpose |
|------|---------|
| **E/W** | PEP 8 compliance |
| **F** | Obvious bugs (unused imports, undefined vars) |
| **I** | Import sorting |
| **B** | Common mistakes (mutable defaults, bare except) |
| **C4** | Modern syntax (comprehensions) |
| **UP** | Python syntax updates (Set[int] → set[int]) |
| **ARG** | Unused function arguments |
| **SIM** | Code simplification |

### Common Fixes

```python
# Remove unused imports
# ❌ import sys
# ✅ (delete it)

# Use TYPE_CHECKING for type hints
# ❌ from module import Type
# ✅ from typing import TYPE_CHECKING
#    if TYPE_CHECKING:
#        from module import Type

# Fix mutable defaults
# ❌ def func(items={}):
# ✅ def func(items=None):
#        if items is None:
#            items = {}

# Sort imports
# ❌ from z_mod import x; from a_mod import y
# ✅ from a_mod import y; from z_mod import x
```

---

## ty: Type Checking

### Installation

```bash
uv add --group dev ty>=0.0.1a6
```

### Key Commands

```bash
uv run ty check src/             # Type check source only
uv run ty check src/module.py    # Check specific file
```

### Configuration

No setup needed! ty uses `requires-python` from pyproject.toml.

Optional: Create `ty.toml`

```toml
[tool.ty]
strict = true                    # Strict mode (recommended)
include = ["src/"]               # Directories to check
exclude = ["tests/", ".venv/"]   # Skip directories
```

### Type Hints Best Practices

```python
from __future__ import annotations  # PEP 563
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_project.config import Config

def extract_metadata(
    path: Path,
    config: Config,  # No quotes needed with __future__ annotations
    max_chars: int = 150,
) -> dict:
    """Extract metadata.

    Args:
        path: Path to file.
        config: Configuration.
        max_chars: Max description length.

    Returns:
        Dictionary with extracted data.
    """
    pass
```

**Key pattern**: Use TYPE_CHECKING guards to avoid circular imports while maintaining full type safety.

---

## make: Automation

### Why Make?

- ✅ Portable (macOS, Linux, Windows WSL)
- ✅ Universal (every developer knows make)
- ✅ Simple syntax
- ✅ Dependency tracking
- ✅ No magic

### Makefile Template

```makefile
.PHONY: help install dev lint format typecheck test test-cov check clean build publish

help:
	@echo "Available targets:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Install all dependencies (including dev)"
	@echo "  make lint       - Check code style"
	@echo "  make format     - Auto-format code"
	@echo "  make typecheck  - Check types"
	@echo "  make test       - Run tests"
	@echo "  make test-cov   - Run tests with coverage (89% required)"
	@echo "  make check      - Run all checks (lint → typecheck → test-cov)"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make build      - Build distribution"
	@echo "  make publish    - Publish to PyPI"

install:
	uv sync

dev:
	uv sync --all-extras

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

typecheck:
	uv run ty check src

test:
	uv run pytest

test-cov:
	uv run pytest --cov=my_project --cov-report=term-missing --cov-fail-under=89

check: lint typecheck test-cov

clean:
	rm -rf dist build *.egg-info .pytest_cache __pycache__ .ruff_cache .coverage

build: clean
	uv build

publish: build
	uv publish
```

### Common Targets

| Target | Purpose |
|--------|---------|
| `make dev` | Install all dependencies |
| `make format` | Auto-format code |
| `make lint` | Check violations |
| `make typecheck` | Type check |
| `make test-cov` | Tests + coverage |
| `make check` | **All checks (use before commit)** |
| `make clean` | Remove artifacts |
| `make build` | Create distribution |
| `make publish` | Upload to PyPI |

### Running Targets

```bash
make check                       # All checks
make check -v                    # Verbose output
make check -n                    # Dry run
```

---

## pre-commit: Git Hooks

### Installation

```bash
uv add --group dev pre-commit>=4.0

# Install hooks in repo
pre-commit install
```

### Configuration: .pre-commit-config.yaml

```yaml
default_language_version:
  python: python3.13

repos:
  # Standard file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']

  # Ruff
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.13
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  # Type checking
  - repo: local
    hooks:
      - id: ty-check
        name: type check
        entry: uv run ty check src
        language: system
        types: [python]
        pass_filenames: false
```

### Hook Execution Flow

```
git commit -m "my change"
    ↓
1. trailing-whitespace (auto-fix)
2. end-of-file-fixer (auto-fix)
3. check-yaml/toml (fails if invalid)
4. ruff-check --fix (auto-fix)
5. ruff-format (auto-format)
6. ty-check (type check, fails if errors)
    ↓
IF ALL PASS: commit proceeds
IF ANY FAILS: commit blocked, developer fixes
```

### Common Workflow

```bash
git add src/new_module.py
git commit -m "feat: add new module"
# pre-commit runs automatically
# → If violations, commit blocked
# → Developer fixes
# → git add . && git commit (retry)
```

### Updating Hooks

```bash
pre-commit autoupdate              # Update to latest versions
pre-commit run --all-files         # Run on all files
pre-commit run ruff-check --all-files  # Run specific hook
```

---

## Configuration Templates

### Complete pyproject.toml

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "My Python project"
readme = "README.md"
license = "MIT"
requires-python = ">=3.13"
authors = [{ name = "Your Name", email = "you@example.com" }]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]

dependencies = [
    "click>=8.1",
    "pydantic>=2.10",
    "rich>=13.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-cov>=6.0",
    "ruff>=0.9",
    "ty>=0.0.1a6",
    "pre-commit>=4.0",
]
all = ["my-project[dev]"]

[project.scripts]
my-cli = "my_project.cli:main"

[project.urls]
Homepage = "https://github.com/username/my-project"
Repository = "https://github.com/username/my-project"
Issues = "https://github.com/username/my-project/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Ruff
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["my_project"]

# Pytest
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"

# Coverage
[tool.coverage.run]
source = ["src/my_project"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
fail_under = 89
```

---

## Development Workflow

### Complete Workflow

```bash
# 1. Initial setup
git clone <repo>
cd my-project
make dev

# 2. Make changes
# ... edit src/ and tests/ ...

# 3. Check quality
make format                      # Auto-fix formatting
make check                       # All checks (required)

# 4. Commit
git add .
git commit -m "feat: add new feature"
# pre-commit runs automatically

# 5. Push & PR
git push origin feature-branch
# GitHub Actions CI runs make check
```

### Quick Quality Check

```bash
# Just formatting
make format

# Full quality gate
make check                       # 2-5 min
```

### Test Organization

```
tests/
├── unit/          # Core module tests
│   ├── test_config.py
│   ├── test_cache.py
│   └── test_processor.py
├── cli/           # Command tests
│   ├── test_extract_cmd.py
│   └── test_move_cmd.py
├── integration/   # Workflow tests
│   └── test_workflows.py
├── fixtures/      # Test data
│   └── sample-vault/
└── conftest.py    # Shared fixtures
```

### Coverage Target

```bash
make test-cov      # Fails if < 89%
uv run pytest --cov --cov-report=html  # Open htmlcov/index.html
```

---

## Integration Flow

### Complete Quality Pipeline

```
┌─────────────────────────────────────────┐
│      Developer: make format             │
│   (ruff auto-fixes formatting)          │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│      Developer: make check              │
│  1. ruff check (linting)                │
│  2. ty check (type checking)            │
│  3. pytest --cov (testing + coverage)   │
└────────────────┬────────────────────────┘
                 ↓
         (pass? continue)
                 ↓
┌─────────────────────────────────────────┐
│    Developer: git commit                │
│      (pre-commit hooks run)             │
│  1. trailing-whitespace (auto-fix)      │
│  2. end-of-file-fixer (auto-fix)        │
│  3. check-yaml, check-toml              │
│  4. ruff-check --fix (auto-fix)         │
│  5. ruff-format (auto-format)           │
│  6. ty-check (type check)               │
└────────────────┬────────────────────────┘
                 ↓
         (violations?
          → developer fixes
          → git add . && git commit)
                 ↓
┌─────────────────────────────────────────┐
│    GitHub Actions CI                    │
│  1. Checkout code                       │
│  2. Install uv and Python (3.13, 3.14)  │
│  3. Run: make check (identical)         │
│  4. Build distribution: uv build        │
│  5. Publish coverage report             │
└────────────────┬────────────────────────┘
                 ↓
         (all pass? can merge)
```

### Enforcement Points

| Point | Tool | Action |
|-------|------|--------|
| **Local pre-commit** | ruff + checks | Commit blocked if violations |
| **make check** | ruff + ty + pytest | Must pass before committing |
| **Coverage gate** | pytest --cov-fail-under=89 | Tests fail if < 89% |
| **CI Pipeline** | GitHub Actions | PR blocked if CI fails |
| **Branch protection** | GitHub | Can't merge without passing CI |

---

## Troubleshooting

### Pre-commit failed, but I need to commit

```bash
# Fix the violations shown
# Stage the fixes
git add .
# Retry commit
git commit
```

### Test coverage too low

```bash
uv run pytest --cov --cov-report=term-missing
# Shows which lines aren't covered
# Write more tests or update target in Makefile
```

### Type checking errors

```bash
# Option 1: Fix the error
# Option 2: Use TYPE_CHECKING guard to avoid import
# Option 3: Use string forward reference (last resort)
value = unsafe_cast()  # type: ignore
```

### Import sorting issues

```bash
make format    # ruff format fixes import order
```

### Dependencies out of date

```bash
uv sync --upgrade
git add uv.lock && git commit -m "chore: update dependencies"
```

### Outdated hooks

```bash
pre-commit autoupdate
pre-commit run --all-files
git add .pre-commit-config.yaml && git commit
```

---

## Quick Reference

```bash
# Setup
make dev                         # Install everything

# Before commit
make format                      # Fix formatting
make check                       # Run all checks (required)

# Running tests
uv run pytest                    # All tests
uv run pytest tests/unit         # Unit tests only
uv run pytest -k test_name       # Specific test
uv run pytest --cov              # With coverage

# Running CLI
uv run my-cli --help            # Show help
uv run my-cli command           # Run command

# Git workflow
git add .
git commit -m "feat: description"  # pre-commit runs automatically
git push

# Building
make clean                       # Remove artifacts
make build                       # Create distribution
make publish                     # Upload to PyPI
```

---

## Summary

This tooling stack provides:

✅ **Unified Code Quality**: Single `make check` runs all checks
✅ **Automatic Enforcement**: pre-commit prevents bad commits
✅ **Type Safety**: ty catches errors before runtime
✅ **Fast Iteration**: ruff auto-fixes most issues
✅ **Reproducible Builds**: uv.lock ensures identical dependencies
✅ **Cross-Platform**: Works on macOS, Linux, Windows
✅ **No Configuration Complexity**: Sensible defaults, minimal setup

When all tools work together, you get a **robust, automated workflow** that catches issues before they reach main branch.
