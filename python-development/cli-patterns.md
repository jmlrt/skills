# CLI Patterns & Architecture

Production patterns for building CLI tools: separation of concerns, clean architecture, dependency injection.

---

## Separation of Concerns

The fundamental principle: **Keep CLI parsing separate from business logic.**

```
┌──────────────────────────────┐
│   CLI Command Module (50-150 lines)
│   • Parse Click arguments
│   • Call core function
│   • Display output (Rich)
│   • Handle errors
└────────────────┬─────────────┘
                 ↓ (passes config as parameter)
┌──────────────────────────────┐
│   Core Module (Pure Logic)
│   • No Click dependencies
│   • No Rich/console imports
│   • Returns dataclass
│   • 100% testable without CLI
└──────────────────────────────┘
```

### The Problem: Mixed Concerns

```python
# ❌ WRONG: CLI and logic mixed
def extract_command(ctx: click.Context, path: str):
    # Business logic HERE
    articles = []
    for file in Path(path).glob("*.md"):
        content = file.read_text()
        # Parse, extract, truncate...
        articles.append({...})

    # CLI display HERE
    for article in articles:
        console.print(f"[blue]{article['title']}[/blue]")
```

**Problems:**
- ❌ Can't test extraction without CLI
- ❌ Can't reuse in other commands
- ❌ Can't output in different formats without rewriting
- ❌ ~400 lines mixing two concerns

### The Solution: Separate

#### Step 1: Core Module (Pure Logic)

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
    path: str

@dataclass
class ExtractionResult:
    success: bool
    articles: list[Article]
    error: str | None = None

def extract_metadata(
    path: Path,
    config: Config,
    max_chars: int = 150,
) -> ExtractionResult:
    """Pure business logic - no CLI dependencies.

    Args:
        path: Directory to scan.
        config: Application configuration.
        max_chars: Max description characters.

    Returns:
        ExtractionResult with articles.
    """
    try:
        articles = []
        for file in path.glob("*.md"):
            title = file.stem
            content = file.read_text()
            articles.append(Article(
                title=title,
                description=content[:max_chars],
                path=str(file),
            ))
        return ExtractionResult(success=True, articles=articles)
    except Exception as e:
        return ExtractionResult(success=False, articles=[], error=str(e))
```

#### Step 2: CLI Command (Thin Wrapper)

```python
# src/my_project/commands/extract.py
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from my_project.core.extractor import extract_metadata

console = Console()

@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--max-chars", "-m", type=int, default=150, help="Max description chars")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
@click.pass_context
def extract_command(
    ctx: click.Context,
    path: str,
    max_chars: int,
    format: str,
) -> None:
    """Extract metadata from markdown files."""
    from my_project.context import Context

    # Get configuration
    cli_ctx: Context = ctx.find_object(Context)
    config = cli_ctx.config

    if config is None:
        console.print("[red]Error:[/red] No configuration loaded")
        raise SystemExit(1)

    # Call core logic
    result = extract_metadata(Path(path), config, max_chars)

    # Display results
    if not result.success:
        console.print(f"[red]Error:[/red] {result.error}")
        raise SystemExit(1)

    if format == "json":
        import json
        data = [
            {"title": a.title, "description": a.description}
            for a in result.articles
        ]
        console.print_json(data=data)
    else:
        table = Table(title="Articles")
        table.add_column("Title")
        table.add_column("Description")
        for article in result.articles:
            table.add_row(article.title, article.description)
        console.print(table)
```

### Comparison

| Aspect | Mixed (❌) | Separated (✅) |
|--------|-----------|----------------|
| **CLI lines** | 400 | 60 |
| **Core lines** | 0 | 100 |
| **Total lines** | 400 | 160 |
| **Testable without CLI?** | No | Yes |
| **Reusable in other commands?** | No | Yes |
| **Output formats** | One | Many |

---

## File Organization

```
src/my_project/
├── commands/
│   ├── extract.py          # ← CLI wrapper (~60 lines)
│   ├── move.py             # ← CLI wrapper
│   └── stats.py            # ← CLI wrapper
├── core/
│   ├── extractor.py        # ← Pure logic (~100 lines)
│   ├── mover.py            # ← Pure logic
│   └── stats.py            # ← Pure logic
├── context.py              # ← Context for dependency injection
└── cli.py                  # ← Entry point, command registration
```

---

## Context Module Pattern: Solving Circular Imports

The **context module** extracts shared configuration to break circular dependencies.

### The Problem

```python
# ❌ Circular dependency
# cli.py imports Command for registration
# Command imports Context from cli.py for configuration
# → Import fails!
```

### The Solution

**Create dedicated `context.py` module:**

```python
# src/my_project/context.py
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_project.config import Config

