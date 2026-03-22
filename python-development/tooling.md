# Python Tooling: Greenfield Templates

Copy-paste templates for new projects. For brownfield guidance, see SKILL.md.

---

## Greenfield pyproject.toml

Use this as your starting template for new projects:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-project"
version = "0.1.0"
description = "Your project description"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.12"
authors = [{name = "Your Name", email = "you@example.com"}]

dependencies = [
    # Add your runtime dependencies here
    "typer>=0.12",       # if building a CLI
    "rich>=13.9",        # for console output (optional, only if --verbose flag needed)
]

[project.scripts]
# Uncomment if you have a CLI
# my-project = "my_project.cli:main"

[dependency-groups]
dev = [
    "pre-commit>=4.0.0",
    "pytest>=9.0.0",
    "pytest-cov>=7.0.0",
    "ruff>=0.14.0",
    "ty>=0.0.1a0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "--cov=my_project --cov-report=term-missing:skip-covered --cov-fail-under=80"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]  # PEP 8, Pyflakes, isort, warnings
ignore = ["E501"]               # Line too long (handled by formatter)

[tool.ruff.lint.isort]
known-first-party = ["my_project"]

[tool.hatch.build.targets.wheel]
packages = ["src/my_project"]
```

---

## Greenfield Makefile

```makefile
.PHONY: help install test test-v test-cov lint format fix check typecheck clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv sync --all-extras
	uv run pre-commit install

test:  ## Run tests
	uv run pytest -q

test-v:  ## Run tests (verbose)
	uv run pytest -v

test-cov:  ## Run tests with coverage report
	uv run pytest --cov=my_project --cov-report=term-missing

lint:  ## Lint and check formatting
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:  ## Auto-format code
	uv run ruff format src/ tests/

fix:  ## Auto-fix all issues
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

typecheck:  ## Type check with strict mode
	uv run ty check src/

check:  lint typecheck test  ## Run all checks (lint + typecheck + test)

clean:  ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .ruff_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

---

## Greenfield .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/astral-sh/ty-pre-commit
    rev: v0.0.1a0
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

## Greenfield Setup (First Time)

```bash
# Create .python-version file
echo "3.12" > .python-version

# Install dependencies
make install

# Run all checks
make check

# You're ready
git add .
git commit -m "Initial project setup"
```

---

## Brownfield: Minimal Makefile

If working with legacy code, use just this:

```makefile
.PHONY: help install test lint check clean

help:
	@echo "install - install dependencies"
	@echo "test - run tests"
	@echo "lint - run linter"
	@echo "check - lint + test"
	@echo "clean - remove artifacts"

install:
	pip install -e ".[dev]" || uv sync

test:
	pytest

lint:
	ruff check .

check: lint test

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

This works with any project structure.

