# CLI Patterns & Architecture

Production patterns for building testable, reusable CLI tools.

---

## Separation of Concerns

**Pattern**: CLI parsing (thin wrapper) + business logic (pure functions).

```
CLI Module (50-150 lines)     Core Module (Pure Logic)
  • Parse Click args      →     • No Click dependencies
  • Call core function    ←     • Returns dataclass
  • Display with Rich         • 100% testable
```

### Example: Core Module

```python
# src/my_project/core/extractor.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_project.config import Config

@dataclass
class Article:
    title: str
    description: str

@dataclass
class ExtractionResult:
    success: bool
    articles: list[Article]
    error: str | None = None

def extract_metadata(
    path: Path,
    config: Config,
) -> ExtractionResult:
    """Extract metadata from markdown files."""
    try:
        articles = []
        for file in path.glob("*.md"):
            articles.append(Article(
                title=file.stem,
                description=file.read_text()[:150],
            ))
        return ExtractionResult(success=True, articles=articles)
    except Exception as e:
        return ExtractionResult(success=False, articles=[], error=str(e))
```

### Example: CLI Module

```python
# src/my_project/commands/extract.py
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from my_project.core.extractor import extract_metadata
from my_project.context import Context

console = Console()

@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
@click.pass_context
def extract_command(
    ctx: click.Context,
    path: str,
    format: str,
) -> None:
    """Extract metadata from markdown files."""
    cli_ctx: Context = ctx.find_object(Context)
    config = cli_ctx.config

    if config is None:
        console.print("[red]Error:[/red] No configuration loaded")
        raise SystemExit(1)

    # Call core logic
    result = extract_metadata(Path(path), config)

    # Display results
    if not result.success:
        console.print(f"[red]Error:[/red] {result.error}")
        raise SystemExit(1)

    if format == "json":
        import json
        console.print_json(data=[{"title": a.title} for a in result.articles])
    else:
        table = Table(title="Articles")
        table.add_column("Title")
        for article in result.articles:
            table.add_row(article.title)
        console.print(table)
```

**Result**: Core logic testable without Click, reusable in other commands, multiple output formats.

---

## Type Checking & Circular Imports

**Pattern**: Use `TYPE_CHECKING` to import types without causing circular imports.

### The Problem

```python
# ❌ CIRCULAR: module_a imports module_b, module_b imports module_a
# module_a.py
from module_b import Config

def process(config: Config) -> None:
    pass

# module_b.py
from module_a import SomeClass  # Import fails here
```

### The Solution

```python
# ✅ NO CIRCULAR: Use TYPE_CHECKING guard
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module_b import Config  # Type checking only, not at runtime

def process(config: "Config") -> None:  # String reference
    # No circular import at runtime
    pass
```

### Example: CLI Architecture

```python
# src/my_project/context.py
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_project.config import Config

class Context:
    """CLI context object."""
    def __init__(self, config: Config | None = None):
        self.config = config

# src/my_project/cli.py
from my_project.context import Context

@click.group()
@click.pass_context
def main(ctx: click.Context) -> None:
    context = Context(config=load_config())
    ctx.obj = context

# src/my_project/commands/extract.py
from my_project.context import Context

@click.command()
@click.pass_context
def extract(ctx: click.Context) -> None:
    cli_ctx: Context = ctx.find_object(Context)
    config = cli_ctx.config
    # Use config
```

**Key Points**:
- All files import from `context.py` (neutral location)
- No circular dependencies
- Full type safety (IDE autocomplete works)
- Zero runtime overhead

---

## Testing CLI Logic

### Test Core Logic (No Click)

```python
# tests/unit/test_extractor.py
from pathlib import Path
from my_project.core.extractor import extract_metadata

def test_extract_finds_articles(tmp_path: Path):
    """Test extraction logic directly."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Title\n\nDescription here...")

    config = Config()
    result = extract_metadata(tmp_path, config)

    assert result.success
    assert len(result.articles) == 1
```

### Test CLI Interface

```python
# tests/cli/test_extract_cmd.py
from click.testing import CliRunner
from my_project.commands.extract import extract_command
from my_project.context import Context

def test_extract_command_output(mock_config):
    """Test CLI interface."""
    runner = CliRunner()
    result = runner.invoke(
        extract_command,
        ["--format", "json"],
        obj=Context(config=mock_config)
    )

    assert result.exit_code == 0
    assert "Title" in result.output
```

