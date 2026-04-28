#!/usr/bin/env python3
"""Generate report figures from verified local CSV outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate report-local figures from current CSV outputs."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "report" / "figures",
        help="Directory for generated PNG files. Defaults to report/figures.",
    )
    return parser.parse_args()


def read_csv(rel_path: str) -> pd.DataFrame:
    path = ROOT / rel_path
    if not path.exists():
        raise FileNotFoundError(f"Required source file not found: {path}")
    return pd.read_csv(path)


def save_current(fig_dir: Path, name: str) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    out = fig_dir / name
    plt.tight_layout()
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"saved {out}")


def plot_oos_metric_comparison(fig_dir: Path) -> None:
    frames = []
    for level, rel_path in [
        ("Macro", "outputs/gat/GAT_output_macro/goodness_of_fit_metrics_macro_OOS.csv"),
        ("Meso", "outputs/gat/GAT_output_meso/goodness_of_fit_metrics_meso_OOS.csv"),
    ]:
        df = read_csv(rel_path)
        df = df[df["Target"].isin(["Ret", "Vol"])].copy()
        df["Level"] = level
        frames.append(df)

    data = pd.concat(frames, ignore_index=True)
    data["Label"] = data["Level"] + " " + data["Target"] + " " + data["Model"].replace({"Identity Baseline": "Identity"})

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    colors = data["Model"].map({"ST-GAT": "#2f6f9f", "Identity Baseline": "#9a9a9a"})

    for ax, metric, title in [
        (axes[0], "RMSE", "OOS RMSE by Target"),
        (axes[1], "Spearman_Rank", "OOS Spearman Rank by Target"),
    ]:
        ordered = data.sort_values(["Level", "Target", "Model"])
        ax.barh(ordered["Label"], ordered[metric], color=colors.loc[ordered.index])
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_title(title)
        ax.set_xlabel(metric.replace("_", " "))
        ax.grid(axis="x", linestyle="--", alpha=0.35)

    fig.suptitle("ST-GAT vs. Identity Baseline: OOS Forecast Metrics", fontsize=13, fontweight="bold")
    save_current(fig_dir, "oos_metric_comparison.png")


def plot_graph_density(fig_dir: Path) -> None:
    macro = read_csv("outputs/gat/GAT_output_macro/graph_diagnostics_macro_forecast_tau.csv")
    meso = read_csv("outputs/gat/GAT_output_meso/graph_diagnostics_meso_forecast_tau.csv")
    macro = macro[macro["Year"].between(2021, 2024)].copy()
    meso = meso[meso["Year"].between(2021, 2024)].copy()

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].plot(macro["Year"], macro["Num_OffDiagonal_Edges"], marker="o", label="Macro", color="#b55239")
    axes[0].plot(meso["Year"], meso["Num_OffDiagonal_Edges"], marker="o", label="Meso", color="#2f6f9f")
    axes[0].set_title("Off-Diagonal Directed Edges")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Edges")
    axes[0].legend()
    axes[0].grid(True, linestyle="--", alpha=0.35)

    axes[1].plot(
        macro["Year"],
        100 * macro["Density_Among_Active_Risk_Nodes"],
        marker="o",
        label="Macro",
        color="#b55239",
    )
    axes[1].plot(
        meso["Year"],
        100 * meso["Density_Among_Active_Risk_Nodes"],
        marker="o",
        label="Meso",
        color="#2f6f9f",
    )
    axes[1].set_title("Density Among Active Risk Nodes")
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Density (%)")
    axes[1].legend()
    axes[1].grid(True, linestyle="--", alpha=0.35)

    fig.suptitle("Macro vs. Meso OOS Graph Density", fontsize=13, fontweight="bold")
    save_current(fig_dir, "graph_density_macro_meso.png")


def plot_top_bottom_spread(fig_dir: Path) -> None:
    spread = read_csv("outputs/portfolio/GAT_portfolio_output/top_bottom_spread_diagnostics.csv")
    keep = spread[spread["Score_Method"].eq("return_only")].copy()
    keep["Annualized_TopMinusBottom"] = 100 * keep["Annualized_TopMinusBottom"]
    keep["Label"] = keep["Model"].replace({"ST-GAT": "Meso ST-GAT", "Identity Baseline": "Identity"})

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bars = ax.bar(
        keep["Label"],
        keep["Annualized_TopMinusBottom"],
        color=["#2f6f9f" if model == "ST-GAT" else "#9a9a9a" for model in keep["Model"]],
    )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Annualized top-minus-bottom spread (%)")
    ax.set_title("Return-Only Signal Ranking Diagnostic")
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    for bar, row in zip(bars, keep.itertuples(index=False)):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"t={row.Spread_TStat:.2f}\np={row.Spread_PValue:.3f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    save_current(fig_dir, "portfolio_top_bottom_spread.png")


def main() -> None:
    args = parse_args()
    fig_dir = args.output_dir
    if not fig_dir.is_absolute():
        fig_dir = ROOT / fig_dir
    plot_oos_metric_comparison(fig_dir)
    plot_graph_density(fig_dir)
    plot_top_bottom_spread(fig_dir)


if __name__ == "__main__":
    main()
