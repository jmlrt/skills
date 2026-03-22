# Error Handling: Greenfield Defaults

For new projects: **Result dataclasses for expected failures**, **exceptions for bugs**.

---

## Core Principle

- ✅ **Result Dataclasses**: Expected failures (file not found, invalid input, network timeout)
- ✅ **Exceptions**: Unexpected bugs (programming errors, system failures)

This gives explicit control flow without exception overhead.

---

## Result Dataclasses for Expected Failures

### Pattern

```python
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
        # Do work
        result_data = {"processed": item}
        return ProcessResult(success=True, data=result_data)
    except ValueError as e:
        return ProcessResult(success=False, error=str(e))
```

### Usage in CLI

```python
# In your CLI command
result = process_item("input")

if not result.success:
    console.print(f"[red]Error:[/red] {result.error}")
    raise typer.Exit(1)

console.print(f"Success: {result.data}")
```

### Partial Success Pattern

When processing multiple items:

```python
from dataclasses import dataclass, field

@dataclass
class BatchResult:
    success: bool  # True = all succeeded
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
            failed.append((item, result.error or "Unknown"))

    return BatchResult(
        success=len(failed) == 0,
        succeeded=succeeded,
        failed=failed,
    )
```

---

## Custom Exceptions for Bugs

For errors that shouldn't happen:

```python
class AppError(Exception):
    """Base application error."""
    exit_code: int = 1

class ConfigError(AppError):
    """Configuration error."""
    pass

class ValidationError(AppError):
    """Validation error."""
    pass
```

Usage:

```python
def load_config(path: Path) -> Config:
    """Load config file."""
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        with path.open() as f:
            data = yaml.safe_load(f)
        return Config(**data)
    except Exception as e:
        raise ConfigError(f"Invalid config: {e}")

# In CLI:
try:
    config = load_config(config_path)
    result = do_work(config)
except AppError as e:
    console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(e.exit_code)
```

---

## Testing Error Paths

```python
# tests/test_processor.py

def test_succeeds_with_valid_input():
    result = process_item("valid")
    assert result.success
    assert result.data == {"processed": "valid"}

def test_fails_with_invalid_input():
    result = process_item("invalid")
    assert not result.success
    assert "invalid" in result.error.lower()

def test_partial_success():
    result = process_batch(["valid", "invalid", "valid"])
    assert not result.success  # Some failed
    assert len(result.succeeded) == 2
    assert len(result.failed) == 1
```

---

## Best Practices

**DO**:
- ✅ Use result dataclasses for expected failures
- ✅ Use exceptions for bugs
- ✅ Always check `.success` before using result data
- ✅ Include error message when `success=False`

**DON'T**:
- ❌ Raise exceptions for expected failures
- ❌ Ignore result status
- ❌ Leave `.error` unset when `success=False`

