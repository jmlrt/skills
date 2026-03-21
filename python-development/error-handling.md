# Error Handling Patterns

Production-grade error patterns: result dataclasses for expected failures, custom exceptions for bugs.

---

## Core Principle

- ✅ **Result Dataclasses**: Expected failures (user input, file not found)
- ✅ **Custom Exceptions**: Unexpected bugs (programming errors, system failures)

---

## Result Dataclasses for Expected Failures

### Pattern

```python
from __future__ import annotations

from dataclasses import dataclass

@dataclass
class OperationResult:
    """Result of an operation."""
    success: bool
    data: dict | None = None
    error: str | None = None

def process_item(item: str) -> OperationResult:
    """Process an item.

    Returns:
        OperationResult with success status and optional data/error.
    """
    try:
        # Do work
        result_data = {"processed": item}
        return OperationResult(success=True, data=result_data)
    except ValueError as e:
        return OperationResult(success=False, error=str(e))
```

### Why Result Dataclasses?

1. **Explicit Control Flow** - No exception handling overhead for expected failures
2. **Type Safety** - Clear return type with data structure
3. **Testability** - Easy to verify success/error cases
4. **Composability** - Chain results together
5. **Readability** - Clear what function returns

---

## Real-World Example: Directory Processing

```python
# src/my_project/core/processor.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_project.config import Config

@dataclass
class ProcessResult:
    """Result of processing an item."""
    success: bool
    processed_items: int = 0
    skipped_items: int = 0
    error: str | None = None

def process_directory(
    path: Path,
    config: Config,
) -> ProcessResult:
    """Process all files in directory.

    Args:
        path: Directory to process.
        config: Configuration.

    Returns:
        ProcessResult with counts and optional error.
    """
    processed = 0
    skipped = 0

    if not path.exists():
        return ProcessResult(
            success=False,
            error=f"Directory not found: {path}"
        )

    try:
        for file in path.glob("*.md"):
            try:
                # Process file
                result = process_file(file, config)
                if result.success:
                    processed += 1
                else:
                    skipped += 1
            except Exception as e:
                # Unexpected error in single file
                # Continue with others
                skipped += 1

        return ProcessResult(
            success=True,
            processed_items=processed,
            skipped_items=skipped,
        )
    except Exception as e:
        # Unexpected error (e.g., permission denied)
        return ProcessResult(
            success=False,
            error=f"Failed to process directory: {e}"
        )

def process_file(file: Path, config: Config) -> ProcessResult:
    """Process single file.

    Returns:
        ProcessResult with success status.
    """
    try:
        content = file.read_text()
        # Do processing...
        return ProcessResult(success=True, processed_items=1)
    except FileNotFoundError:
        return ProcessResult(success=False, error=f"File not found: {file}")
```

---

## Partial Success Pattern

When some items succeed and some fail:

```python
from dataclasses import dataclass, field

@dataclass
class BatchResult:
    """Result of batch operation."""
    success: bool  # True = all succeeded, False = some/all failed
    succeeded: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)  # (item, error)

def process_batch(items: list[str]) -> BatchResult:
    """Process multiple items.

    Returns:
        BatchResult with succeeded and failed items.
    """
    succeeded = []
    failed = []

    for item in items:
        try:
            result = process_item(item)
            if result.success:
                succeeded.append(item)
            else:
                failed.append((item, result.error or "Unknown error"))
        except Exception as e:
            failed.append((item, str(e)))

    all_succeeded = len(failed) == 0
    return BatchResult(
        success=all_succeeded,
        succeeded=succeeded,
        failed=failed,
    )
```

---

## Using Results in CLI Commands

```python
# src/my_project/commands/process.py
from __future__ import annotations

import click
from rich.console import Console
from pathlib import Path

from my_project.core.processor import process_directory

console = Console()

@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.pass_context
def process_command(ctx: click.Context, path: str) -> None:
    """Process files in directory."""
    from my_project.context import Context

    cli_ctx: Context = ctx.find_object(Context)
    config = cli_ctx.config

    if config is None:
        console.print("[red]Error:[/red] No configuration loaded")
        raise SystemExit(1)

    # Call core function
    result = process_directory(Path(path), config)

    # Check result
    if not result.success:
        console.print(f"[red]Error:[/red] {result.error}")
        raise SystemExit(1)

    # Display success
    console.print(
        f"[green]Success![/green] "
        f"Processed: {result.processed_items}, "
        f"Skipped: {result.skipped_items}"
    )
```

---

## Testing Results

```python
# tests/unit/test_processor.py
from pathlib import Path
import pytest

from my_project.core.processor import process_directory

def test_process_succeeds_with_valid_directory(tmp_path: Path):
    """Test successful processing."""
    # Setup
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test")

    config = Config()

    # Execute
    result = process_directory(tmp_path, config)

    # Assert
    assert result.success is True
    assert result.processed_items == 1
    assert result.error is None

def test_process_fails_with_missing_directory():
    """Test handling missing directory."""
    config = Config()

    result = process_directory(Path("/nonexistent"), config)

    assert result.success is False
    assert "not found" in result.error.lower()
    assert result.processed_items == 0

def test_process_handles_partial_failures(tmp_path: Path):
    """Test handling mixed success/failure."""
    # Setup
    (tmp_path / "valid.md").write_text("# Valid")
    (tmp_path / "invalid.md").write_text(None)  # Will fail

    config = Config()

    # Execute
    result = process_directory(tmp_path, config)

    # Assert
    assert result.success is True  # Some succeeded
    assert result.processed_items > 0
    assert result.skipped_items > 0
```

---

## Custom Exception Hierarchy

For unexpected errors and bugs:

```python
class AppError(Exception):
    """Base exception for all app errors."""
    exit_code: int = 1

class ConfigError(AppError):
    """Configuration file errors."""
    pass

class FetchError(AppError):
    """URL fetching errors."""
    pass

class ValidationError(AppError):
    """Input validation errors."""
    pass

class PartialSuccessError(AppError):
    """Some operations succeeded, some failed."""
    exit_code: int = 2
```

### Usage

```python
def load_config(path: Path) -> Config:
    if not path.exists():
        raise ConfigError(f"Config not found: {path}")

    try:
        with path.open() as f:
            data = yaml.safe_load(f)
        return Config.model_validate(data)
    except ValidationError as e:
        raise ConfigError(f"Invalid config: {e}")
```

### Handling in CLI

```python
try:
    result = do_work()
except AppError as e:
    console.print(f"[red]Error:[/red] {e}")
    raise SystemExit(e.exit_code)
```

---

## Best Practices

### ✅ DO

- ✅ Use result dataclasses for expected failures
- ✅ Include error message when `success=False`
- ✅ Use dataclass fields with defaults
- ✅ Test both success and failure paths
- ✅ Chain results in core functions
- ✅ Convert results to exceptions at boundaries

### ❌ DON'T

- ❌ Raise exceptions for expected failures
- ❌ Leave `error` field unset when `success=False`
- ❌ Ignore result status (always check `.success`)
- ❌ Overload result dataclass with too much data
- ❌ Use result dataclasses in library APIs (use exceptions instead)

---

## Summary

**Error Handling Strategy**:
- ✅ Use result dataclasses for expected failures
- ✅ Use custom exceptions for bugs
- ✅ Test both success and failure paths
- ✅ Clear, explicit error messages
- ✅ Appropriate exit codes

Result dataclasses provide:
- Explicit error handling without exception overhead
- Type safety and structure
- Composability and testability
- Clear control flow

Use them in core modules to return operation status. Let CLI commands handle the actual exceptions and exit codes.