class Context:
    """CLI context object."""
    def __init__(self, config: Config | None = None, verbose: int = 0):
        self.config = config
        self.verbose = verbose
```

**Commands import from context:**

```python
# src/my_project/commands/extract.py
from my_project.context import Context  # ← Import from context module

@click.command()
def extract(ctx: click.Context) -> None:
    cli_ctx: Context = ctx.find_object(Context)
    config = cli_ctx.config
```

**CLI imports from context:**

```python
# src/my_project/cli.py
from my_project.context import Context  # ← Same module

@click.group()
@click.pass_context
def main(ctx: click.Context) -> None:
    context = Context(config=load_config())
    ctx.obj = context
```

### Result

✅ No circular imports
✅ Commands import Context from context module
✅ CLI imports Context from same module
✅ All top-level imports clean

---

## Testing Impact

### Testing Core Logic (Easy)

```python
# tests/unit/test_extractor.py
from pathlib import Path
from my_project.core.extractor import extract_metadata

def test_extract_finds_articles(tmp_path: Path):
    """Test extraction logic directly."""
    # Create test file
    test_file = tmp_path / "test.md"
    test_file.write_text("# Title\n\nDescription here...")

    # Call core function directly
    config = Config()  # Create test config
    result = extract_metadata(tmp_path, config)

    assert result.success
    assert len(result.articles) == 1
    assert result.articles[0].title == "test"
```

### Testing CLI (Also Easy)

```python
# tests/cli/test_extract_cmd.py
from click.testing import CliRunner
from my_project.commands.extract import extract_command

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

---

## Common Patterns

### Pattern 1: CLI with Single Core Call

```python
@click.command()
@click.argument("input", type=click.Path())
def command(input: str) -> None:
    result = core_module.process(Path(input), config)
    if result.success:
        console.print(result.data)
    else:
        console.print(f"[red]{result.error}[/red]")
        raise SystemExit(1)
```

### Pattern 2: CLI with Multiple Core Calls

```python
@click.command()
@click.argument("path", type=click.Path())
def command(path: str) -> None:
    base = Path(path)

    # Call multiple core functions
    stats_result = core.stats.calculate(base, config)
    dupes_result = core.duplicates.find(base, config)

    # Display combined results
    console.print(f"Stats: {stats_result.data}")
    console.print(f"Duplicates: {dupes_result.data}")
```

### Pattern 3: CLI with Streaming Output

```python
@click.command()
@click.argument("items", nargs=-1)
def command(items: tuple[str]) -> None:
    for item in items:
        result = core_module.process(item, config)
        console.print(f"✓ {result.data}")
```

---

## Responsibilities

### CLI Module SHOULD:
- ✅ Parse Click arguments/options
- ✅ Call core functions
- ✅ Display output (Rich tables, colors, etc.)
- ✅ Handle user errors gracefully
- ✅ Exit with appropriate code

### CLI Module SHOULD NOT:
- ❌ Contain business logic
- ❌ Do file I/O directly
- ❌ Parse data formats
- ❌ Complex algorithms
- ❌ Direct database queries

### Core Module SHOULD:
- ✅ Implement business logic
- ✅ Accept parameters (not global config)
- ✅ Return dataclasses
- ✅ Be fully testable
- ✅ Be reusable

### Core Module SHOULD NOT:
- ❌ Import Click
- ❌ Use console.print()
- ❌ Parse CLI arguments
- ❌ Get config from global context
- ❌ Call sys.exit()

---

## Summary

**Separation of Concerns**:
- Keeps CLI and logic in separate modules
- CLI modules: 50-150 lines (thin wrappers)
- Core modules: Pure Python functions
- Results: Testable, reusable, maintainable code

**Context Module Pattern**:
- Extract configuration to separate module
- Break circular dependencies
- Enable clean command registration

This is the foundation of professional Python development.
