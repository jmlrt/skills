# CLI Patterns: Separation of Concerns

For greenfield CLI projects: **thin CLI wrapper** + **pure core logic**.

---

## Pattern: Separation of Concerns

**Goal**: Make core logic testable without mocking Click/Typer.

```
CLI Layer (50-150 lines)           Core Layer (Pure Logic)
  • Parse arguments      →           • No CLI imports
  • Call core function   ←           • Returns dataclass
  • Display output                   • 100% testable
```

### Example: Greenfield CLI (englog pattern)

Core logic:

```python
# src/my_project/core/processor.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

@dataclass
class ProcessResult:
    success: bool
    processed: int = 0
    error: str | None = None

def process_file(path: Path) -> ProcessResult:
    """Pure business logic - no CLI dependencies."""
    try:
        content = path.read_text()
        # Do work
        return ProcessResult(success=True, processed=1)
    except FileNotFoundError:
        return ProcessResult(success=False, error=f"Not found: {path}")
```

CLI wrapper:

```python
# src/my_project/cli.py
import typer
from rich.console import Console
from my_project.core.processor import process_file

app = typer.Typer()
console = Console()

@app.command()
def process(path: str) -> None:
    """Process a file."""
    result = process_file(Path(path))

    if not result.success:
        console.print(f"[red]Error:[/red] {result.error}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Processed {result.processed} items")

if __name__ == "__main__":
    app()
```

Test core logic (no CLI):

```python
# tests/test_processor.py
from pathlib import Path
from my_project.core.processor import process_file

def test_process_succeeds(tmp_path: Path):
    """Test core logic directly."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    result = process_file(test_file)
    assert result.success
    assert result.processed == 1

def test_process_fails_not_found():
    """Test error handling."""
    result = process_file(Path("/nonexistent"))
    assert not result.success
    assert "Not found" in result.error
```

**Result**: Core logic testable, reusable, no Click/Typer mocks needed.

---

## Type Checking: Optional for Complex Projects

Only needed if you have circular imports between modules.

**Problem**: Module A imports types from Module B for type hints, Module B imports from Module A.

```python
# ❌ CIRCULAR
# module_a.py
from module_b import Config

def process(config: Config) -> None:
    pass

# module_b.py
from module_a import SomeClass  # ← Import error!
```

**Solution**: Use `TYPE_CHECKING` to import only for type hints:

```python
# ✅ FIXED
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module_b import Config  # Type checking only

def process(config: "Config") -> None:  # String reference
    pass
```

**When to use**:
- Complex projects (clipmd) with many interdependencies → use TYPE_CHECKING
- Simple projects (englog, spotfm) → probably don't need it

**Don't add it unless you hit a circular import error.**

---

## Testing Patterns

### Test Core Logic

```python
# tests/test_core_logic.py
def test_core_function(tmp_path: Path):
    """Test business logic directly."""
    result = core.do_something(tmp_path)
    assert result.success
```

### Test CLI Interface (if needed)

```python
# tests/test_cli.py
from typer.testing import CliRunner
from my_project.cli import app

def test_cli_command():
    """Test CLI command interface."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
```

**Key**: Test core logic directly, test CLI only for argument parsing + output.

