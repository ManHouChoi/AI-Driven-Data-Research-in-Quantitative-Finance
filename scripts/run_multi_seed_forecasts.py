#!/usr/bin/env python3
"""Run final ST-GAT forecasts across multiple random seeds.

This is a controlled robustness protocol: it uses the existing validation-selected
Optuna parameter files and writes outputs to `outputs/gat/multi_seed/`, leaving
the canonical headline outputs untouched.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


LEVEL_CONFIG = {
    "macro": {
        "script": ROOT / "src" / "gat" / "GAT_forecast_macro.py",
        "output_env": "FYP_GAT_MACRO_OUTPUT_DIR",
        "params_env": "FYP_GAT_MACRO_PARAMS_JSON",
        "params_path": ROOT / "outputs" / "gat" / "GAT_output_macro" / "optuna_best_params_macro.json",
        "metrics_name": "goodness_of_fit_metrics_macro_OOS.csv",
    },
    "meso": {
        "script": ROOT / "src" / "gat" / "GAT_forecast_meso.py",
        "output_env": "FYP_GAT_MESO_OUTPUT_DIR",
        "params_env": "FYP_GAT_MESO_PARAMS_JSON",
        "params_path": ROOT / "outputs" / "gat" / "GAT_output_meso" / "optuna_best_params_meso.json",
        "metrics_name": "goodness_of_fit_metrics_meso_OOS.csv",
    },
}


def parse_csv_list(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Macro/Meso ST-GAT forecasts across seeds.")
    parser.add_argument("--seeds", default="41,42,43", help="Comma-separated random seeds.")
    parser.add_argument("--levels", default="macro,meso", help="Comma-separated levels: macro,meso.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "outputs" / "gat" / "multi_seed",
        help="Root directory for multi-seed outputs.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip a seed/level if its metrics CSV already exists.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing forecasts.",
    )
    parser.add_argument(
        "--max-epochs",
        type=int,
        default=None,
        help="Optional forecast epoch override for smoke tests.",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=None,
        help="Optional early-stopping patience override for smoke tests.",
    )
    return parser.parse_args()


def build_env(level: str, seed: int, output_dir: Path, args: argparse.Namespace) -> Dict[str, str]:
    config = LEVEL_CONFIG[level]
    env = os.environ.copy()
    env["FYP_PROJECT_ROOT"] = str(ROOT)
    env[config["output_env"]] = str(output_dir)
    env[config["params_env"]] = str(config["params_path"])
    env["FYP_GAT_SEED"] = str(seed)
    env["PYTHONPATH"] = (
        f"{ROOT / 'src' / 'gat'}:{ROOT / 'src' / 'data'}:{ROOT / 'src' / 'taxonomy'}:"
        f"{ROOT / 'src' / 'portfolio'}:{ROOT / 'src' / 'econometrics'}:{ROOT}:"
        f"{env.get('PYTHONPATH', '')}"
    )
    if args.max_epochs is not None:
        env["FYP_GAT_MAX_EPOCHS"] = str(args.max_epochs)
    if args.patience is not None:
        env["FYP_GAT_PATIENCE"] = str(args.patience)
    return env


def run_one(level: str, seed: int, output_root: Path, args: argparse.Namespace) -> None:
    config = LEVEL_CONFIG[level]
    params_path = config["params_path"]
    if not params_path.exists():
        raise FileNotFoundError(f"Best-parameter JSON not found for {level}: {params_path}")

    output_dir = output_root / level / f"seed_{seed}"
    metrics_path = output_dir / config["metrics_name"]
    if args.skip_existing and metrics_path.exists():
        print(f"Skipping {level} seed {seed}; metrics already exist: {metrics_path}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(config["script"])]
    print(f"\n==> {level} seed {seed}")
    print(" ".join(cmd))
    print(f"output: {output_dir}")
    if args.dry_run:
        return

    subprocess.run(cmd, cwd=str(ROOT), env=build_env(level, seed, output_dir, args), check=True)


def aggregate_metrics(output_root: Path, levels: Iterable[str], seeds: Iterable[int]) -> None:
    rows = []
    for level in levels:
        metrics_name = LEVEL_CONFIG[level]["metrics_name"]
        for seed in seeds:
            path = output_root / level / f"seed_{seed}" / metrics_name
            if not path.exists():
                continue
            df = pd.read_csv(path)
            df.insert(0, "Seed", seed)
            df.insert(0, "Level", level.capitalize())
            df.insert(0, "Source_File", str(path.relative_to(ROOT)))
            rows.append(df)

    if not rows:
        print("No multi-seed metrics found to aggregate.")
        return

    metrics = pd.concat(rows, ignore_index=True)
    output_root.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(output_root / "multi_seed_oos_metrics.csv", index=False)

    summary = (
        metrics.groupby(["Level", "Target", "Model"], as_index=False)[["RMSE", "MAE", "Spearman_Rank"]]
        .agg(["mean", "std", "min", "max"])
    )
    summary.columns = [
        "_".join([part for part in col if part]) if isinstance(col, tuple) else col
        for col in summary.columns
    ]
    summary.to_csv(output_root / "multi_seed_oos_summary.csv", index=False)
    print(f"\nAggregated multi-seed metrics to {output_root}")


def write_notes(output_root: Path, levels: List[str], seeds: List[int]) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "README.md").write_text(
        "\n".join(
            [
                "# Multi-Seed ST-GAT Forecasts",
                "",
                "These outputs rerun the final Macro/Meso forecast scripts across random seeds.",
                "They use the existing validation-selected Optuna parameter JSON files and do not overwrite canonical headline outputs.",
                "",
                f"Levels: {', '.join(levels)}",
                f"Seeds: {', '.join(str(seed) for seed in seeds)}",
                "",
                "Aggregate files:",
                "",
                "- `multi_seed_oos_metrics.csv`",
                "- `multi_seed_oos_summary.csv`",
                "",
                "The risk-year 2024 target-window caveat still applies before 2026-06-30.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    seeds = [int(seed) for seed in parse_csv_list(args.seeds)]
    levels = parse_csv_list(args.levels)
    unknown = sorted(set(levels).difference(LEVEL_CONFIG))
    if unknown:
        raise ValueError(f"Unknown level(s): {unknown}. Expected one or both of {sorted(LEVEL_CONFIG)}")

    output_root = args.output_root
    if not output_root.is_absolute():
        output_root = ROOT / output_root

    write_notes(output_root, levels, seeds)
    for level in levels:
        for seed in seeds:
            run_one(level, seed, output_root, args)

    if not args.dry_run:
        aggregate_metrics(output_root, levels, seeds)


if __name__ == "__main__":
    main()
