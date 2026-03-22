# Patterns

Core patterns for CLI structure, error handling, and testing.

---

## Verbosity / Rich Logging

Default output is `typer.echo`. Add Rich + stdlib logging **only** when the user asks for a `--verbose` flag.

```python
import logging
import typer
from rich.console import Console
from rich.logging import RichHandler

console = Console()

def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity flag."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=Console(stderr=True), show_time=False)],
    )

app = typer.Typer()

@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug output")) -> None:
    """My CLI tool."""
    setup_logging(verbose)
```

Use `logging.debug(...)` in core modules for diagnostic output. Use `typer.echo` / `console.print` in the CLI layer for user-facing output.

---

## CLI / Core Separation

**Goal**: core logic is testable without mocking Typer.

```
CLI layer                          Core layer
  parse args           →             no CLI imports
  call core function   ←             returns value or raises
  display output                     100% testable
```

**Core function:**

```python
# src/my_project/core/processor.py
from dataclasses import dataclass
from pathlib import Path

from my_project.exceptions import ProcessError

@dataclass
class ProcessResult:
    """Result of a processing operation."""
    processed: int
    output: Path

def process_file(path: Path) -> ProcessResult:
    """Process a single file and return the result."""
    if not path.exists():
        raise ProcessError(f"File not found: {path}")
    # do work
    return ProcessResult(processed=1, output=path.with_suffix(".out"))
```

**CLI wrapper:**

```python
# src/my_project/cli.py
import typer
from pathlib import Path
from my_project.core.processor import process_file
from my_project.exceptions import AppError

app = typer.Typer()

@app.command()
def process(path: Path) -> None:
    """Process a file."""
    try:
        result = process_file(path)
        typer.echo(f"Processed {result.processed} file(s) → {result.output}")
    except AppError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
```

---

## Exception Hierarchy

Define a base `AppError` and domain-specific subclasses in `exceptions.py`.

```python
# src/my_project/exceptions.py

class AppError(Exception):
    """Base exception for all application errors."""
    exit_code: int = 1

class ConfigError(AppError):
    """Configuration file is missing or invalid."""

class ProcessError(AppError):
    """Processing failed."""

class PartialSuccessError(AppError):
    """Some items succeeded, some failed."""
    exit_code: int = 2
```

**Rules:**
- Raise in core logic, catch at the CLI layer — never both
- Always chain with `from e` when re-raising
- Catch specific exceptions — never bare `except:` or `except Exception` without re-raising

```python
# ✅ Correct — specific, chained
try:
    with path.open("rb") as f:
        data = tomllib.load(f)
except tomllib.TOMLDecodeError as e:
    raise ConfigError(f"Invalid config file: {path}") from e

# ❌ Wrong — swallows the error
try:
    with path.open("rb") as f:
        data = tomllib.load(f)
except Exception:
    pass
```

---

## Batch Result Pattern

Use only when processing multiple items where **partial success is meaningful**.

```python
from dataclasses import dataclass, field

@dataclass
class BatchResult:
    """Result of a batch operation."""
    succeeded: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)  # (item, error)

    @property
    def success(self) -> bool:
        """Return True if all items succeeded."""
        return len(self.failed) == 0

def process_batch(items: list[str]) -> BatchResult:
    """Process multiple items, collecting successes and failures."""
    result = BatchResult()
    for item in items:
        try:
            process_item(item)
            result.succeeded.append(item)
        except ProcessError as e:
            result.failed.append((item, str(e)))
    return result
```

For single-item operations, raise exceptions directly — don't wrap in a result object.

---

## Testing Patterns

**Class-based organization:**

```python
# tests/test_processor.py
from pathlib import Path
import pytest
from my_project.core.processor import process_file
from my_project.exceptions import ProcessError

class TestProcessFile:
    """Tests for process_file."""

    def test_processes_valid_file(self, tmp_path: Path) -> None:
        """Happy path."""
        f = tmp_path / "input.txt"
        f.write_text("content")
        result = process_file(f)
        assert result.processed == 1

    def test_raises_on_missing_file(self) -> None:
        """Missing file raises ProcessError."""
        with pytest.raises(ProcessError, match="File not found"):
            process_file(Path("/nonexistent/file.txt"))
```

**CLI testing:**

```python
# tests/test_cli.py
from typer.testing import CliRunner
from my_project.cli import app

runner = CliRunner()

class TestProcessCommand:
    """Tests for the process CLI command."""

    def test_exits_with_error_on_missing_file(self) -> None:
        """CLI returns exit code 1 for missing files."""
        result = runner.invoke(app, ["process", "/nonexistent"])
        assert result.exit_code == 1
```

**Fixture rules:**
- `tmp_path` for filesystem isolation (built-in pytest fixture)
- `monkeypatch` for env vars and module attributes
- Shared fixtures in `conftest.py`

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Isolated config directory for tests."""
    d = tmp_path / ".config" / "myapp"
    d.mkdir(parents=True)
    return d
```

---

## TYPE_CHECKING Guard

Only use if you hit an actual circular import error. Don't add it preemptively.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_project.config import Config  # imported for type hints only

def process(config: "Config") -> None:
    """Process with config."""
    ...
```
