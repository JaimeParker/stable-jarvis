---
name: python-patterns
description: "Enforces project-specific Python conventions including type hints, error handling, concurrency patterns, and package organization. Use when writing, reviewing, or refactoring Python code, setting up Python project structure, configuring linting and formatting tools, or ensuring PEP 8 compliance in .py files."
---

# Python Development Patterns

Project-specific Python conventions and patterns for this codebase. Focuses on idioms and practices that differ from defaults or need consistent enforcement.

## Type Hints

Use modern Python 3.9+ built-in types. Fall back to `typing` imports only for Python 3.8 compatibility:

```python
# Python 3.9+ — preferred
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# Use Protocol for duck typing
from typing import Protocol

class Renderable(Protocol):
    def render(self) -> str: ...

def render_all(items: list[Renderable]) -> str:
    return "\n".join(item.render() for item in items)
```

## Error Handling

Always catch specific exceptions and chain them:

```python
def load_config(path: str) -> Config:
    try:
        with open(path) as f:
            return Config.from_json(f.read())
    except FileNotFoundError as e:
        raise ConfigError(f"Config file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in config: {path}") from e
```

Use a project exception hierarchy:

```python
class AppError(Exception):
    """Base exception for all application errors."""

class ValidationError(AppError):
    """Raised when input validation fails."""

class NotFoundError(AppError):
    """Raised when a requested resource is not found."""
```

## Concurrency

| Task Type | Pattern | Module |
|-----------|---------|--------|
| I/O-bound (network, file) | `ThreadPoolExecutor` | `concurrent.futures` |
| CPU-bound (computation) | `ProcessPoolExecutor` | `concurrent.futures` |
| Async I/O | `asyncio` + `aiohttp` | `asyncio` |

```python
# I/O-bound: threads
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_to_url = {executor.submit(fetch_url, url): url for url in urls}
    for future in concurrent.futures.as_completed(future_to_url):
        results[future_to_url[future]] = future.result()

# CPU-bound: processes
with concurrent.futures.ProcessPoolExecutor() as executor:
    results = list(executor.map(process_data, datasets))
```

## Performance Patterns

```python
# Use __slots__ for memory-critical classes
class Point:
    __slots__ = ['x', 'y']
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

# Use generators for large data
def read_lines(path: str) -> Iterator[str]:
    with open(path) as f:
        for line in f:
            yield line.strip()

# Use join, not concatenation in loops
result = "".join(str(item) for item in items)
```

## Project Tooling

```toml
# pyproject.toml essentials
[tool.black]
line-length = 88
target-version = ['py39']

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=mypackage --cov-report=term-missing"
```

```bash
# Standard workflow
black . && isort .    # Format
ruff check .          # Lint
mypy .                # Type check
pytest                # Test
```

## Anti-Patterns to Avoid

```python
# Mutable default arguments — use None instead
def append_to(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

# Use isinstance, not type()
if isinstance(obj, list): ...

# Use `is` for None comparison
if value is None: ...

# Explicit imports, never `from module import *`
from os.path import join, exists
```
