"""Deterministic seeding helper shared by experiments."""

from __future__ import annotations

import os
import random

import numpy as np


def set_global_seed(seed: int = 42, deterministic_torch: bool = True) -> None:
    """Seed Python, NumPy, and Torch when Torch is installed."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)

    try:
        import torch
    except Exception:
        return

    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic_torch:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
