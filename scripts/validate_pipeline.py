#!/usr/bin/env python3
"""Validate core research artifacts for the IEDA4920 quant finance pipeline.

The checks in this script are intentionally lightweight: they inspect existing
intermediate/output files and selected implementation contracts without
rerunning SEC extraction, taxonomy classification, model training, or portfolio
price downloads.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import tempfile
import warnings
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ieda4920_mpl"))
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

import numpy as np
import pandas as pd


TRAIN_END_YEAR = 2016
VALIDATION_END_YEAR = 2020


@dataclass
class CheckResult:
    status: str
    name: str
    message: str


class Validator:
    def __init__(self) -> None:
        self.results: List[CheckResult] = []

    def pass_(self, name: str, message: str) -> None:
        self.results.append(CheckResult("PASS", name, message))

    def warn(self, name: str, message: str) -> None:
        self.results.append(CheckResult("WARN", name, message))

    def fail(self, name: str, message: str) -> None:
        self.results.append(CheckResult("FAIL", name, message))

    def has_failures(self) -> bool:
        return any(r.status == "FAIL" for r in self.results)

    def has_warnings(self) -> bool:
        return any(r.status == "WARN" for r in self.results)

    def print_summary(self) -> None:
        for result in self.results:
            print(f"[{result.status}] {result.name}: {result.message}")

        counts = {
            status: sum(1 for r in self.results if r.status == status)
            for status in ("PASS", "WARN", "FAIL")
        }
        print(
            "\nSummary: "
            f"{counts['PASS']} passed, {counts['WARN']} warnings, {counts['FAIL']} failed"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate key IEDA4920 FYP research artifacts without rerunning training."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of scripts/.",
    )
    parser.add_argument(
        "--as-of",
        type=str,
        default=date.today().isoformat(),
        help="Date used for forward-target availability checks, in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero on warnings as well as failures.",
    )
    return parser.parse_args()


def project_paths(root: Path) -> Dict[str, Path]:
    return {
        "macro_risk": root / "data/interim/scoring_outputs/risk_scores_macro_annual.csv",
        "meso_risk": root / "data/interim/scoring_outputs/risk_scores_meso_annual.csv",
        "financial_matrix": root / "data/interim/scoring_outputs/fin_data_matrix_enhanced.csv",
        "taxonomy_json": root / "data/interim/taxonomy/taxonomy_base.json",
        "taxonomy_csv": root / "data/interim/taxonomy/hierarchical_risk_categories.csv",
        "macro_panel": root / "outputs/gat/GAT_output_macro/ST_GAT_vs_Baseline_Panel_macro.csv",
        "meso_panel": root / "outputs/gat/GAT_output_meso/ST_GAT_vs_Baseline_Panel_meso.csv",
        "macro_oos": root / "outputs/gat/GAT_output_macro/goodness_of_fit_metrics_macro_OOS.csv",
        "meso_oos": root / "outputs/gat/GAT_output_meso/goodness_of_fit_metrics_meso_OOS.csv",
        "macro_params": root / "outputs/gat/GAT_output_macro/optuna_best_params_macro.json",
        "meso_params": root / "outputs/gat/GAT_output_meso/optuna_best_params_meso.json",
        "portfolio_summary": root / "outputs/portfolio/GAT_portfolio_output/portfolio_performance_summary_ranked.csv",
        "portfolio_spread": root / "outputs/portfolio/GAT_portfolio_output/top_bottom_spread_diagnostics.csv",
        "portfolio_monthly_returns": root / "outputs/portfolio/GAT_portfolio_output/monthly_returns.csv",
        "portfolio_weights": root / "outputs/portfolio/GAT_portfolio_output/weights_GAT_LongShort_TopBottomQuintile_return_only.csv",
        "portfolio_turnover": root / "outputs/portfolio/GAT_portfolio_output/turnover_GAT_LongShort_TopBottomQuintile_return_only.csv",
        "report_tex": root / "report/Research_Report.tex",
        "report_pdf": root / "report/Research_Report.pdf",
        "report_oos_metric_figure": root / "report/figures/oos_metric_comparison.png",
        "report_graph_density_figure": root / "report/figures/graph_density_macro_meso.png",
        "report_portfolio_spread_figure": root / "report/figures/portfolio_top_bottom_spread.png",
        "robust_oos_evaluation": root / "outputs/gat/robust_oos_evaluation.csv",
        "multi_seed_metrics": root / "outputs/gat/multi_seed/multi_seed_oos_metrics.csv",
        "multi_seed_summary": root / "outputs/gat/multi_seed/multi_seed_oos_summary.csv",
        "portfolio_spread_robust_inference": root / "outputs/portfolio/GAT_portfolio_output/top_bottom_spread_robust_inference.csv",
        "portfolio_strategy_robust_inference": root / "outputs/portfolio/GAT_portfolio_output/strategy_return_robust_inference.csv",
        "dav_peak_summary": root / "outputs/econometrics/dav_peak_analysis/dav_peak_summary.csv",
        "dav_peak_summary_doc": root / "docs/dav_peak_analysis_summary.md",
    }


def check_required_files(validator: Validator, paths: Dict[str, Path]) -> None:
    missing = [f"{name} -> {path}" for name, path in paths.items() if not path.exists()]
    if missing:
        validator.fail("file path existence", "missing required artifact(s): " + "; ".join(missing))
    else:
        validator.pass_("file path existence", f"all {len(paths)} canonical artifacts are present")


def check_nonempty_artifacts(validator: Validator, paths: Dict[str, Path]) -> None:
    labels = [
        "report_tex",
        "report_pdf",
        "report_oos_metric_figure",
        "report_graph_density_figure",
        "report_portfolio_spread_figure",
        "robust_oos_evaluation",
        "multi_seed_metrics",
        "multi_seed_summary",
        "portfolio_spread_robust_inference",
        "portfolio_strategy_robust_inference",
        "dav_peak_summary",
        "dav_peak_summary_doc",
    ]
    empty = [
        f"{label} -> {paths[label]}"
        for label in labels
        if paths[label].exists() and paths[label].stat().st_size == 0
    ]
    if empty:
        validator.fail("report artifact nonempty", "empty artifact(s): " + "; ".join(empty))
    else:
        validator.pass_("report artifact nonempty", "report source, PDF, and generated report figures are nonempty")


def read_csv(validator: Validator, name: str, path: Path, **kwargs: object) -> Optional[pd.DataFrame]:
    if not path.exists():
        validator.fail(f"read {name}", f"file not found: {path}")
        return None
    try:
        return pd.read_csv(path, **kwargs)
    except Exception as exc:  # pragma: no cover - defensive reporting path
        validator.fail(f"read {name}", f"could not read {path}: {exc}")
        return None


def require_columns(
    validator: Validator,
    name: str,
    df: Optional[pd.DataFrame],
    required: Iterable[str],
) -> bool:
    if df is None:
        return False
    missing = sorted(set(required).difference(df.columns))
    if missing:
        validator.fail(f"{name} schema", f"missing required columns: {missing}")
        return False
    validator.pass_(f"{name} schema", f"required columns present: {sorted(required)}")
    return True


def check_no_duplicate_keys(
    validator: Validator,
    name: str,
    df: Optional[pd.DataFrame],
    keys: List[str],
) -> None:
    if df is None or not set(keys).issubset(df.columns):
        return
    duplicated = int(df.duplicated(keys).sum())
    if duplicated:
        validator.fail(f"{name} keys", f"{duplicated} duplicate row(s) by {keys}")
    else:
        validator.pass_(f"{name} keys", f"no duplicate rows by {keys}")


def check_no_missing_required_values(
    validator: Validator,
    name: str,
    df: Optional[pd.DataFrame],
    required: Iterable[str],
) -> None:
    if df is None:
        return
    columns = [c for c in required if c in df.columns]
    if not columns:
        return
    missing = df[columns].isna().sum()
    missing = missing[missing > 0]
    if missing.empty:
        validator.pass_(f"{name} required values", f"no missing values in {columns}")
    else:
        validator.fail(
            f"{name} required values",
            "missing required values: " + ", ".join(f"{k}={int(v)}" for k, v in missing.items()),
        )


def numeric_year_series(df: pd.DataFrame) -> pd.Series:
    return pd.to_numeric(df["Year"], errors="coerce").astype("Int64")


def check_risk_scores(validator: Validator, name: str, df: Optional[pd.DataFrame]) -> None:
    if not require_columns(validator, name, df, {"Ticker", "Year"}):
        return
    assert df is not None
    check_no_duplicate_keys(validator, name, df, ["Ticker", "Year"])
    check_no_missing_required_values(validator, name, df, ["Ticker", "Year"])

    risk_cols = [
        c
        for c in df.select_dtypes(include=[np.number]).columns
        if c not in {"Year"}
    ]
    if not risk_cols:
        validator.fail(f"{name} risk exposure columns", "no numeric risk exposure columns found")
        return

    exposures = df[risk_cols].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    row_sums = exposures.sum(axis=1)
    positive = row_sums > 0
    if not positive.any():
        validator.fail(f"{name} risk exposure normalization", "all exposure rows sum to zero")
        return

    max_dev = float((row_sums[positive] - 1.0).abs().max())
    if max_dev <= 1e-4:
        validator.pass_(
            f"{name} risk exposure normalization",
            f"{len(risk_cols)} exposure columns; positive rows sum to one within {max_dev:.2e}",
        )
    elif max_dev <= 1e-2:
        validator.warn(
            f"{name} risk exposure normalization",
            f"positive rows are close to one but max absolute deviation is {max_dev:.4f}",
        )
    else:
        validator.fail(
            f"{name} risk exposure normalization",
            f"positive rows do not look normalized; max absolute deviation is {max_dev:.4f}",
        )


def check_financial_matrix(validator: Validator, df: Optional[pd.DataFrame]) -> None:
    required = {
        "Year",
        "Ticker",
        "Vol",
        "Downside_Vol",
        "MA_200_Ratio",
        "Momentum_11M",
        "Dollar_Volume",
        "Log_Dollar_Volume",
        "Target_Ret",
        "Target_Vol",
        "SP500_Ret",
        "SP500_Vol",
        "VIX_Avg",
        "VIX_Change",
        "TenY_Yield_Avg",
        "TenY_Yield_Change",
    }
    if not require_columns(validator, "financial matrix", df, required):
        return
    assert df is not None
    check_no_duplicate_keys(validator, "financial matrix", df, ["Ticker", "Year"])
    check_no_missing_required_values(validator, "financial matrix targets", df, ["Ticker", "Year", "Target_Ret", "Target_Vol"])

    feature_cols = sorted(required.difference({"Year", "Ticker", "Target_Ret", "Target_Vol"}))
    missing_features = int(df[feature_cols].isna().sum().sum())
    if missing_features:
        validator.warn(
            "financial matrix feature completeness",
            f"{missing_features} missing feature value(s); graph builder should impute with training medians only",
        )
    else:
        validator.pass_("financial matrix feature completeness", "no missing values in required feature columns")


def check_prediction_panel(validator: Validator, name: str, df: Optional[pd.DataFrame]) -> None:
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
    if not require_columns(validator, f"{name} prediction panel", df, required):
        return
    assert df is not None
    check_no_duplicate_keys(validator, f"{name} prediction panel", df, ["Ticker", "Year"])
    check_no_missing_required_values(validator, f"{name} prediction panel", df, required)

    labels = set(df["Dataset"].dropna().astype(str).unique())
    allowed = {"Train", "Validation", "Test", "Test (OOS)"}
    unexpected = sorted(labels.difference(allowed))
    if unexpected:
        validator.fail(f"{name} dataset labels", f"unexpected Dataset value(s): {unexpected}")
    else:
        validator.pass_(f"{name} dataset labels", f"labels are within {sorted(allowed)}")


def check_chronological_split(validator: Validator, name: str, df: Optional[pd.DataFrame]) -> None:
    if df is None or not {"Year", "Dataset"}.issubset(df.columns):
        return
    work = df[["Year", "Dataset"]].copy()
    work["Year"] = pd.to_numeric(work["Year"], errors="coerce")
    work = work.dropna(subset=["Year", "Dataset"])
    work["Year"] = work["Year"].astype(int)

    violations = []
    train_bad = work[(work["Dataset"] == "Train") & (work["Year"] > TRAIN_END_YEAR)]
    val_bad = work[(work["Dataset"] == "Validation") & ((work["Year"] <= TRAIN_END_YEAR) | (work["Year"] > VALIDATION_END_YEAR))]
    test_labels = work["Dataset"].isin(["Test", "Test (OOS)"])
    test_bad = work[test_labels & (work["Year"] <= VALIDATION_END_YEAR)]
    if not train_bad.empty:
        violations.append(f"Train contains years above {TRAIN_END_YEAR}: {sorted(train_bad['Year'].unique())}")
    if not val_bad.empty:
        violations.append(f"Validation outside 2017-{VALIDATION_END_YEAR}: {sorted(val_bad['Year'].unique())}")
    if not test_bad.empty:
        violations.append(f"Test contains years at/before {VALIDATION_END_YEAR}: {sorted(test_bad['Year'].unique())}")

    if violations:
        validator.fail(f"{name} chronological split", "; ".join(violations))
    else:
        ranges = work.groupby("Dataset")["Year"].agg(["min", "max"]).to_dict("index")
        validator.pass_(f"{name} chronological split", f"Dataset year ranges are chronological: {ranges}")


def add_project_import_paths(root: Path) -> None:
    for rel in ("src/gat", "src/portfolio", "src/data"):
        path = str(root / rel)
        if path not in sys.path:
            sys.path.insert(0, path)


def check_train_only_preprocessing(
    validator: Validator,
    root: Path,
    risk_df: Optional[pd.DataFrame],
    fin_df: Optional[pd.DataFrame],
) -> None:
    if risk_df is None or fin_df is None:
        return
    try:
        add_project_import_paths(root)
        from GAT_data_pipeline import FinancialGraphBuilder
    except Exception as exc:
        validator.fail("feature standardization import", f"could not import FinancialGraphBuilder: {exc}")
        return

    try:
        builder = FinancialGraphBuilder(risk_df, fin_df, train_year_end=TRAIN_END_YEAR)
        train_df = fin_df[pd.to_numeric(fin_df["Year"], errors="coerce") <= TRAIN_END_YEAR]
        train_features = (
            train_df[builder.feature_cols]
            .apply(pd.to_numeric, errors="coerce")
            .replace([np.inf, -np.inf], np.nan)
        )
        medians = train_features.median(axis=0).fillna(0.0)
        means = train_features.mean(axis=0).fillna(0.0)
        stds = train_features.std(axis=0, ddof=0).replace(0.0, 1.0).fillna(1.0)

        med_ok = np.allclose(builder.feature_medians_.values, medians[builder.feature_cols].values, atol=1e-12)
        mean_ok = np.allclose(builder.feature_means_.values, means[builder.feature_cols].values, atol=1e-12)
        std_ok = np.allclose(builder.feature_stds_.values, stds[builder.feature_cols].values, atol=1e-12)
    except Exception as exc:
        validator.fail("feature standardization train-only fit", f"could not validate preprocessing: {exc}")
        return

    if med_ok and mean_ok and std_ok:
        validator.pass_(
            "feature standardization train-only fit",
            f"medians/means/stds are fitted only on Year <= {TRAIN_END_YEAR}",
        )
    else:
        validator.fail(
            "feature standardization train-only fit",
            "builder preprocessing statistics differ from Year <= 2016 recomputation",
        )


def read_tau(path: Path, fallback: float = 0.85) -> float:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return float(data["best_params"]["tau"])
    except Exception:
        return fallback


def check_graph_contracts(
    validator: Validator,
    root: Path,
    risk_df: Optional[pd.DataFrame],
    fin_df: Optional[pd.DataFrame],
    params_path: Path,
    label: str,
) -> None:
    if risk_df is None or fin_df is None:
        return
    try:
        add_project_import_paths(root)
        from GAT_data_pipeline import FinancialGraphBuilder
    except Exception as exc:
        validator.fail(f"{label} graph import", f"could not import FinancialGraphBuilder: {exc}")
        return

    try:
        tau = read_tau(params_path)
        builder = FinancialGraphBuilder(risk_df, fin_df, train_year_end=TRAIN_END_YEAR)
        snapshots, masks = builder.build_signal(tau=tau)
    except Exception as exc:
        validator.fail(f"{label} graph build", f"could not build graph snapshots: {exc}")
        return

    expected_mask_shape = (len(builder.years), builder.num_nodes)
    if tuple(masks.shape) != expected_mask_shape:
        validator.fail(f"{label} active mask shape", f"expected {expected_mask_shape}, got {tuple(masks.shape)}")
    else:
        validator.pass_(f"{label} active mask shape", f"mask shape is {expected_mask_shape}")

    shape_errors = []
    loop_errors = []
    for year, snapshot in zip(builder.years, snapshots):
        if snapshot.edge_index.shape[0] != 2:
            shape_errors.append(f"{year}: edge_index first dimension {snapshot.edge_index.shape[0]}")
        if snapshot.edge_attr.shape[0] != snapshot.edge_index.shape[1]:
            shape_errors.append(f"{year}: edge_attr length does not match edge count")
        if tuple(snapshot.x.shape) != (builder.num_nodes, builder.in_features):
            shape_errors.append(f"{year}: x shape {tuple(snapshot.x.shape)}")
        if tuple(snapshot.y.shape) != (builder.num_nodes, 2):
            shape_errors.append(f"{year}: y shape {tuple(snapshot.y.shape)}")

        first_edges = snapshot.edge_index[:, : builder.num_nodes]
        first_weights = snapshot.edge_attr[: builder.num_nodes]
        diagonal_first = bool((first_edges[0] == first_edges[1]).all().item())
        covers_all_nodes = set(first_edges[0].detach().cpu().numpy().tolist()) == set(range(builder.num_nodes))
        unit_weight = bool(np.allclose(first_weights.detach().cpu().numpy(), 1.0))
        if not (diagonal_first and covers_all_nodes and unit_weight):
            loop_errors.append(str(year))

    if shape_errors:
        validator.fail(f"{label} graph tensor shapes", "; ".join(shape_errors[:5]))
    else:
        validator.pass_(f"{label} graph tensor shapes", f"{len(snapshots)} annual snapshots have consistent tensors")

    if loop_errors:
        validator.fail(f"{label} graph self-loop logic", f"self-loop contract failed for years: {loop_errors[:10]}")
    else:
        validator.pass_(
            f"{label} graph self-loop logic",
            "each snapshot starts with one unit-weight self-loop per global node",
        )

    try:
        identity_snapshots, _ = builder.build_identity_signal()
    except Exception as exc:
        validator.fail(f"{label} identity baseline build", f"could not build identity snapshots: {exc}")
        return

    bad_identity = []
    for year, snapshot in zip(builder.years, identity_snapshots):
        edge_index = snapshot.edge_index.detach().cpu().numpy()
        edge_attr = snapshot.edge_attr.detach().cpu().numpy()
        if edge_index.shape != (2, builder.num_nodes):
            bad_identity.append(f"{year}: edge_index shape {edge_index.shape}")
            continue
        if not np.array_equal(edge_index[0], edge_index[1]):
            bad_identity.append(f"{year}: off-diagonal identity edge found")
        if not np.allclose(edge_attr, 1.0):
            bad_identity.append(f"{year}: identity edge weights are not all one")

    if bad_identity:
        validator.fail(f"{label} identity baseline", "; ".join(bad_identity[:5]))
    else:
        validator.pass_(
            f"{label} identity baseline",
            "identity baseline contains only diagonal unit-weight edges",
        )


def check_target_alignment(
    validator: Validator,
    root: Path,
    fin_df: Optional[pd.DataFrame],
    as_of: pd.Timestamp,
) -> None:
    try:
        add_project_import_paths(root)
        from generate_fin_data import FinancialDataEngineer
    except Exception as exc:
        validator.fail("target alignment import", f"could not import FinancialDataEngineer: {exc}")
        return

    expected = {
        "feat_start": pd.Timestamp("2021-07-01"),
        "feat_end": pd.Timestamp("2022-06-30"),
        "mom_end": pd.Timestamp("2022-05-31"),
        "target_start": pd.Timestamp("2022-07-01"),
        "target_end": pd.Timestamp("2023-06-30"),
    }
    windows = FinancialDataEngineer.make_windows(2021)
    actual = {
        "feat_start": windows.feat_start,
        "feat_end": windows.feat_end,
        "mom_end": windows.mom_end,
        "target_start": windows.target_start,
        "target_end": windows.target_end,
    }
    if actual == expected:
        validator.pass_("target alignment convention", "Year=t uses July t to June t+1 features and July t+1 to June t+2 targets")
    else:
        validator.fail("target alignment convention", f"unexpected 2021 window mapping: {actual}")

    if fin_df is None or "Year" not in fin_df.columns:
        return
    years = sorted(pd.to_numeric(fin_df["Year"], errors="coerce").dropna().astype(int).unique().tolist())
    incomplete = [
        year
        for year in years
        if FinancialDataEngineer.make_windows(int(year)).target_end > as_of
    ]
    if incomplete:
        validator.warn(
            "forward target availability",
            "target window(s) extend beyond "
            f"{as_of.date()}: {incomplete}. Treat any realized results for these years as unavailable until the windows close.",
        )
    else:
        validator.pass_(
            "forward target availability",
            f"all target windows in the financial matrix close on or before {as_of.date()}",
        )


def check_portfolio_contracts(
    validator: Validator,
    root: Path,
    weights_df: Optional[pd.DataFrame],
    monthly_returns_df: Optional[pd.DataFrame],
) -> None:
    try:
        add_project_import_paths(root)
        from portfolio_backtest import PredictionWeightedPortfolioBacktester
    except Exception as exc:
        validator.fail("portfolio import", f"could not import PredictionWeightedPortfolioBacktester: {exc}")
        return

    start, end = PredictionWeightedPortfolioBacktester.signal_window(2021)
    if start == pd.Timestamp("2022-07-31") and end == pd.Timestamp("2023-06-30"):
        validator.pass_("portfolio signal window", "Year=2021 predictions map to July 2022 through June 2023 month-ends")
    else:
        validator.fail("portfolio signal window", f"unexpected Year=2021 signal window: {start} to {end}")

    cost_rate = PredictionWeightedPortfolioBacktester._one_way_cost_rate(10.0, 5.0)
    if abs(cost_rate - 0.0015) <= 1e-12:
        validator.pass_("transaction cost application", "10 bps cost + 5 bps slippage converts to a 0.0015 one-way turnover cost")
    else:
        validator.fail("transaction cost application", f"unexpected cost rate for 10+5 bps: {cost_rate}")

    if weights_df is None:
        return
    required = {"Rebalance_Date", "Holding_Return_Date", "Ticker", "Weight", "Score_Method", "Model_Prefix"}
    if not require_columns(validator, "portfolio weights", weights_df, required):
        return

    work = weights_df.copy()
    work["Rebalance_Date"] = pd.to_datetime(work["Rebalance_Date"], errors="coerce")
    work["Holding_Return_Date"] = pd.to_datetime(work["Holding_Return_Date"], errors="coerce")
    if work[["Rebalance_Date", "Holding_Return_Date"]].isna().any().any():
        validator.fail("portfolio rebalance timing", "some weight rows have invalid rebalance/holding dates")
        return

    same_or_before = int((work["Holding_Return_Date"] <= work["Rebalance_Date"]).sum())
    if same_or_before:
        validator.fail("portfolio rebalance timing", f"{same_or_before} row(s) earn returns on or before the rebalance date")
    else:
        validator.pass_("portfolio rebalance timing", "all holding return dates occur after the rebalance dates")

    if monthly_returns_df is None or "Date" not in monthly_returns_df.columns:
        return
    returns = monthly_returns_df.copy()
    returns["Date"] = pd.to_datetime(returns["Date"], errors="coerce")
    returns = returns.dropna(subset=["Date"]).set_index("Date").sort_index()
    return_dates = returns.index
    pair_errors = []
    for rebalance_date, holding_return_date in work[["Rebalance_Date", "Holding_Return_Date"]].drop_duplicates().itertuples(index=False):
        pos = return_dates.searchsorted(rebalance_date, side="right")
        if pos >= len(return_dates):
            continue
        expected_date = return_dates[pos]
        if holding_return_date != expected_date:
            pair_errors.append(f"{rebalance_date.date()} -> {holding_return_date.date()}, expected {expected_date.date()}")
    if pair_errors:
        validator.fail("portfolio next-month return mapping", "; ".join(pair_errors[:5]))
    else:
        validator.pass_("portfolio next-month return mapping", "weight files use the next available monthly return date after each rebalance")

    missing_return_count = 0
    sampled_rows = 0
    return_cols = set(returns.columns.astype(str))
    for row in work.itertuples(index=False):
        ticker = str(row.Ticker)
        if ticker not in return_cols:
            missing_return_count += 1
            continue
        value = returns.at[row.Holding_Return_Date, ticker] if row.Holding_Return_Date in returns.index else np.nan
        if pd.isna(value):
            missing_return_count += 1
        sampled_rows += 1
    if missing_return_count:
        validator.warn(
            "portfolio held-ticker return availability",
            f"{missing_return_count} of {sampled_rows} held rows have missing next-month returns; current code fills missing returns with 0.0",
        )
    else:
        validator.pass_("portfolio held-ticker return availability", f"all {sampled_rows} held rows have realized next-month returns")


def check_portfolio_outputs(
    validator: Validator,
    summary_df: Optional[pd.DataFrame],
    spread_df: Optional[pd.DataFrame],
    turnover_df: Optional[pd.DataFrame],
) -> None:
    require_columns(
        validator,
        "portfolio summary",
        summary_df,
        {"Strategy", "Total_Return", "Annualized_Return", "Annualized_Volatility", "Sharpe", "Num_Months"},
    )
    require_columns(
        validator,
        "top-bottom spread diagnostics",
        spread_df,
        {"Model", "Score_Method", "Mean_Monthly_TopMinusBottom", "Annualized_TopMinusBottom", "Num_Months"},
    )
    if turnover_df is not None:
        first_col = turnover_df.columns[0] if len(turnover_df.columns) else None
        if first_col is None or len(turnover_df.columns) < 2:
            validator.fail("portfolio turnover output", "turnover CSV should contain dates and turnover values")
        else:
            values = pd.to_numeric(turnover_df.iloc[:, 1], errors="coerce")
            if values.dropna().empty:
                validator.fail("portfolio turnover output", "turnover CSV contains no numeric turnover values")
            elif (values.dropna() < 0).any():
                validator.fail("portfolio turnover output", "turnover values must be nonnegative")
            else:
                validator.pass_("portfolio turnover output", "turnover values are numeric and nonnegative")


def check_multi_seed_outputs(
    validator: Validator,
    metrics_df: Optional[pd.DataFrame],
    summary_df: Optional[pd.DataFrame],
) -> None:
    if require_columns(
        validator,
        "multi-seed metrics",
        metrics_df,
        {"Level", "Seed", "Target", "Model", "RMSE", "MAE", "Spearman_Rank"},
    ):
        assert metrics_df is not None
        seeds = sorted(pd.to_numeric(metrics_df["Seed"], errors="coerce").dropna().astype(int).unique().tolist())
        levels = sorted(metrics_df["Level"].dropna().astype(str).unique().tolist())
        if len(seeds) < 3:
            validator.warn("multi-seed coverage", f"fewer than 3 seeds found: {seeds}")
        else:
            validator.pass_("multi-seed coverage", f"levels={levels}, seeds={seeds}")

    require_columns(
        validator,
        "multi-seed summary",
        summary_df,
        {"Level", "Target", "Model", "RMSE_mean", "RMSE_std", "MAE_mean", "Spearman_Rank_mean"},
    )


def check_dav_peak_outputs(
    validator: Validator,
    root: Path,
    summary_df: Optional[pd.DataFrame],
) -> None:
    if not require_columns(
        validator,
        "DAV peak summary",
        summary_df,
        {"ticker", "macro_risk", "meso_risk", "improvement_pct", "figure", "ocr_text"},
    ):
        return
    assert summary_df is not None

    figures = sorted((root / "outputs/econometrics/dav_peak_analysis").glob("*_multi_peak.png"))
    if len(summary_df) != len(figures):
        validator.warn(
            "DAV peak summary coverage",
            f"summary has {len(summary_df)} row(s), but {len(figures)} peak figure(s) are present",
        )
    else:
        validator.pass_("DAV peak summary coverage", f"{len(figures)} peak figure(s) represented")

    improvements = pd.to_numeric(summary_df["improvement_pct"], errors="coerce")
    missing = int(improvements.isna().sum())
    if missing:
        validator.warn("DAV peak OCR completeness", f"{missing} improvement percentage(s) could not be parsed")
    else:
        positive = int((improvements > 0).sum())
        negative = int((improvements < 0).sum())
        validator.pass_(
            "DAV peak OCR completeness",
            f"all {len(improvements)} improvement percentages parsed; positive={positive}, negative={negative}",
        )


def check_deterministic_seed_smoke(validator: Validator) -> None:
    try:
        import torch
    except Exception as exc:
        validator.fail("deterministic seed smoke test", f"could not import torch: {exc}")
        return

    def sample(seed: int) -> Tuple[float, float, float]:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        return (
            random.random(),
            float(np.random.random()),
            float(torch.rand(1).item()),
        )

    first = sample(42)
    second = sample(42)
    third = sample(43)
    if first == second and first != third:
        validator.pass_("deterministic seed smoke test", "Python, NumPy, and Torch RNG streams repeat under a fixed seed")
    else:
        validator.fail("deterministic seed smoke test", "fixed seed did not reproduce RNG samples")


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    as_of = pd.Timestamp(args.as_of)
    validator = Validator()

    paths = project_paths(root)
    check_required_files(validator, paths)
    check_nonempty_artifacts(validator, paths)

    macro_risk = read_csv(validator, "macro risk scores", paths["macro_risk"])
    meso_risk = read_csv(validator, "meso risk scores", paths["meso_risk"])
    fin_matrix = read_csv(validator, "financial matrix", paths["financial_matrix"])
    macro_panel = read_csv(validator, "macro prediction panel", paths["macro_panel"])
    meso_panel = read_csv(validator, "meso prediction panel", paths["meso_panel"])
    portfolio_summary = read_csv(validator, "portfolio summary", paths["portfolio_summary"])
    portfolio_spread = read_csv(validator, "portfolio spread diagnostics", paths["portfolio_spread"])
    portfolio_weights = read_csv(validator, "portfolio weights", paths["portfolio_weights"])
    portfolio_monthly_returns = read_csv(validator, "portfolio monthly returns", paths["portfolio_monthly_returns"])
    portfolio_turnover = read_csv(validator, "portfolio turnover", paths["portfolio_turnover"])
    multi_seed_metrics = read_csv(validator, "multi-seed metrics", paths["multi_seed_metrics"])
    multi_seed_summary = read_csv(validator, "multi-seed summary", paths["multi_seed_summary"])
    dav_peak_summary = read_csv(validator, "DAV peak summary", paths["dav_peak_summary"])

    check_risk_scores(validator, "macro risk scores", macro_risk)
    check_risk_scores(validator, "meso risk scores", meso_risk)
    check_financial_matrix(validator, fin_matrix)
    check_prediction_panel(validator, "macro", macro_panel)
    check_prediction_panel(validator, "meso", meso_panel)
    check_chronological_split(validator, "macro", macro_panel)
    check_chronological_split(validator, "meso", meso_panel)
    check_train_only_preprocessing(validator, root, meso_risk, fin_matrix)
    check_graph_contracts(validator, root, meso_risk, fin_matrix, paths["meso_params"], "meso")
    check_target_alignment(validator, root, fin_matrix, as_of)
    check_portfolio_outputs(validator, portfolio_summary, portfolio_spread, portfolio_turnover)
    check_portfolio_contracts(validator, root, portfolio_weights, portfolio_monthly_returns)
    check_multi_seed_outputs(validator, multi_seed_metrics, multi_seed_summary)
    check_dav_peak_outputs(validator, root, dav_peak_summary)
    check_deterministic_seed_smoke(validator)

    validator.print_summary()
    if validator.has_failures() or (args.strict and validator.has_warnings()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
