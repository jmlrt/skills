# Python Patterns

## CLI / Core Separation

- Core (`core/`): no CLI imports, returns values (dataclasses) or raises domain exceptions. Fully testable.
- CLI (`cli.py`, `commands/`): parses args, calls core, displays output, catches `AppError` and exits.
- Raise in core, catch at the CLI layer, never both.

```python
@app.command()
def process(path: Path) -> None:
    """Process a file."""
    try:
        result = process_file(path)
    except AppError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(e.exit_code) from e
    typer.echo(f"Processed {result.processed} file(s)")
```

## Exception Hierarchy

`exceptions.py` defines `AppError(Exception)` with `exit_code: int = 1`, plus domain subclasses (`ConfigError`,
`ProcessError`). Use `PartialSuccessError` (`exit_code = 2`) with a `BatchResult` dataclass (`succeeded`, `failed`)
only when partial success over many items is meaningful; single-item operations just raise.

## Testing

- Class-based: `class TestFoo` / `def test_scenario`; shared fixtures in `conftest.py`.
- Test core directly; test the CLI (`typer.testing.CliRunner`) only for argument parsing and exit codes.
- **Module-level mutable state** (caches, registries, "used" sets): an `autouse` fixture that replaces or clears it is
  load-bearing. Without it, data from committed config files leaks into tests and assertions pass against real state.

```python
@pytest.fixture(autouse=True)
def _isolate_state(mocker: MockerFixture) -> None:
    mocker.patch.object(m, "REGISTRY", {})
    m._used.clear()
```
