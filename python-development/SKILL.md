---
name: python-development
description: Production patterns for modern Python development (uv, ruff, ty, make, pre-commit)
allowed-tools: Read, Grep
---

# Python Development Patterns

Reference guide for production Python development: tooling, architecture, error handling, and testing patterns.

**Python**: 3.11+

---

## Use Cases

### I'm building a new CLI tool
1. Read [Separation of Concerns](#separation-of-concerns)
2. Read [Type Checking & Guards](#type-checking--guards)
3. Copy templates from [tooling.md](tooling.md)
4. Run `make dev` to bootstrap

### I'm fixing circular imports
1. Read [Type Checking & Guards](#type-checking--guards)
2. Apply [CLI Patterns](#cli-patterns)
3. Run `make check` (ty will catch remaining issues)

### I'm improving code quality
1. Read [Test Organization](#test-organization)
2. Read [tooling.md](tooling.md) for complete setup
3. Run `make check` before every commit

### I'm setting up tooling
1. Follow [tooling.md](tooling.md) for uv, ruff, ty, make, pre-commit
2. Copy templates: pyproject.toml, Makefile, .pre-commit-config.yaml
3. Run `make dev && make check`

---

## Core Patterns Overview

### Separation of Concerns

Keep CLI parsing separate from business logic:

```
CLI Module (50-150 lines)     Core Module (Pure Logic)
  • Parse Click args      →     • No CLI dependencies
  • Call core function    ←     • Returns dataclass
  • Display with Rich         • 100% testable
```

**Key principle**: Test core logic without mocking Click.

**Result**: 2x less total code, 12x more reusable, 100% testable.

### Type Checking & Guards

Break circular imports using `TYPE_CHECKING`:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module_b import Config  # Type checking only

def process(config: "Config") -> None:  # String reference
    # No circular import at runtime
    pass
```

**Benefits**: Full type safety, IDE autocomplete, zero runtime overhead.

### Error Handling

Use result dataclasses for expected failures:

```python
@dataclass
class ProcessResult:
    success: bool
    data: dict | None = None
    error: str | None = None

def process_item(item: str) -> ProcessResult:
    try:
        return ProcessResult(success=True, data={"item": item})
    except ValueError as e:
        return ProcessResult(success=False, error=str(e))
```

**Rule**: Results for expected failures, exceptions for bugs.

### CLI Patterns

Extract context to solve circular imports:

```python
# src/my_project/context.py
class Context:
    def __init__(self, config: Config | None = None):
        self.config = config

# Commands import from context, not cli.py
# cli.py imports from context, not commands
# → No circular dependency
```

### Test Organization

Organize tests by type:

```
tests/
├── unit/          # Core logic tests
├── cli/           # Command interface tests
└── integration/   # Workflow tests
```

High coverage enforced by `make test-cov`.

---

## Tooling Stack

All details in [tooling.md](tooling.md):

- **uv** - Package management, builds, publishing
- **ruff** - Linting & formatting (unified)
- **ty** - Type checking (Astral, fast)
- **make** - Development automation
- **pre-commit** - Git hooks framework

Master target: `make check` (runs lint + typecheck + test)

---

## Quick Start

```bash
# Read the complete guide
cat tooling.md

# Copy templates and set up
make dev                 # Install dependencies
make check              # Run all quality checks
pre-commit install      # Install git hooks
```

---

## Core Principles

1. **Type Safety First** - Every function has type hints, ty catches errors
2. **Separation of Concerns** - CLI thin wrappers (50-150 lines) + pure core logic
3. **Test-Driven Quality** - High coverage target, enforced by `make test-cov`
4. **Automated Enforcement** - `make check` + pre-commit + CI
5. **Configuration Over Convention** - All choices in config files

---

## Key Files

| File | Purpose |
|------|---------|
| [tooling.md](tooling.md) | Complete setup guide (uv, ruff, ty, make, pre-commit) |
| [type-checking-guards.md](type-checking-guards.md) | Solving circular imports |
| [cli-patterns.md](cli-patterns.md) | Architecture patterns |
| [error-handling.md](error-handling.md) | Exception & result patterns |

---

**Python**: 3.11+ | **Status**: Reference
