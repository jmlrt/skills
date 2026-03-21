# Error Handling Patterns

Production patterns for handling expected failures and bugs.

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
class ProcessResult:
    """Result of an operation."""
    success: bool
    data: dict | None = None
    error: str | None = None

def process_item(item: str) -> ProcessResult:
    """Process an item."""
    try:
        result_data = {"processed": item}
        return ProcessResult(success=True, data=result_data)
    except ValueError as e:
        return ProcessResult(success=False, error=str(e))
```

### Usage in CLI

```python
# src/my_project/commands/process.py
from my_project.core.processor import process_directory

@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.pass_context
def process_command(ctx: click.Context, path: str) -> None:
    """Process files in directory."""
    cli_ctx: Context = ctx.find_object(Context)
    config = cli_ctx.config

    result = process_directory(Path(path), config)

    if not result.success:
        console.print(f"[red]Error:[/red] {result.error}")
        raise SystemExit(1)

    console.print(
        f"[green]Success![/green] "
        f"Processed: {result.processed_items}, "
        f"Skipped: {result.skipped_items}"
    )
```

### Partial Success Pattern

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
    """Process multiple items."""
    succeeded = []
    failed = []

    for item in items:
        result = process_item(item)
        if result.success:
            succeeded.append(item)
        else:
            failed.append((item, result.error or "Unknown error"))

    return BatchResult(
        success=len(failed) == 0,
        succeeded=succeeded,
        failed=failed,
    )
```

---

## Testing Results

```python
# tests/unit/test_processor.py
def test_process_succeeds_with_valid_directory(tmp_path: Path):
    """Test successful processing."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test")

    config = Config()
    result = process_directory(tmp_path, config)

    assert result.success is True
    assert result.processed_items == 1
    assert result.error is None

def test_process_fails_with_missing_directory():
    """Test handling missing directory."""
    config = Config()
    result = process_directory(Path("/nonexistent"), config)

    assert result.success is False
    assert "not found" in result.error.lower()
```

---

## Custom Exceptions for Bugs

For unexpected errors and programming bugs:

```python
class AppError(Exception):
    """Base exception for all app errors."""
    exit_code: int = 1

class ConfigError(AppError):
    """Configuration file errors."""
    pass

class ValidationError(AppError):
    """Input validation errors."""
    pass

class FetchError(AppError):
    """URL fetching errors."""
    pass
```

### Usage in CLI

```python
def load_config(path: Path) -> Config:
    """Load configuration from file."""
    if not path.exists():
        raise ConfigError(f"Config not found: {path}")

    try:
        with path.open() as f:
            data = yaml.safe_load(f)
        return Config.model_validate(data)
    except ValidationError as e:
        raise ConfigError(f"Invalid config: {e}")

# In main CLI handler
try:
    config = load_config(config_path)
    result = do_work(config)
except AppError as e:
    console.print(f"[red]Error:[/red] {e}")
    raise SystemExit(e.exit_code)
```

---

## Best Practices

**DO**:
- ✅ Use result dataclasses for expected failures
- ✅ Use custom exceptions for bugs
- ✅ Check `.success` before using result data
- ✅ Return error message when `success=False`

**DON'T**:
- ❌ Raise exceptions for expected failures (file not found, invalid input)
- ❌ Ignore result status
- ❌ Leave `error` field unset when `success=False`

