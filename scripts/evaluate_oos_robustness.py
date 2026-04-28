#!/usr/bin/env python3
"""Robust OOS forecast comparison for ST-GAT versus identity baselines.

This script evaluates existing forecast panels only. It does not retrain models
or tune hyperparameters, so it is safe to run after the test set is locked.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate robust OOS ST-GAT comparisons.")
    parser.add_argument("--seed", type=int, default=42, help="Bootstrap random seed.")
    parser.add_argument("--n-bootstrap", type=int, default=5000, help="Year-block bootstrap draws.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "gat",
        help="Output directory for robustness CSVs.",
    )
    return parser.parse_args()


def panel_paths() -> Dict[str, Path]:
    return {
        "macro": Path(
            os.getenv(
                "FYP_GAT_MACRO_PANEL_CSV",
                ROOT / "outputs/gat/GAT_output_macro/ST_GAT_vs_Baseline_Panel_macro.csv",
            )
        ),
        "meso": Path(
            os.getenv(
                "FYP_GAT_MESO_PANEL_CSV",
                ROOT / "outputs/gat/GAT_output_meso/ST_GAT_vs_Baseline_Panel_meso.csv",
            )
        ),
    }


def safe_spearman(actual: pd.Series, pred: pd.Series) -> float:
    if actual.nunique(dropna=True) <= 1 or pred.nunique(dropna=True) <= 1:
        return np.nan
    corr, _ = spearmanr(actual, pred)
    return float(corr)


def base_metrics(df: pd.DataFrame, target: str, pred_prefix: str) -> Tuple[float, float, float]:
    actual = df[f"Actual_{target}"]
    pred = df[f"{pred_prefix}_Pred_{target}"]
    rmse = float(np.sqrt(mean_squared_error(actual, pred)))
    mae = float(mean_absolute_error(actual, pred))
    rank = safe_spearman(actual, pred)
    return rmse, mae, rank


def comparison_deltas(df: pd.DataFrame, target: str) -> Dict[str, float]:
    gat_rmse, gat_mae, gat_rank = base_metrics(df, target, "GAT")
    base_rmse, base_mae, base_rank = base_metrics(df, target, "Base")
    return {
        "GAT_RMSE": gat_rmse,
        "Identity_RMSE": base_rmse,
        "RMSE_Improvement": base_rmse - gat_rmse,
        "GAT_MAE": gat_mae,
        "Identity_MAE": base_mae,
        "MAE_Improvement": base_mae - gat_mae,
        "GAT_Spearman": gat_rank,
        "Identity_Spearman": base_rank,
        "Spearman_Improvement": gat_rank - base_rank,
    }


def year_block_bootstrap(
    df: pd.DataFrame,
    target: str,
    rng: np.random.Generator,
    n_bootstrap: int,
) -> Dict[str, float]:
    years = sorted(df["Year"].dropna().astype(int).unique().tolist())
    by_year = {year: group.copy() for year, group in df.groupby("Year")}
    draws: Dict[str, List[float]] = {
        "RMSE_Improvement": [],
        "MAE_Improvement": [],
        "Spearman_Improvement": [],
    }

    if len(years) < 2:
        return {f"{key}_{suffix}": np.nan for key in draws for suffix in ("CI_Low", "CI_High", "Bootstrap_P")}

    for _ in range(n_bootstrap):
        sampled_years = rng.choice(years, size=len(years), replace=True)
        sampled = pd.concat([by_year[int(year)] for year in sampled_years], ignore_index=True)
        delta = comparison_deltas(sampled, target)
        for key in draws:
            draws[key].append(delta[key])

    out: Dict[str, float] = {}
    for key, values in draws.items():
        arr = np.asarray(values, dtype=float)
        arr = arr[np.isfinite(arr)]
        if len(arr) == 0:
            out[f"{key}_CI_Low"] = np.nan
            out[f"{key}_CI_High"] = np.nan
            out[f"{key}_Bootstrap_P"] = np.nan
            continue
        out[f"{key}_CI_Low"] = float(np.quantile(arr, 0.025))
        out[f"{key}_CI_High"] = float(np.quantile(arr, 0.975))
        p_left = float(np.mean(arr <= 0.0))
        p_right = float(np.mean(arr >= 0.0))
        out[f"{key}_Bootstrap_P"] = min(1.0, 2.0 * min(p_left, p_right))
    return out


def annual_loss_tests(df: pd.DataFrame, target: str) -> Tuple[Dict[str, float], pd.DataFrame]:
    actual = df[f"Actual_{target}"].astype(float)
    gat = df[f"GAT_Pred_{target}"].astype(float)
    base = df[f"Base_Pred_{target}"].astype(float)
    work = df[["Ticker", "Year"]].copy()
    work["Squared_Error_Improvement"] = (actual - base) ** 2 - (actual - gat) ** 2
    work["Absolute_Error_Improvement"] = (actual - base).abs() - (actual - gat).abs()

    annual = (
        work.groupby("Year", as_index=False)[["Squared_Error_Improvement", "Absolute_Error_Improvement"]]
        .mean()
        .sort_values("Year")
    )

    result: Dict[str, float] = {"Num_OOS_Years": float(len(annual))}
    for column in ("Squared_Error_Improvement", "Absolute_Error_Improvement"):
        values = annual[column].dropna()
        if len(values) >= 3 and values.std(ddof=1) > 0:
            test = stats.ttest_1samp(values, popmean=0.0)
            result[f"{column}_AnnualBlock_Mean"] = float(values.mean())
            result[f"{column}_AnnualBlock_TStat"] = float(test.statistic)
            result[f"{column}_AnnualBlock_PValue"] = float(test.pvalue)
        else:
            result[f"{column}_AnnualBlock_Mean"] = float(values.mean()) if len(values) else np.nan
            result[f"{column}_AnnualBlock_TStat"] = np.nan
            result[f"{column}_AnnualBlock_PValue"] = np.nan
    return result, annual


def load_oos_panel(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Forecast panel not found: {path}")
    df = pd.read_csv(path)
    required = {
        "Ticker",
        "Year",
        "Dataset",
        "Actual_Ret",
        "Actual_Vol",
        "GAT_Pred_Ret",
        "GAT_Pred_Vol",
        "Base_Pred_Ret",
        "Base_Pred_Vol",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {sorted(missing)}")
    df = df[df["Dataset"].astype(str).isin(["Test", "Test (OOS)"])].copy()
    if df.empty:
        raise ValueError(f"{path} contains no OOS rows.")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype(int)
    return df


def write_notes(output_dir: Path, n_bootstrap: int) -> None:
    notes = output_dir / "robust_oos_evaluation_notes.md"
    notes.write_text(
        "\n".join(
            [
                "# Robust OOS Evaluation Notes",
                "",
                "This file documents `robust_oos_evaluation.csv`.",
                "",
                "- Positive RMSE/MAE improvement means ST-GAT has lower error than the identity baseline.",
                "- Positive Spearman improvement means ST-GAT has better cross-sectional ranking.",
                "- Bootstrap intervals use OOS years as resampling blocks.",
                f"- Bootstrap draws: {n_bootstrap}.",
                "- Annual-block t-statistics are intentionally conservative and unstable with only four OOS years.",
                "- The risk-year 2024 target-window caveat still applies before 2026-06-30.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    rows = []
    annual_rows = []
    for level, path in panel_paths().items():
        df = load_oos_panel(path)
        for target in ("Ret", "Vol"):
            target_df = df.dropna(
                subset=[f"Actual_{target}", f"GAT_Pred_{target}", f"Base_Pred_{target}"]
            ).copy()
            row: Dict[str, float | str] = {
                "Level": level.capitalize(),
                "Target": target,
                "Num_FirmYears": int(len(target_df)),
            }
            row.update(comparison_deltas(target_df, target))
            row.update(year_block_bootstrap(target_df, target, rng, args.n_bootstrap))
            annual_test, annual = annual_loss_tests(target_df, target)
            row.update(annual_test)
            rows.append(row)

            annual.insert(0, "Target", target)
            annual.insert(0, "Level", level.capitalize())
            annual_rows.append(annual)

    robust_df = pd.DataFrame(rows)
    robust_df.to_csv(output_dir / "robust_oos_evaluation.csv", index=False)
    pd.concat(annual_rows, ignore_index=True).to_csv(
        output_dir / "robust_oos_annual_loss_differences.csv",
        index=False,
    )
    write_notes(output_dir, args.n_bootstrap)
    print(f"Wrote robust OOS evaluation to {output_dir}")


if __name__ == "__main__":
    main()
