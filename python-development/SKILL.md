---
name: python-development
description: "Guide Python development with greenfield defaults and brownfield flexibility. Apply when writing, maintaining, or reviewing Python code to ensure consistency with modern tooling (uv, ruff, ty, pytest, pre-commit) and patterns (CLI separation, type safety, error handling)."
allowed-tools: "Read, Grep, Glob, Edit, Write"
argument-hint: ""
user-invocable: false
---

# Python Development

Apply this skill when writing, maintaining, or reviewing Python code.

---

## Mode Detection

Detect the mode from the user's request before acting:

| Signal | Mode |
|---|---|
| "write", "create", "add", "scaffold", "implement", "new" | **WRITE** |
| "fix", "refactor", "update", "change", "migrate", "improve" | **MAINTAIN** |
| "review", "check", "audit", "look at", "what do you think" | **REVIEW** |

---

## WRITE Mode

### Step 1: Greenfield or brownfield?

**Greenfield** (new project or new module in a greenfield project):
- Use templates from [tooling.md](tooling.md) verbatim — don't approximate
- Apply src/ layout, hatchling build system, full tooling stack
- Apply all rules below from the start

**Brownfield** (inheriting existing code):
- Read existing code first with Read/Grep before writing anything
- Match existing patterns — don't retrofit greenfield defaults
- Use the brownfield decision tree at the bottom of this file

### Step 2: Apply these rules when writing any code

**Functions and modules:**
- Every function and module gets a docstring summary (one line is enough; add more lines only when behavior is non-obvious)
- Every function gets full type hints using modern syntax (`str | None`, `list[str]`, not `Optional`, not `Union`)
- See [code-style.md](code-style.md) for all style rules

**Error handling:**
- Raise domain exceptions in core logic, catch at the CLI layer — never both
- Always chain exceptions: `raise AppError("msg") from e`
- See [patterns.md](patterns.md) for exception hierarchy and CLI/core separation

**Structure:**
- Separate CLI layer (parse args + display output) from core layer (pure logic, no CLI imports)
- Use `pathlib.Path` for all file operations — never `os.path` or string concatenation
- Use `@dataclass` for any domain model with 2+ fields

**Output:**
- Default to `typer.echo` — don't add Rich or logging unless the user asks for a `--verbose` flag

**Config:**
- Use `tomllib` (stdlib) + TOML file — not Pydantic, not env vars
- Env vars only for secrets or CI overrides

**Tests:**
- Class-based: `class TestFoo`, `def test_scenario`
- `conftest.py` for shared fixtures
- `tmp_path` for filesystem, `monkeypatch` for env vars
- Test core logic directly; test CLI only for argument parsing and exit codes

---

## MAINTAIN Mode

1. **Read before writing** — use Read/Grep to understand the existing code
2. **Match existing patterns** — preserve the style even if it differs from greenfield defaults
3. **Run checks after editing** — ask the user to run `make check` to validate
4. **Don't change tooling** unless the user explicitly asks

For brownfield codebases: apply only the brownfield decision tree below.

---

## REVIEW Mode

Go through the code and report findings in two categories:

### Blockers (must fix)
- [ ] Bare `except:` or `except Exception` without re-raising
- [ ] Unused imports or dead code
- [ ] Secrets or credentials hardcoded in source

### Nits (suggest, don't block)
- [ ] Missing type hints on function signatures
- [ ] Missing docstrings on functions or modules
- [ ] Hardcoded values that should be module-level constants or config
- [ ] Exception not chained with `from e` when re-raising
- [ ] `os.path` or string paths instead of `pathlib.Path`
- [ ] Mutable default arguments (`def f(x=[])`)
- [ ] Wrong exception type (raising base `Exception` instead of domain-specific)
- [ ] Tests touching real filesystem or env vars without `monkeypatch`/`tmp_path`

When a blocker is found, grep for the same pattern across the codebase and report all instances.

---

## Brownfield Decision Tree

**Build system?**
- Exists (Poetry, setup.cfg, etc.) → keep it
- Missing → migrate to hatchling

**Python version?**
- 3.11 or older → keep it, don't force upgrade
- 3.12+ → align with greenfield defaults

**CLI framework?**
- Click or Typer → already aligned, keep it
- argparse or custom → refactor only if actively developing
- No CLI → leave as-is

**Type hints?**
- 80%+ coverage → run `ty check --strict`
- <80% → run `ruff check` only, skip ty
- 0% → run tests only

**Test count?**
- 50+ tests → consider unit/cli split
- <50 → keep flat `tests/` directory

**Minimal acceptable setup for any brownfield project:**
```makefile
make install   # install deps
make test      # run tests
make lint      # check style
make check     # all of the above
```

---

## Greenfield Checklist

- [ ] `.python-version` set to `3.12`
- [ ] `pyproject.toml` with hatchling, `requires-python = ">=3.12"`, `[dependency-groups] dev`
- [ ] `Makefile` with: `install`, `test`, `test-v`, `lint`, `format`, `fix`, `typecheck`, `check`, `clean`
- [ ] `.pre-commit-config.yaml` with ruff + ty hooks
- [ ] `src/my_project/` with `cli.py`, `commands/`, `core/`
- [ ] `tests/` with `conftest.py`
- [ ] `make install && make check` passes before first commit
- [ ] `pre-commit install` enabled

See [tooling.md](tooling.md) for copy-paste templates.
