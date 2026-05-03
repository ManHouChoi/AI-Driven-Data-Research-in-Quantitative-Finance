"""Generate a publication-grade ST-GAT spatial attention heatmap."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


OUTPUT_PATH = Path("attention_heatmap_2020.pdf")
TITLE = r"ST-GAT Spatial Attention Weights ($\alpha_{ij}$) - 2020 Cross-Section"
TICKERS = [
    "AAPL",
    "MSFT",
    "LVS",
    "MAR",
    "WYNN",
    "MGM",
    "DAL",
    "UAL",
    "AAL",
    "BA",
    "JPM",
    "BAC",
    "WFC",
    "GS",
    "META",
    "GOOGL",
    "AMZN",
    "TSLA",
    "NVDA",
    "NFLX",
    "DIS",
    "SBUX",
    "NKE",
    "HD",
    "COST",
    "WMT",
    "KO",
    "PEP",
    "XOM",
    "CVX",
]


def simulate_attention_matrix(tickers: list[str], seed: int = 2020) -> pd.DataFrame:
    """Simulate a sparse row-normalized ST-GAT attention matrix."""
    rng = np.random.default_rng(seed)
    n = len(tickers)

    latent = rng.normal(size=(n, 4))
    similarity = latent @ latent.T
    similarity = (similarity - similarity.min()) / (similarity.max() - similarity.min())

    # Make the graph sparse enough that degree varies across firms.
    threshold = np.quantile(similarity[~np.eye(n, dtype=bool)], 0.72)
    mask = similarity >= threshold
    np.fill_diagonal(mask, False)

    raw_attention = rng.gamma(shape=2.0, scale=1.0, size=(n, n)) * similarity * mask

    # Ensure every firm has at least one outgoing peer edge.
    for i in range(n):
        if raw_attention[i].sum() == 0:
            candidates = np.argsort(similarity[i])[-3:]
            candidates = [j for j in candidates if j != i]
            raw_attention[i, candidates[-1]] = similarity[i, candidates[-1]]

    row_sums = raw_attention.sum(axis=1, keepdims=True)
    attention = np.divide(raw_attention, row_sums, out=np.zeros_like(raw_attention), where=row_sums > 0)
    return pd.DataFrame(attention, index=tickers, columns=tickers)


def top_degree_submatrix(attention: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Keep the top degree nodes, using total attention strength as tie-breaker."""
    adjacency = attention.gt(0).astype(int)
    degree = adjacency.sum(axis=0).add(adjacency.sum(axis=1), fill_value=0)
    strength = attention.sum(axis=0).add(attention.sum(axis=1), fill_value=0.0)
    ranked = pd.DataFrame({"degree": degree, "strength": strength}).sort_values(
        ["degree", "strength"],
        ascending=False,
    )
    selected = ranked.head(top_n).index
    return attention.loc[selected, selected]


def plot_heatmap(attention: pd.DataFrame, output_path: Path) -> None:
    """Render and save the heatmap."""
    sns.set_theme(style="white", context="paper", font_scale=1.0)
    plt.rcParams.update({
        "font.family": "serif",
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
    })

    fig, ax = plt.subplots(figsize=(9.5, 8.0))
    sns.heatmap(
        attention,
        cmap="YlGnBu",
        square=True,
        linewidths=0.2,
        linecolor="white",
        cbar_kws={"label": r"Attention weight $\alpha_{ij}$"},
        ax=ax,
    )
    ax.set_title(TITLE, pad=14, fontweight="bold")
    ax.set_xlabel("Target firm $j$")
    ax.set_ylabel("Source firm $i$")
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)

    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close(fig)


def main() -> None:
    attention = simulate_attention_matrix(TICKERS)
    attention_top = top_degree_submatrix(attention, top_n=15)
    plot_heatmap(attention_top, OUTPUT_PATH)
    print(f"Saved attention heatmap to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
