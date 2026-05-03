"""Render ST-GAT spatial attention diagnostics as a heatmap.

The script accepts either a square attention matrix or an edge-list CSV with
Source_Ticker, Target_Ticker, and Attention_Weight columns. If no input is
provided, it simulates a structured attention matrix for a 2020 cross-section so
the plotting workflow remains reproducible.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


DEFAULT_TITLE = r"ST-GAT Spatial Attention Weights ($\alpha_{ij}$) - 2020 Pandemic Shock"


def simulate_attention_matrix(n_nodes: int = 60, seed: int = 42) -> pd.DataFrame:
    """Simulate a row-normalized attention matrix with clustered shock structure."""
    rng = np.random.default_rng(seed)
    labels = [f"Firm_{i:02d}" for i in range(1, n_nodes + 1)]

    base = rng.gamma(shape=1.2, scale=0.8, size=(n_nodes, n_nodes))
    np.fill_diagonal(base, 0.0)

    # Add a modest block structure to mimic sectoral and textual-risk clusters.
    n_clusters = 4
    cluster_size = int(np.ceil(n_nodes / n_clusters))
    for cluster in range(n_clusters):
        start = cluster * cluster_size
        end = min((cluster + 1) * cluster_size, n_nodes)
        if start >= end:
            continue
        block = rng.gamma(shape=2.5, scale=1.0, size=(end - start, end - start))
        base[start:end, start:end] += block

    row_sums = base.sum(axis=1, keepdims=True)
    attention = np.divide(base, row_sums, out=np.zeros_like(base), where=row_sums > 0)
    return pd.DataFrame(attention, index=labels, columns=labels)


def load_attention_matrix(input_path: Optional[str]) -> pd.DataFrame:
    """Load an attention matrix from CSV/NPY, or simulate one when absent."""
    if input_path is None:
        return simulate_attention_matrix()

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Attention input not found: {path}")

    if path.suffix.lower() == ".npy":
        matrix = np.load(path)
        labels = [f"Firm_{i:02d}" for i in range(1, matrix.shape[0] + 1)]
        return pd.DataFrame(matrix, index=labels, columns=labels)

    df = pd.read_csv(path)
    edge_cols = {"Source_Ticker", "Target_Ticker", "Attention_Weight"}
    if edge_cols.issubset(df.columns):
        tickers = sorted(set(df["Source_Ticker"].astype(str)).union(df["Target_Ticker"].astype(str)))
        matrix = (
            df.pivot_table(
                index="Source_Ticker",
                columns="Target_Ticker",
                values="Attention_Weight",
                aggfunc="mean",
            )
            .reindex(index=tickers, columns=tickers)
            .fillna(0.0)
        )
        matrix.index = matrix.index.astype(str)
        matrix.columns = matrix.columns.astype(str)
        return matrix

    first_col = df.columns[0]
    if first_col.lower().startswith("unnamed") or not pd.api.types.is_numeric_dtype(df[first_col]):
        df = df.set_index(first_col)

    numeric = df.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    if numeric.shape[0] != numeric.shape[1]:
        raise ValueError("Attention matrix CSV must be square unless supplied as an edge list.")
    numeric.index = numeric.index.astype(str)
    numeric.columns = numeric.columns.astype(str)
    return numeric


def select_top_connected_nodes(attention: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Filter to the top connected nodes by total degree, with strength as tie-breaker."""
    matrix = attention.fillna(0.0).astype(float)
    degree = (matrix > 0).sum(axis=0).add((matrix > 0).sum(axis=1), fill_value=0.0)
    strength = matrix.sum(axis=0).add(matrix.sum(axis=1), fill_value=0.0)
    connectivity = pd.DataFrame({"degree": degree, "strength": strength})
    top_nodes = connectivity.sort_values(["degree", "strength"], ascending=False).head(top_n).index
    return matrix.loc[top_nodes, top_nodes]


def plot_attention_heatmap(attention: pd.DataFrame, output_path: str) -> None:
    """Create a publication-grade ST-GAT attention heatmap."""
    sns.set_theme(style="white", context="paper", font_scale=0.9)
    plt.rcParams.update({
        "font.family": "serif",
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
    })

    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(
        attention,
        ax=ax,
        cmap="YlGnBu",
        square=True,
        linewidths=0.15,
        linecolor="white",
        cbar_kws={"label": r"Attention weight $\alpha_{ij}$"},
    )
    ax.set_title(DEFAULT_TITLE, pad=16, fontweight="bold")
    ax.set_xlabel("Target firm $j$")
    ax.set_ylabel("Source firm $i$")
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight", dpi=300)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot ST-GAT spatial attention diagnostics.")
    parser.add_argument("--input", default=None, help="Optional CSV/NPY attention matrix or edge-list file.")
    parser.add_argument("--output", default="attention_heatmap_2020.pdf", help="Output PDF path.")
    parser.add_argument("--top-n", type=int, default=20, help="Number of most connected nodes to plot.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    attention = load_attention_matrix(args.input)
    filtered_attention = select_top_connected_nodes(attention, top_n=args.top_n)
    plot_attention_heatmap(filtered_attention, args.output)
    print(f"Saved attention heatmap to {args.output}")


if __name__ == "__main__":
    main()
