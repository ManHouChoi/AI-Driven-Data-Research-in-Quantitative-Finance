"""Small IO helpers for reproducible research scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Set, Union

import pandas as pd
import yaml


PathLike = Union[str, Path]


def load_yaml_config(path: PathLike) -> Dict[str, Any]:
    """Load a YAML configuration file and return an empty dict for empty files."""
    with Path(path).expanduser().resolve().open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def read_csv_checked(path: PathLike, required_columns: Optional[Set[str]] = None) -> pd.DataFrame:
    """Read a CSV and raise a clear error if required columns are missing."""
    csv_path = Path(path).expanduser().resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if required_columns:
        missing = sorted(required_columns.difference(df.columns))
        if missing:
            raise ValueError(f"{csv_path} is missing required columns: {missing}")
    return df


def ensure_parent_dir(path: PathLike) -> Path:
    """Create the parent directory for a file path and return the resolved path."""
    resolved = Path(path).expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved
