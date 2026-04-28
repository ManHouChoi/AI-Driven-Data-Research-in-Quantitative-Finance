#!/usr/bin/env python3
"""Portfolio inference addendum for existing backtest outputs."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, List

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate robust portfolio inference outputs.")
    parser.add_argument(
        "--portfolio-dir",
        type=Path,
        default=Path(
            os.getenv(
                "FYP_PORTFOLIO_OUTPUT_DIR",
                ROOT / "outputs/portfolio/GAT_portfolio_output",
            )
        ),
        help="Portfolio output directory.",
    )
    parser.add_argument("--hac-lags", type=int, default=3, help="Newey-West/HAC max lags.")
    return parser.parse_args()


def bh_q_values(p_values: Iterable[float]) -> List[float]:
    values = np.asarray(list(p_values), dtype=float)
    q = np.full(values.shape, np.nan, dtype=float)
    finite = np.isfinite(values)
    if not finite.any():
        return q.tolist()

    finite_p = values[finite]
    order = np.argsort(finite_p)
    ranked = finite_p[order]
    n = len(ranked)
    adjusted = np.empty(n, dtype=float)
    running = 1.0
    for idx in range(n - 1, -1, -1):
        rank = idx + 1
        running = min(running, ranked[idx] * n / rank)
        adjusted[idx] = running
    q_finite = np.empty(n, dtype=float)
    q_finite[order] = np.minimum(adjusted, 1.0)
    q[finite] = q_finite
    return q.tolist()


def hac_mean_test(series: pd.Series, maxlags: int) -> dict:
    y = pd.to_numeric(series, errors="coerce").dropna().astype(float)
    if len(y) < 3:
        return {"Mean": float(y.mean()) if len(y) else np.nan, "HAC_SE": np.nan, "HAC_TStat": np.nan, "HAC_PValue": np.nan}

    X = np.ones((len(y), 1))
    model = sm.OLS(y.values, X).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    mean = float(model.params[0])
    se = float(model.bse[0])
    t_stat = float(model.tvalues[0])
    p_value = float(model.pvalues[0])
    return {"Mean": mean, "HAC_SE": se, "HAC_TStat": t_stat, "HAC_PValue": p_value}


def simple_t_test(series: pd.Series) -> dict:
    y = pd.to_numeric(series, errors="coerce").dropna().astype(float)
    if len(y) < 2 or y.std(ddof=1) <= 0:
        return {"Simple_TStat": np.nan, "Simple_PValue": np.nan}
    test = stats.ttest_1samp(y, popmean=0.0)
    return {"Simple_TStat": float(test.statistic), "Simple_PValue": float(test.pvalue)}


def infer_spreads(portfolio_dir: Path, hac_lags: int) -> pd.DataFrame:
    rows = []
    for path in sorted(portfolio_dir.glob("top_bottom_monthly_spreads_*.csv")):
        df = pd.read_csv(path)
        if df.empty or "Top_Minus_Bottom" not in df.columns:
            continue
        series = df["Top_Minus_Bottom"]
        row = {
            "Source_File": path.name,
            "Model": df["Model"].iloc[0] if "Model" in df.columns else np.nan,
            "Model_Prefix": df["Model_Prefix"].iloc[0] if "Model_Prefix" in df.columns else np.nan,
            "Score_Method": df["Score_Method"].iloc[0] if "Score_Method" in df.columns else np.nan,
            "Num_Months": int(series.dropna().shape[0]),
            "Annualized_Mean_Spread": float(series.mean() * 12.0),
            "Positive_Spread_Rate": float((series > 0).mean()),
        }
        row.update(simple_t_test(series))
        row.update(hac_mean_test(series, hac_lags))
        rows.append(row)

    result = pd.DataFrame(rows)
    if not result.empty:
        result["HAC_QValue_BH"] = bh_q_values(result["HAC_PValue"])
        result = result.sort_values(
            ["Annualized_Mean_Spread", "HAC_TStat"],
            ascending=[False, False],
            na_position="last",
        )
    return result


def infer_strategy_returns(portfolio_dir: Path, hac_lags: int) -> pd.DataFrame:
    rows = []
    for path in sorted(portfolio_dir.glob("returns_*.csv")):
        df = pd.read_csv(path)
        if df.empty or len(df.columns) < 2:
            continue
        strategy = path.stem.replace("returns_", "")
        series = pd.to_numeric(df.iloc[:, 1], errors="coerce")
        row = {
            "Strategy": strategy,
            "Source_File": path.name,
            "Num_Months": int(series.dropna().shape[0]),
            "Annualized_Mean_Return": float(series.mean() * 12.0),
            "Positive_Return_Rate": float((series > 0).mean()),
        }
        row.update(simple_t_test(series))
        row.update(hac_mean_test(series, hac_lags))
        rows.append(row)

    result = pd.DataFrame(rows)
    if not result.empty:
        result["HAC_QValue_BH"] = bh_q_values(result["HAC_PValue"])
        result = result.sort_values(
            ["Annualized_Mean_Return", "HAC_TStat"],
            ascending=[False, False],
            na_position="last",
        )
    return result


def write_notes(portfolio_dir: Path, hac_lags: int) -> None:
    (portfolio_dir / "portfolio_inference_notes.md").write_text(
        "\n".join(
            [
                "# Portfolio Inference Notes",
                "",
                "These inference files are computed from existing monthly backtest outputs.",
                "",
                f"- HAC/Newey-West max lags: {hac_lags}.",
                "- `HAC_QValue_BH` applies Benjamini-Hochberg correction within each output table.",
                "- The tests are diagnostics for an academic backtest, not investment advice.",
                "- The risk-year 2024 target-window caveat still applies before 2026-06-30.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    portfolio_dir = args.portfolio_dir
    if not portfolio_dir.is_absolute():
        portfolio_dir = ROOT / portfolio_dir
    if not portfolio_dir.exists():
        raise FileNotFoundError(f"Portfolio output directory not found: {portfolio_dir}")

    spread = infer_spreads(portfolio_dir, args.hac_lags)
    spread.to_csv(portfolio_dir / "top_bottom_spread_robust_inference.csv", index=False)

    returns = infer_strategy_returns(portfolio_dir, args.hac_lags)
    returns.to_csv(portfolio_dir / "strategy_return_robust_inference.csv", index=False)

    write_notes(portfolio_dir, args.hac_lags)
    print(f"Wrote portfolio inference outputs to {portfolio_dir}")


if __name__ == "__main__":
    main()
