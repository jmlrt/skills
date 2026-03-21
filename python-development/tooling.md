# Python Development Tooling

Setup and configuration templates for modern Python development.

**Tools**: uv (package mgmt) | ruff (lint + format) | ty (type check) | make (automation) | pre-commit (git hooks)

**Master command**: `make check` (lint + typecheck + test)

---

## Key Commands

### uv
```bash
uv sync                          # Install from pyproject.toml
uv sync --all-extras             # Include all optional deps
uv run pytest                    # Run tests in venv
uv run ruff check src/           # Run linter in venv
uv build                         # Build distribution
uv publish                       # Publish to PyPI
```

### ruff
```bash
ruff check src/                  # Find violations
ruff check --fix src/            # Auto-fix
ruff format src/                 # Format code
```

### ty
```bash
ty check src/                    # Type check project
ty check --strict src/           # Strict mode
```

### make
```bash
make dev                         # Install dependencies
make check                       # Lint + typecheck + test
make test                        # Run tests only
make test-cov                    # Tests with coverage
```

### pre-commit
```bash
pre-commit install               # Install hooks
pre-commit run --all-files       # Run all hooks manually
pre-commit autoupdate            # Update hook versions
```

---

## pyproject.toml Template

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-project"
version = "0.1.0"
description = "My Python project"
requires-python = ">=3.11"
authors = [{name = "Your Name", email = "you@example.com"}]
license = {text = "MIT"}

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

[project.scripts]
my-cli = "my_project.cli:main"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["my_project"]

[tool.ty]
python_version = "3.11"
strict = true
exclude = ["tests/", "venv/"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=my_project --cov-report=term-missing:skip-covered --cov-fail-under=80"

[tool.coverage.run]
omit = ["*/tests/*"]
```

---

## Makefile Template

```makefile
.PHONY: dev check test test-cov format lint typecheck clean help

help:
	@echo "Available targets:"
	@echo "  make dev         Install dependencies"
	@echo "  make check       Lint + typecheck + test"
	@echo "  make test        Run tests only"
	@echo "  make test-cov    Tests with coverage"
	@echo "  make format      Auto-format code"
	@echo "  make lint        Run linter (no fix)"
	@echo "  make typecheck   Run type checker"

dev:
	uv sync --all-extras

check: lint typecheck test

test:
	uv run pytest

test-cov:
	uv run pytest --cov=my_project --cov-report=term-missing:skip-covered

lint:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

typecheck:
	uv run ty check src/

clean:
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
```

---

## .pre-commit-config.yaml Template

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/astral-sh/ty-pre-commit
    rev: v0.0.1a6
    hooks:
      - id: ty

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: bash -c 'uv run pytest'
        language: system
        types: [python]
        pass_filenames: false
        stages: [commit]
```

---

## Test Directory Structure

```
tests/
├── unit/
│   ├── test_processor.py    # Core logic, no I/O
│   ├── test_parser.py
│   └── conftest.py          # unit test fixtures
├── cli/
│   ├── test_extract_cmd.py  # Click command interface
│   └── conftest.py          # CLI fixtures (CliRunner, etc.)
└── integration/
    ├── test_workflow.py     # Full E2E
    └── fixtures/
        ├── sample_input.md
        └── expected_output.txt
```

Coverage target: 80%+ (enforced by pyproject.toml).

---

## Installation

See official docs for each tool:
- uv: https://docs.astral.sh/uv/getting-started/
- ruff: https://docs.astral.sh/ruff/
- ty: https://github.com/astral-sh/ty
- pre-commit: https://pre-commit.com/

Then run: `make dev && make check`

