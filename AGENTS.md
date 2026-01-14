# AGENTS.md

This file contains guidelines and commands for agentic coding agents working in this repository.

## Project Setup

This is a Python project using `pyproject.toml` for configuration. The project targets Python 3.12+.

### Initial Setup with UV Package Manager

Use UV package manager to set up this project as a proper package:

```bash
# Install uv if not already installed (choose one method)
# Method 1: pip install
pip install uv

# Method 2: Installer script (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
# On Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create virtual environment
uv venv

# Install dependencies (use uv sync for projects with pyproject.toml)
uv sync

# Install with all extras and dev dependencies
uv sync --all-extras --dev

# Alternative: Install specific dependency groups
uv sync --group dev
uv sync --no-dev  # Install only runtime dependencies

# Set Python version for project
uv python pin 3.12
```

### Project Structure

```
photo-organiser/
├── src/                 # Source code directory
│   └── photo_organiser/  # Main package
│       ├── __init__.py   # Package initialization and main()
│       └── __main__.py   # Module execution support
├── .venv/               # UV virtual environment
├── pyproject.toml        # Project configuration
├── uv.lock              # UV dependency lock file
├── README.md            # Project documentation
├── .python-version      # Python version specification
└── .gitignore           # Git ignore rules
```

## Build/Lint/Test Commands

This project is already configured with `ruff`, `mypy`, and `pytest`.

### Essential Commands

```bash
# Install dependencies
uv sync                    # Install from pyproject.toml
uv sync --dev             # Include dev dependencies
uv pip install -e .       # Editable install

# Add/remove dependencies (DO NOT edit pyproject.toml for deps)
# Use `uv add/uv remove` so `uv.lock` stays consistent.
uv add requests           # Add runtime dependency
uv add --dev pytest       # Add dev dependency
uv remove requests         # Remove dependency

# Run the CLI (no activation needed)
uv run photo-organiser --help
uv run python -m photo_organiser --help

# Common CLI commands
uv run photo-organiser init-db
uv run photo-organiser db-status
uv run photo-organiser scan-photos ./some/photos --recursive

# Linting (recommended: ruff)
uv run ruff check .
uv run ruff format .

# Type checking (recommended: mypy)
uv run mypy .

# Testing (recommended: pytest)
uv run pytest
uv run pytest tests/test_specific.py::test_function  # Single test
uv run pytest -v  # Verbose output
uv run pytest --cov=src --cov-report=html  # With coverage

# Smoke checks (safe: uses a temporary DB + temp storage dirs)
uv run python -m scripts.run_smoke

# Regenerate local image fixtures (if needed)
uv run python scripts/generate_test_photos.py

# Build and publish
uv build                  # Build package
uv publish               # Publish to PyPI

# Upgrade dependencies
uv sync --upgrade         # Upgrade all dependencies
uv add requests@latest    # Upgrade specific package

# Lockfile management
uv lock                   # Create/update uv.lock
uv sync --frozen          # Install from lockfile (exact versions)
uv lock --upgrade         # Update lockfile
```

### Recommended Development Dependencies

These are already included (see `pyproject.toml`). If you add more, prefer `uv add --dev ...`.

```toml
[project.optional-dependencies]
dev = [
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
]
```

## Code Style Guidelines

### Python Code Style

Follow PEP 8 with these specific conventions:

#### Import Organization
```python
# Standard library imports first
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

# Third-party imports second
import numpy as np
import pandas as pd

# Local imports third
from .utils import helper_function
from .models import DataModel
```

#### Formatting
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 88 characters (Black default)
- Use f-strings for string formatting
- Add type hints to all function signatures and variables

#### Naming Conventions
```python
# Variables and functions: snake_case
photo_directory = "/path/to/photos"
def organize_photos() -> None:

# Classes: PascalCase
class PhotoOrganizer:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 10_000_000
DEFAULT_PHOTO_FORMAT = "JPEG"

# Private methods: underscore prefix
def _internal_helper() -> str:
    return "internal"
```

#### Type Hints
```python
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

def process_photos(
    directory: Path,
    file_types: List[str],
    recursive: bool = True,
) -> Dict[str, Any]:
    """Process photos in the given directory.
    
    Args:
        directory: Path to the photo directory
        file_types: List of allowed file extensions
        recursive: Whether to search recursively
        
    Returns:
        Dictionary containing processing results
    """
    pass
```

