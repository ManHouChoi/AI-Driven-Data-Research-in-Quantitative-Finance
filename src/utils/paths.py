"""Path helpers for running scripts from the repository root."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union


PathLike = Union[str, Path]


def project_root() -> Path:
    """Return the configured project root or infer it from this file location."""
    configured = os.getenv("FYP_PROJECT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def resolve_project_path(path: PathLike) -> Path:
    """Resolve repository-relative paths against the project root."""
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (project_root() / candidate).resolve()


def ensure_dir(path: PathLike) -> Path:
    """Create and return a directory path."""
    resolved = resolve_project_path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved
