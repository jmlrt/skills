# Code Style

Reference for all style rules. Apply these when writing or reviewing Python code.

---

## Type Hints

Use modern syntax throughout — Python 3.12+ doesn't need `from __future__ import annotations`.

```python
# ✅ Correct
def process(path: Path, name: str | None = None) -> list[str]:

# ❌ Wrong
from __future__ import annotations
from typing import Optional, List, Union
def process(path: Path, name: Optional[str] = None) -> List[str]:
```

Use `collections.abc` for abstract types in hints:

```python
from collections.abc import Iterator, Sequence

def iter_files(root: Path) -> Iterator[Path]:
```

---

## Docstrings

Every function and module gets a docstring summary. One line is enough; add more lines only when behavior is non-obvious. No `Args:`, `Returns:`, or `Raises:` sections.

```python
# ✅ Correct
"""Parse tags from a markdown line."""

# ❌ Wrong — too much
"""Parse tags from a markdown line.

Args:
    line: The markdown line to parse.
Returns:
    List of tag strings.
"""

# ❌ Wrong — missing
def parse_tags(line: str) -> list[str]:
    return TAG_PATTERN.findall(line)
```

Add more than one line only when behavior is genuinely non-obvious.

---

## Imports

Three groups, separated by blank lines. Absolute imports only — no relative imports.

```python
# stdlib
import re
from dataclasses import dataclass
from pathlib import Path

# third-party
import typer
from rich.console import Console

# local
from my_project.core.processor import process_file
from my_project.exceptions import AppError
```

Never use `from x import *`.

---

## Paths

Always `pathlib.Path`. Never `os.path` or string concatenation.

```python
# ✅ Correct
config_file = Path.home() / ".config" / "myapp" / "config.toml"
content = config_file.read_text()

# ❌ Wrong
import os
config_file = os.path.join(os.path.expanduser("~"), ".config", "myapp", "config.toml")
```

---

## Module-Level Constants

Compile regex patterns and repeated values at module level, in `UPPER_SNAKE_CASE`, after imports.

```python
import re

TAG_PATTERN = re.compile(r"@([a-zA-Z0-9_-]+)")
DEFAULT_TIMEOUT = 30
```

---

## Private Helpers

Prefix with `_` for anything not part of the public API.

```python
def _parse_raw_entry(line: str) -> dict[str, str]:
    """Parse a raw log line into fields."""
    ...
```

---

## Dataclasses

Use `@dataclass` for any domain model with 2+ fields. Use `field(default_factory=...)` for mutable defaults.

```python
from dataclasses import dataclass, field

@dataclass
class TimerEntry:
    """A time tracking entry."""
    description: str
    tags: list[str] = field(default_factory=list)
    duration_minutes: int = 0
    is_active: bool = False
```

---

## Exception Chaining

Always chain with `from e` when catching and re-raising.

```python
# ✅ Correct
try:
    data = tomllib.load(f)
except tomllib.TOMLDecodeError as e:
    raise ConfigError(f"Invalid config: {path}") from e

# ❌ Wrong — loses original traceback
try:
    data = tomllib.load(f)
except tomllib.TOMLDecodeError as e:
    raise ConfigError(f"Invalid config: {path}")
```

---

## `__init__.py`

Keep it minimal. Only put `__version__` if the project exposes a version (e.g. has a CLI with `--version`). Otherwise leave it empty.

```python
# src/my_project/__init__.py
__version__ = "0.1.0"
```

The version in `__init__.py` must match `pyproject.toml`. Use hatchling's version hook to avoid duplication if it becomes a maintenance burden.

---

## Config Pattern

Use `tomllib` (stdlib, Python 3.11+) with a TOML file. Env vars only for secrets or CI overrides.

```python
import tomllib
from pathlib import Path

CONFIG_FILE = Path.home() / ".config" / "myapp" / "config.toml"

def load_config(path: Path = CONFIG_FILE) -> dict:
    """Load configuration from TOML file."""
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)
```

Example `config.toml`:
```toml
[api]
key = "..."
timeout = 30

[output]
format = "markdown"
```

**Use Pydantic instead of raw `tomllib` when:**
- Config has nested sections with required fields and defaults
- You need validation (type coercion, value constraints)
- You want IDE autocompletion on config fields

**Stick with `tomllib` when:**
- Config is flat or simple
- No validation beyond "key exists"
- You want zero extra dependencies

```python
# Pydantic config — worth it when config is complex
from pydantic import BaseModel

class ApiConfig(BaseModel):
    key: str
    timeout: int = 30

class Config(BaseModel):
    api: ApiConfig
    output_format: str = "markdown"

def load_config(path: Path = CONFIG_FILE) -> Config:
    """Load and validate configuration."""
    with path.open("rb") as f:
        data = tomllib.load(f)
    return Config.model_validate(data)
```