### Error Handling

```python
# Use specific exceptions
try:
    with open(file_path, "rb") as f:
        content = f.read()
except FileNotFoundError:
    logger.error(f"File not found: {file_path}")
    raise
except PermissionError:
    logger.error(f"Permission denied: {file_path}")
    raise
except Exception as e:
    logger.error(f"Unexpected error reading {file_path}: {e}")
    raise

# Custom exceptions
class PhotoOrganizerError(Exception):
    """Base exception for photo organizer errors."""
    pass

class InvalidFileTypeError(PhotoOrganizerError):
    """Raised when file type is not supported."""
    pass
```

### Documentation

```python
def organize_photo_library(source_dir: Path, target_dir: Path) -> None:
    """Organize photos from source directory into target directory.
    
    Creates a structured photo library organized by date and metadata.
    Photos are sorted into year/month/day subdirectories.
    
    Args:
        source_dir: Directory containing source photos
        target_dir: Directory where organized photos will be placed
        
    Raises:
        InvalidFileTypeError: When unsupported file types are encountered
        PermissionError: When file access permissions are insufficient
        
    Example:
        >>> organize_photo_library(
        ...     Path("/raw/photos"),
        ...     Path("/organized/photos")
        ... )
    """
    pass
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def process_image(image_path: Path) -> None:
    logger.info(f"Processing image: {image_path}")
    try:
        # Processing logic here
        logger.debug(f"Successfully processed: {image_path}")
    except Exception as e:
        logger.error(f"Failed to process {image_path}: {e}")
        raise
```

## Testing Guidelines

### Test Structure
```python
# tests/test_photo_service.py
from __future__ import annotations

from pathlib import Path

import pytest

from photo_organiser.services.photo_service import PhotoProcessingService


@pytest.mark.asyncio
async def test_scan_directory_finds_photos(tmp_path: Path) -> None:
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()

    # Minimal placeholders for scan logic (scan looks at suffixes)
    (photos_dir / "a.jpg").write_bytes(b"x")
    (photos_dir / "b.png").write_bytes(b"x")

    service = PhotoProcessingService()
    result = await service.scan_directory(photos_dir, recursive=False)
    assert result["photo_count"] == 2
```

### Test Commands
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_photo_service.py

# Run specific test function
uv run pytest tests/test_database.py::test_create_database

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run with verbose output
uv run pytest -v
```

## Development Workflow

1. **Before making changes**: Run existing tests to ensure baseline
2. **Make changes**: Follow code style guidelines
3. **Run linting**: `uv run ruff check . && uv run ruff format .`
4. **Run type checking**: `uv run mypy .`
5. **Run tests**: `uv run pytest`
6. **Commit changes**: Use descriptive commit messages

## Package Management

This project is set up as a Python package. When adding new dependencies:

1. **Do not edit `pyproject.toml` to change dependencies directly** - use `uv add/uv remove` so `uv.lock` stays consistent
2. Add runtime dependencies: `uv add package_name`
3. Add dev dependencies: `uv add --dev package_name`
4. Install with `uv sync` or `uv pip install -e .`
5. UV automatically manages `uv.lock` file

### Advanced Package Management

```bash
# Add packages with version constraints
uv add "django>=4.0,<5.0"
uv add "requests>=2.31.0"

# Add from git repository
uv add git+https://github.com/user/repo.git
uv add git+https://github.com/user/repo.git@v1.0.0

# Add from local path
uv add ./local-package
uv add -e ./local-package  # Editable

# Add optional dependency groups
uv add --optional docs sphinx

# Export to requirements.txt for compatibility
uv export --format requirements-txt > requirements.txt
uv export --format requirements-txt --hash > requirements.txt

# Check for outdated packages
uv tree --outdated
```

## Best Practices

1. **Always use lockfiles** for reproducibility
2. **Pin Python version** with .python-version
3. **Separate dev dependencies** from production
4. **Use uv run** instead of activating venv
5. **Commit uv.lock** to version control
6. **Use --frozen in CI** for consistent builds
7. **Leverage global cache** for speed
8. **Use workspace** for monorepos
9. **Export requirements.txt** for compatibility
10. **Keep uv updated** for latest features

## Notes

- This project currently has minimal structure - expand as needed
- Consider adding `src/` layout for larger projects
- Add pre-commit hooks for automated quality checks
- Set up CI/CD pipeline for automated testing