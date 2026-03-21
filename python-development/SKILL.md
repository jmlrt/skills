---
name: python-development
description: Production patterns for modern Python development (uv, ruff, ty, make, pre-commit)
allowed-tools: Read, Grep
---

# Python Development Patterns

Reference guide: tooling, architecture, error handling, testing.

**Python**: 3.11+ | **Status**: Lean reference

---

## Quick Navigation

**Building a new CLI tool?**
1. Read [cli-patterns.md](cli-patterns.md) (separation of concerns + type checking)
2. Read [error-handling.md](error-handling.md) (result dataclasses)
3. Copy templates from [tooling.md](tooling.md)
4. Run `make dev && make check`

**Fixing circular imports?**
→ Read [cli-patterns.md#type-checking-guards](cli-patterns.md)

**Setting up tooling?**
→ Follow [tooling.md](tooling.md)

**Improving code quality?**
→ Run `make check` before every commit

---

## Core Patterns (One Sentence Each)

**Separation of Concerns**: CLI parsing thin wrapper (50-150 lines) + pure core logic (testable without mocking Click).

**Type Checking**: Use `TYPE_CHECKING` guard to break circular imports without runtime overhead.

**Error Handling**: Result dataclasses for expected failures (user input, file not found); exceptions for bugs.

---

## Tooling Stack

All handled by `make check`:

- **uv** - Package management, builds, publishing
- **ruff** - Linting + formatting (unified)
- **ty** - Type checking (strict mode)
- **make** - Task automation
- **pre-commit** - Git hooks

See [tooling.md](tooling.md) for templates and commands.

---

## Key Files

| File | What's In It |
|------|-------------|
| [tooling.md](tooling.md) | Templates (pyproject.toml, Makefile, .pre-commit-config.yaml) + key commands |
| [cli-patterns.md](cli-patterns.md) | Separation of concerns + TYPE_CHECKING guard pattern |
| [error-handling.md](error-handling.md) | Result dataclasses + exception hierarchy |

