# Type Checking & TYPE_CHECKING Guard Pattern

The `TYPE_CHECKING` guard is a critical pattern for type hints without circular imports.

---

## The Problem: Circular Imports

```python
# ❌ Direct import causes circular dependency
# module_a.py
from module_b import Config

def process(config: Config) -> None:
    ...

# module_b.py
from module_a import process  # Circular import!

class Config:
    pass
```

Result: `ImportError: cannot import name 'Config'`

---

## The Solution: TYPE_CHECKING Guard

```python
# ✅ Use TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module_b import Config  # Type checking only, not at runtime

def process(config: "Config") -> None:  # String forward reference
    ...
```

**Why it works:**
- `TYPE_CHECKING` is `False` at runtime → import is skipped
- `TYPE_CHECKING` is `True` during type checking (ty, mypy, pyright) → import happens
- Result: No circular dependency, full type information for tools

---

## Modern Pattern: PEP 563

Use `from __future__ import annotations` for cleaner code:

```python
from __future__ import annotations  # Makes annotations strings by default

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_project.config import Config

# Now you can use Config WITHOUT quotes!
def process(config: Config) -> None:  # ✅ No quotes needed
    ...
```

**Benefits:**
- ✅ Cleaner code (no `"Config"` strings everywhere)
- ✅ IDE autocomplete works
- ✅ Type checkers understand types
- ✅ No circular imports

---

## Real-World Example

```python
# src/my_project/core/extractor.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_project.config import Config  # ← Only for type checking

@dataclass
class ExtractionResult:
    success: bool
    data: dict
    error: str | None = None

def extract_metadata(
    path: Path,
    config: Config,  # ← No quotes needed
    max_chars: int = 150,
) -> ExtractionResult:
    """Extract metadata from markdown file.

    Args:
        path: Path to markdown file.
        config: Application configuration.
        max_chars: Maximum description length.

    Returns:
        ExtractionResult with extracted fields.
    """
    # At runtime, Config is NOT imported
    # But type checkers know its type
    ...
```

---

## Common Patterns

### Pattern 1: Core Module with Config Dependency

```python
# src/my_project/core/processor.py
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_project.config import Config

def process_file(path: Path, config: Config) -> dict:
    """Process file with configuration."""
    # config is available at runtime (it's a parameter)
    # But we didn't import Config, so no circular dependency
    pass
```

### Pattern 2: Multiple Conditional Imports

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_project.config import Config
    from my_project.context import Context
    from my_project.cache import Cache

def orchestrate(
    config: Config,
    context: Context,
    cache: Cache,
) -> None:
    """Main orchestration function."""
    pass
```

### Pattern 3: CLI Command Accessing Config

```python
# src/my_project/commands/extract.py
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.console import Console

if TYPE_CHECKING:
    from my_project.config import Config

console = Console()

@click.command()
@click.argument("path", type=click.Path())
@click.pass_context
def extract_command(ctx: click.Context, path: str) -> None:
    """Extract data from file."""
    from my_project.cli import get_config  # Runtime import

    config: Config = get_config(ctx)  # Type hint available
    # Use config...
```

---

## When to Use TYPE_CHECKING

✅ **Use TYPE_CHECKING when:**
- Module A needs to type-hint something from Module B
- Module B imports from Module A (or would create circular dependency)
- You want full type safety without runtime overhead

❌ **Don't use when:**
- You need the class/function at runtime
- It's a simple, self-contained import
- The dependency isn't circular

---

## Common Mistakes

### ❌ Mistake 1: Using TYPE_CHECKING Import at Runtime

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_module import MyClass

# ❌ WRONG: Using MyClass that wasn't imported
obj = MyClass()  # NameError: name 'MyClass' is not defined
```

**Fix**: Only use TYPE_CHECKING imports for type hints

```python
def process(obj: MyClass) -> None:  # ✅ OK: Type hint only
    # Use obj parameter (which is passed in)
    pass
```

### ❌ Mistake 2: Forgetting PEP 563

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_module import Config

# ❌ WRONG: Quotes needed without PEP 563
def process(config: Config) -> None:  # Type error!
    pass
```

**Fix**: Always use PEP 563

```python
from __future__ import annotations  # ← Always include this

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_module import Config

def process(config: Config) -> None:  # ✅ No quotes needed
    pass
```

---

## IDE Integration

### VSCode + Pylance

The TYPE_CHECKING import works perfectly with Pylance:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_project.config import Config

def process(config: Config) -> None:
    # Pylance understands Config
    # Autocomplete: config.
    # Shows all available attributes
    pass
```

### PyCharm

Similarly, PyCharm understands TYPE_CHECKING:

```python
# Autocomplete works
# Go to definition works
# Refactoring works
```

---

## Summary

The TYPE_CHECKING pattern:

- ✅ **Simple**: Three lines of code
- ✅ **Safe**: Zero runtime overhead
- ✅ **Powerful**: Full type information for tools
- ✅ **Standard**: Used across modern Python projects
- ✅ **Best practice**: Recommended in PEP 484, PEP 563

**Remember**: TYPE_CHECKING = type hints without runtime imports = no circular imports
