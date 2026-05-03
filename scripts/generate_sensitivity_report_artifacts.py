#!/usr/bin/env python3
"""Generate manuscript figures for taxonomy, topology, and ST-GAT sensitivity evidence."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA


ROOT = Path(__file__).resolve().parents[1]
REPORT_FIGURES = ROOT / "report" / "figures"
SENSITIVITY_OUT = ROOT / "outputs" / "taxonomy" / "sensitivity"


@dataclass(frozen=True)
class VariantArtifact:
    name: str
    label: str
    taxonomy_root: Path
    gat_macro_dir: Path | None
    gat_meso_dir: Path | None
    portfolio_dir: Path | None
    order: int


def normalize_category_name(name: str) -> str:
    text = re.sub(r"\.\d+$", "", str(name))
    text = re.sub(r"\*\*", "", text)
    return re.sub(r"\s+", " ", text).strip()


def short_label(name: str, width: int = 34) -> str:
    text = normalize_category_name(name)
    return text if len(text) <= width else f"{text[: width - 3]}..."


def prettify_variant_name(name: str) -> str:
    if name == "default":
        return "Default"
    match = re.fullmatch(r"theta(\d{3})", name)
    if match:
        return rf"$\theta={int(match.group(1)) / 100:.2f}$"
    match = re.fullmatch(r"macro(\d+)", name)
    if match:
        return rf"Macro min={match.group(1)}"
    match = re.fullmatch(r"meso(\d+)", name)
    if match:
        return rf"Meso min={match.group(1)}"
    match = re.fullmatch(r"umap(\d+)", name)
    if match:
        return rf"UMAP k={match.group(1)}"
    return name.replace("_", " ")


def existing_dir(path: Path | None) -> Path | None:
    return path if path is not None and path.exists() else None


def candidate_gat_dir(name: str, level: str) -> Path | None:
    root = ROOT / "outputs" / "gat" / "taxonomy_sensitivity"
    candidates = [root / f"{name}_{level}"]
    if level == "meso":
        candidates.append(root / name)  # Backward-compatible location used by the theta040 artifact run.
    for path in candidates:
        metric = path / f"goodness_of_fit_metrics_{level}_OOS.csv"
        if metric.exists():
            return path
    return None


def discover_variants() -> list[VariantArtifact]:
    variants: list[VariantArtifact] = [
        VariantArtifact(
            name="default",
            label="Default",
            taxonomy_root=ROOT / "May 2 update" / "taxonomy",
            gat_macro_dir=existing_dir(ROOT / "outputs" / "gat" / "GAT_output_macro"),
            gat_meso_dir=existing_dir(ROOT / "outputs" / "gat" / "GAT_output_meso"),
            portfolio_dir=existing_dir(ROOT / "outputs" / "portfolio" / "GAT_portfolio_output"),
            order=0,
        )
    ]

    sensitivity_root = ROOT / "outputs" / "taxonomy" / "sensitivity"
    if sensitivity_root.exists():
        for root in sorted(sensitivity_root.iterdir()):
            if not root.is_dir() or not (root / "output_risk_factor_2024").exists():
                continue
            variants.append(
                VariantArtifact(
                    name=root.name,
                    label=prettify_variant_name(root.name),
                    taxonomy_root=root,
                    gat_macro_dir=candidate_gat_dir(root.name, "macro"),
                    gat_meso_dir=candidate_gat_dir(root.name, "meso"),
                    portfolio_dir=existing_dir(ROOT / "outputs" / "portfolio" / "taxonomy_sensitivity" / root.name),
                    order=1,
                )
            )
    return sorted(variants, key=lambda item: (item.order, item.name))


def taxonomy_file(year_dir: Path, year: int) -> Path:
    return year_dir / ("taxonomy_base.json" if year == 2006 else "taxonomy_evolved.json")


def vector_file(year_dir: Path, year: int) -> Path:
    return year_dir / ("base_year_vectors.csv" if year == 2006 else "risk_vectors.csv")


def load_parent_map(taxonomy_path: Path) -> dict[str, str]:
    payload = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for meso in payload.get("meso_categories", []):
        name = normalize_category_name(meso.get("name", ""))
        parent = normalize_category_name(meso.get("parent_macro", "Unmapped Macro Risk"))
        if name:
            mapping.setdefault(name, parent or "Unmapped Macro Risk")
    return mapping


def load_taxonomy_logs(variant: VariantArtifact) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for year in range(2006, 2025):
        path = variant.taxonomy_root / f"output_risk_factor_{year}" / "run_log.json"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            log = json.load(handle)
        actions = log.get("actions_taken", [])
        action_counts = {
            action: sum(1 for item in actions if item.get("Action") == action)
            for action in ["ADD", "MERGE", "REORGANIZE"]
        }
        rows.append(
            {
                "Variant": variant.label,
                "Variant_Name": variant.name,
                "Year": year,
                "Total_Risk_Factors": log.get("total_new_factors", log.get("total_risk_factors", 0)),
                "Deviation_Percent": log.get("deviation_percent", np.nan),
                "Final_Meso_Categories": log.get("final_meso_categories", log.get("meso_clusters", np.nan)),
                "ADD": action_counts["ADD"],
                "MERGE": action_counts["MERGE"],
                "REORGANIZE": action_counts["REORGANIZE"],
                "Macro_Coverage_Percent": log.get("macro_coverage_percent", np.nan),
                "Meso_Coverage_Percent": log.get("meso_coverage_percent", np.nan),
            }
        )
    return pd.DataFrame(rows)


def load_final_taxonomy(variant: VariantArtifact) -> dict:
    path = taxonomy_file(variant.taxonomy_root / "output_risk_factor_2024", 2024)
    return json.loads(path.read_text(encoding="utf-8"))


def load_assignment_coverage(variant: VariantArtifact, year: int = 2024) -> pd.DataFrame:
    year_dir = variant.taxonomy_root / f"output_risk_factor_{year}"
    classified_path = year_dir / "classified_risk_factors.csv"
    if year == 2006:
        classified_path = year_dir / "hierarchical_risk_categories.csv"
    if not classified_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(classified_path, usecols=lambda c: c in {"Company", "macro_category", "meso_category"})
    if "meso_category" not in df.columns:
        return pd.DataFrame()
    df["meso_category"] = df["meso_category"].map(normalize_category_name)
    if "macro_category" not in df.columns:
        df["macro_category"] = np.nan
    df["macro_category"] = df["macro_category"].map(normalize_category_name)
    df.loc[df["macro_category"].str.lower().isin({"nan", "none"}), "macro_category"] = np.nan

    parent_map = load_parent_map(taxonomy_file(year_dir, year))
    missing_macro = df["macro_category"].isna() | df["macro_category"].eq("")
    df.loc[missing_macro, "macro_category"] = df.loc[missing_macro, "meso_category"].map(parent_map)
    df["macro_category"] = df["macro_category"].fillna("Unmapped Macro Risk")

    counts = (
        df.groupby("macro_category", as_index=False)
        .size()
        .rename(columns={"macro_category": "Macro_Category", "size": "Paragraph_Count"})
        .sort_values("Paragraph_Count", ascending=False)
    )
    counts["Variant"] = variant.label
    counts["Variant_Name"] = variant.name
    counts["Year"] = year
    counts["Share"] = counts["Paragraph_Count"] / max(counts["Paragraph_Count"].sum(), 1)
    return counts[["Variant", "Variant_Name", "Year", "Macro_Category", "Paragraph_Count", "Share"]]


def metric_value(metrics_path: Path, model: str, target: str, metric: str) -> float:
    df = pd.read_csv(metrics_path)
    row = df[(df["Model"] == model) & (df["Target"] == target)]
    if row.empty:
        return np.nan
    return float(row.iloc[0][metric])


def graph_average(graph_path: Path) -> tuple[float, float]:
    df = pd.read_csv(graph_path)
    density_col = "Density_Among_Active_Risk_Nodes"
    if density_col not in df.columns:
        density_col = "Graph_Density" if "Graph_Density" in df.columns else "Density"
    oos = df[df["Year"].between(2021, 2024)].copy()
    return float(oos[density_col].mean()), float(oos["Num_OffDiagonal_Edges"].mean())


def portfolio_metric(portfolio_dir: Path | None, strategy: str, metric: str) -> float:
    if portfolio_dir is None:
        return np.nan
    path = portfolio_dir / "portfolio_performance_summary_ranked.csv"
    if not path.exists():
        return np.nan
    df = pd.read_csv(path)
    row = df[df["Strategy"] == strategy]
    return float(row.iloc[0][metric]) if not row.empty else np.nan


def spread_metric(portfolio_dir: Path | None, model: str, score: str, metric: str) -> float:
    if portfolio_dir is None:
        return np.nan
    path = portfolio_dir / "top_bottom_spread_diagnostics.csv"
    if not path.exists():
        return np.nan
    df = pd.read_csv(path)
    row = df[(df["Model"] == model) & (df["Score_Method"] == score)]
    return float(row.iloc[0][metric]) if not row.empty else np.nan


def downstream_rows(variants: list[VariantArtifact]) -> pd.DataFrame:
    rows = []
    for variant in variants:
        for level, gat_dir in [("Macro", variant.gat_macro_dir), ("Meso", variant.gat_meso_dir)]:
            if gat_dir is None:
                continue
            metrics_path = gat_dir / f"goodness_of_fit_metrics_{level.lower()}_OOS.csv"
            graph_path = gat_dir / f"graph_diagnostics_{level.lower()}_forecast_tau.csv"
            if not metrics_path.exists() or not graph_path.exists():
                continue
            density, edges = graph_average(graph_path)
            rows.append(
                {
                    "Variant": variant.label,
                    "Variant_Name": variant.name,
                    "Level": level,
                    "Averaged_RMSE_Improvement": metric_value(
                        metrics_path, "Identity Baseline", "Averaged (Ret & Vol)", "RMSE"
                    )
                    - metric_value(metrics_path, "ST-GAT", "Averaged (Ret & Vol)", "RMSE"),
                    "Averaged_MAE_Improvement": metric_value(
                        metrics_path, "Identity Baseline", "Averaged (Ret & Vol)", "MAE"
                    )
                    - metric_value(metrics_path, "ST-GAT", "Averaged (Ret & Vol)", "MAE"),
                    "Averaged_Spearman_Improvement": metric_value(
                        metrics_path, "ST-GAT", "Averaged (Ret & Vol)", "Spearman_Rank"
                    )
                    - metric_value(metrics_path, "Identity Baseline", "Averaged (Ret & Vol)", "Spearman_Rank"),
                    "Vol_RMSE_Improvement": metric_value(metrics_path, "Identity Baseline", "Vol", "RMSE")
                    - metric_value(metrics_path, "ST-GAT", "Vol", "RMSE"),
                    "Return_RMSE_Improvement": metric_value(metrics_path, "Identity Baseline", "Ret", "RMSE")
                    - metric_value(metrics_path, "ST-GAT", "Ret", "RMSE"),
                    "Mean_OOS_Graph_Density": density,
                    "Mean_OOS_OffDiagonal_Edges": edges,
                    "Return_Only_LongShort_Sharpe": portfolio_metric(
                        variant.portfolio_dir, "GAT_LongShort_TopBottomQuintile_return_only", "Sharpe"
                    )
                    if level == "Meso"
                    else np.nan,
                    "Return_Only_Spread": spread_metric(
                        variant.portfolio_dir, "ST-GAT", "return_only", "Annualized_TopMinusBottom"
                    )
                    if level == "Meso"
                    else np.nan,
                }
            )
    return pd.DataFrame(rows)


def plot_taxonomy_evolution(logs: pd.DataFrame) -> None:
    if logs.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.7), dpi=180)
    palette = plt.cm.tab10(np.linspace(0, 1, max(logs["Variant"].nunique(), 3)))

    for color, (label, group) in zip(palette, logs.groupby("Variant", sort=False)):
        axes[0].plot(group["Year"], group["Final_Meso_Categories"], marker="o", linewidth=2.0, markersize=3.4, label=label, color=color)
        axes[1].plot(group["Year"], group["Deviation_Percent"], marker="o", linewidth=2.0, markersize=3.4, label=label, color=color)

    axes[0].set_title("Meso-category accumulation")
    axes[0].set_ylabel("Final Meso categories")
    axes[1].set_title("Annual semantic-deviation rate")
    axes[1].set_ylabel("Deviation rate (%)")
    for ax in axes:
        ax.set_xlabel("Risk year")
        ax.grid(alpha=0.25)
        ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(REPORT_FIGURES / "taxonomy_category_evolution_default_theta040.png", bbox_inches="tight")
    plt.close(fig)


def plot_convergence(variants: list[VariantArtifact]) -> None:
    sources = [(variant.label, variant.gat_meso_dir) for variant in variants if variant.gat_meso_dir is not None]
    sources = [(label, path) for label, path in sources if (path / "training_convergence_meso.csv").exists()][:4]
    if not sources:
        return

    fig, axes = plt.subplots(1, len(sources), figsize=(6.3 * len(sources), 4.6), dpi=180, sharey=True)
    if len(sources) == 1:
        axes = [axes]
    for ax, (title, path) in zip(axes, sources):
        df = pd.read_csv(path / "training_convergence_meso.csv")
        ax.plot(df["epoch"], df["gat_val_loss"], label="ST-GAT validation", color="#214f80", linewidth=2.0)
        ax.plot(df["epoch"], df["base_val_loss"], label="Identity validation", color="#8a8a8a", linewidth=1.9)
        gat_best = df.loc[df["gat_val_loss"].idxmin()]
        base_best = df.loc[df["base_val_loss"].idxmin()]
        ax.scatter([gat_best["epoch"]], [gat_best["gat_val_loss"]], color="#214f80", s=32)
        ax.scatter([base_best["epoch"]], [base_best["base_val_loss"]], color="#8a8a8a", s=32)
        ax.set_title(title)
        ax.set_xlabel("Epoch")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Validation Huber loss")
    axes[-1].legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(REPORT_FIGURES / "stgat_convergence_default_theta040.png", bbox_inches="tight")
    plt.close(fig)


def plot_downstream_dashboard(df: pd.DataFrame) -> None:
    if df.empty:
        return
    df.to_csv(ROOT / "outputs" / "gat" / "taxonomy_downstream_sensitivity_summary.csv", index=False)

    completed = df.sort_values(["Variant_Name", "Level"]).copy()
    completed["Label"] = completed["Variant"] + " " + completed["Level"]
    colors = completed["Level"].map({"Macro": "#8a8a8a", "Meso": "#214f80"}).fillna("#b45f06")

    fig, axes = plt.subplots(2, 2, figsize=(13.2, 8.3), dpi=180)
    charts = [
        ("Averaged RMSE improvement", "Averaged_RMSE_Improvement", "RMSE reduction"),
        ("Volatility RMSE improvement", "Vol_RMSE_Improvement", "RMSE reduction"),
        ("Mean OOS graph density", "Mean_OOS_Graph_Density", "Directed edge density"),
        ("Mean OOS off-diagonal edges", "Mean_OOS_OffDiagonal_Edges", "Directed edges"),
    ]
    for ax, (title, column, ylabel) in zip(axes.ravel(), charts):
        ax.bar(completed["Label"], completed[column], color=colors, width=0.62)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=25, labelsize=8)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(REPORT_FIGURES / "taxonomy_downstream_sensitivity_dashboard.png", bbox_inches="tight")
    plt.close(fig)


def plot_macro_coverage(coverage: pd.DataFrame) -> None:
    if coverage.empty:
        return
    coverage.to_csv(SENSITIVITY_OUT / "taxonomy_macro_coverage_2024.csv", index=False)
    top_categories = (
        coverage.groupby("Macro_Category")["Share"].sum().sort_values(ascending=False).head(10).index.tolist()
    )
    work = coverage[coverage["Macro_Category"].isin(top_categories)].copy()
    work["Macro_Category"] = pd.Categorical(work["Macro_Category"], categories=top_categories[::-1], ordered=True)

    variants = work["Variant"].drop_duplicates().tolist()
    fig, ax = plt.subplots(figsize=(11.2, 6.4), dpi=180)
    y = np.arange(len(top_categories))
    width = 0.34 if len(variants) <= 2 else 0.22
    offsets = np.linspace(-width * (len(variants) - 1) / 2, width * (len(variants) - 1) / 2, len(variants))
    palette = plt.cm.Set2(np.linspace(0, 1, max(len(variants), 3)))
    for offset, color, variant in zip(offsets, palette, variants):
        values = (
            work[work["Variant"] == variant]
            .set_index("Macro_Category")
            .reindex(top_categories[::-1])["Share"]
            .fillna(0.0)
            .values
        )
        ax.barh(y + offset, 100 * values, height=width, color=color, label=variant)
    ax.set_yticks(y)
    ax.set_yticklabels([short_label(cat, 46) for cat in top_categories[::-1]], fontsize=8)
    ax.set_xlabel("Share of 2024 assigned risk paragraphs (%)")
    ax.set_title("Risk-category coverage by final taxonomy")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(REPORT_FIGURES / "taxonomy_macro_coverage_comparison.png", bbox_inches="tight")
    plt.close(fig)


def best_variant_for_topology(variants: list[VariantArtifact]) -> VariantArtifact:
    for variant in variants:
        if variant.name == "theta040":
            return variant
    return variants[0]


def plot_taxonomy_topology(variant: VariantArtifact) -> None:
    taxonomy = load_final_taxonomy(variant)
    coverage = load_assignment_coverage(variant)
    if coverage.empty:
        return
    parent_counts = coverage.set_index("Macro_Category")["Paragraph_Count"].to_dict()
    top_parents = coverage.head(9)["Macro_Category"].tolist()
    meso_rows = []
    parent_map = {}
    for meso in taxonomy.get("meso_categories", []):
        parent = normalize_category_name(meso.get("parent_macro", "Unmapped Macro Risk"))
        name = normalize_category_name(meso.get("name", ""))
        if parent in top_parents and name:
            parent_map[name] = parent

    year_dir = variant.taxonomy_root / "output_risk_factor_2024"
    classified = pd.read_csv(year_dir / "classified_risk_factors.csv", usecols=lambda c: c in {"meso_category"})
    classified["meso_category"] = classified["meso_category"].map(normalize_category_name)
    meso_counts = classified["meso_category"].value_counts().to_dict()
    for meso, parent in parent_map.items():
        meso_rows.append({"Meso": meso, "Parent": parent, "Count": int(meso_counts.get(meso, 0))})
    meso_df = pd.DataFrame(meso_rows)
    meso_df = (
        meso_df.sort_values(["Parent", "Count"], ascending=[True, False])
        .groupby("Parent")
        .head(4)
        .copy()
    )
    meso_df.to_csv(SENSITIVITY_OUT / "taxonomy_topology_meso_nodes_2024.csv", index=False)

    graph = nx.Graph()
    for parent in top_parents:
        graph.add_node(parent, kind="macro", count=parent_counts.get(parent, 0))
    for row in meso_df.itertuples(index=False):
        graph.add_node(row.Meso, kind="meso", count=row.Count)
        graph.add_edge(row.Parent, row.Meso)

    pos = nx.spring_layout(graph, seed=42, k=0.75, iterations=250)
    fig, ax = plt.subplots(figsize=(13.2, 8.2), dpi=180)
    macro_nodes = [n for n, attrs in graph.nodes(data=True) if attrs["kind"] == "macro"]
    meso_nodes = [n for n, attrs in graph.nodes(data=True) if attrs["kind"] == "meso"]
    nx.draw_networkx_edges(graph, pos, ax=ax, width=0.8, alpha=0.35, edge_color="#555555")
    nx.draw_networkx_nodes(
        graph,
        pos,
        nodelist=macro_nodes,
        node_size=[900 + 0.18 * graph.nodes[n]["count"] for n in macro_nodes],
        node_color="#214f80",
        alpha=0.88,
        ax=ax,
        label="Macro",
    )
    nx.draw_networkx_nodes(
        graph,
        pos,
        nodelist=meso_nodes,
        node_size=[80 + 0.55 * math.sqrt(max(graph.nodes[n]["count"], 1)) for n in meso_nodes],
        node_color="#d8a03d",
        alpha=0.78,
        ax=ax,
        label="Meso",
    )
    labels = {node: short_label(node, 30 if graph.nodes[node]["kind"] == "macro" else 24) for node in graph.nodes}
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=7, ax=ax)
    ax.set_title(f"Topological structure of the {variant.label} 2024 taxonomy")
    ax.legend(frameon=False, loc="lower left")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(REPORT_FIGURES / "taxonomy_topology_theta040.png", bbox_inches="tight")
    plt.close(fig)


def load_macro_profiles(variant: VariantArtifact) -> pd.DataFrame:
    records = []
    for year in range(2006, 2025):
        year_dir = variant.taxonomy_root / f"output_risk_factor_{year}"
        path = vector_file(year_dir, year)
        tax_path = taxonomy_file(year_dir, year)
        if not path.exists() or not tax_path.exists():
            continue
        parent_map = load_parent_map(tax_path)
        df = pd.read_csv(path)
        company_col = "Company" if "Company" in df.columns else df.columns[0]
        df[company_col] = df[company_col].astype(str).str.upper().str.strip()
        risk_cols = [col for col in df.columns if col != company_col]
        macro_blocks = {}
        for col in risk_cols:
            parent = parent_map.get(normalize_category_name(col), "Unmapped Macro Risk")
            macro_blocks.setdefault(parent, pd.Series(0.0, index=df.index))
            macro_blocks[parent] = macro_blocks[parent] + pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        macro_df = pd.DataFrame(macro_blocks)
        macro_df.insert(0, "Company", df[company_col])
        macro_df.insert(1, "Year", year)
        records.append(macro_df)
    if not records:
        return pd.DataFrame()
    return pd.concat(records, ignore_index=True, sort=False).fillna(0.0)


def load_score_panel(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "Ticker" not in df.columns or "Year" not in df.columns:
        return pd.DataFrame()
    df["Ticker"] = df["Ticker"].astype(str).str.upper().str.strip()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    return df.dropna(subset=["Year"]).copy()


def top_category(row: pd.Series, excluded: set[str]) -> tuple[str, float]:
    values = row.drop(labels=list(excluded), errors="ignore")
    values = pd.to_numeric(values, errors="coerce").fillna(0.0)
    if values.empty:
        return "", 0.0
    category = str(values.idxmax())
    return category, float(values.loc[category])


def build_lvs_case_summary(variant: VariantArtifact) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    macro = load_score_panel(variant.taxonomy_root / "risk_scores_macro_annual.csv")
    meso = load_score_panel(variant.taxonomy_root / "risk_scores_meso_annual.csv")
    if macro.empty or meso.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    macro_lvs = macro[macro["Ticker"] == "LVS"].sort_values("Year").copy()
    meso_lvs = meso[meso["Ticker"] == "LVS"].sort_values("Year").copy()
    if macro_lvs.empty or meso_lvs.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    meso_cols = [c for c in meso.columns if c not in {"Ticker", "Year"}]
    summary_rows = []
    previous_vector: np.ndarray | None = None
    for row in meso_lvs.itertuples(index=False):
        year = int(row.Year)
        meso_row = meso_lvs[meso_lvs["Year"] == year].iloc[0]
        macro_row = macro_lvs[macro_lvs["Year"] == year].iloc[0]
        top_macro, top_macro_share = top_category(macro_row, {"Ticker", "Year"})
        top_meso, top_meso_share = top_category(meso_row, {"Ticker", "Year"})

        year_panel = meso[meso["Year"] == year].copy()
        x = meso_row[meso_cols].to_numpy(dtype=float)
        peer = ""
        peer_sim = np.nan
        if len(year_panel) > 1 and np.linalg.norm(x) > 0:
            matrix = year_panel[meso_cols].to_numpy(dtype=float)
            denom = np.linalg.norm(matrix, axis=1) * np.linalg.norm(x)
            sims = np.divide(matrix @ x, denom, out=np.zeros(len(year_panel)), where=denom > 0)
            year_panel = year_panel.assign(Cosine=sims)
            peer_row = year_panel[year_panel["Ticker"] != "LVS"].sort_values("Cosine", ascending=False).head(1)
            if not peer_row.empty:
                peer = str(peer_row.iloc[0]["Ticker"])
                peer_sim = float(peer_row.iloc[0]["Cosine"])

        distance = np.nan
        if previous_vector is not None:
            denom = np.linalg.norm(previous_vector) * np.linalg.norm(x)
            distance = float(1.0 - (previous_vector @ x / denom)) if denom > 0 else np.nan
        previous_vector = x

        summary_rows.append(
            {
                "Ticker": "LVS",
                "Year": year,
                "Top_Macro_Category": top_macro,
                "Top_Macro_Share": top_macro_share,
                "Top_Meso_Category": top_meso,
                "Top_Meso_Share": top_meso_share,
                "Vector_Distance_From_Previous": distance,
                "Nearest_Peer": peer,
                "Nearest_Peer_Cosine": peer_sim,
            }
        )

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(SENSITIVITY_OUT / "taxonomy_lvs_dynamic_case_summary.csv", index=False)

    top_meso = (
        meso_lvs[meso_cols]
        .loc[meso_lvs["Year"] >= 2012]
        .sum(axis=0)
        .sort_values(ascending=False)
        .head(7)
        .index.tolist()
    )
    meso_traj = meso_lvs[["Ticker", "Year", *top_meso]].copy()
    meso_traj.to_csv(SENSITIVITY_OUT / "taxonomy_lvs_meso_trajectory.csv", index=False)

    peer_rows = []
    for year in summary["Year"]:
        year_panel = meso[meso["Year"] == year].copy()
        lvs = year_panel[year_panel["Ticker"] == "LVS"]
        if lvs.empty:
            continue
        x = lvs.iloc[0][meso_cols].to_numpy(dtype=float)
        matrix = year_panel[meso_cols].to_numpy(dtype=float)
        denom = np.linalg.norm(matrix, axis=1) * np.linalg.norm(x)
        sims = np.divide(matrix @ x, denom, out=np.zeros(len(year_panel)), where=denom > 0)
        for row in year_panel.assign(Cosine=sims).query("Ticker != 'LVS'").nlargest(5, "Cosine").itertuples(index=False):
            peer_rows.append({"Year": int(year), "Peer": row.Ticker, "Cosine": float(row.Cosine)})
    peers = pd.DataFrame(peer_rows)
    peers.to_csv(SENSITIVITY_OUT / "taxonomy_lvs_nearest_peers.csv", index=False)
    return summary, meso_traj, peers


def plot_lvs_dynamic_case_study(variant: VariantArtifact) -> None:
    summary, meso_traj, _ = build_lvs_case_summary(variant)
    macro = load_score_panel(variant.taxonomy_root / "risk_scores_macro_annual.csv")
    if summary.empty or meso_traj.empty or macro.empty:
        return

    macro_lvs = macro[macro["Ticker"] == "LVS"].sort_values("Year").copy()
    macro_cols = [c for c in macro_lvs.columns if c not in {"Ticker", "Year"}]
    top_macros = macro_lvs[macro_cols].sum(axis=0).sort_values(ascending=False).head(5).index.tolist()
    macro_plot = macro_lvs[["Year", *top_macros]].copy()
    macro_plot["Other"] = 1.0 - macro_plot[top_macros].sum(axis=1)
    years = macro_plot["Year"].astype(int).to_numpy()

    fig, axes = plt.subplots(3, 1, figsize=(12.6, 11.0), dpi=180, sharex=True)

    colors = ["#214f80", "#d8a03d", "#4f8c6b", "#b55239", "#6f5b8f", "#b9b9b9"]
    axes[0].stackplot(
        years,
        [macro_plot[col].to_numpy(dtype=float) for col in [*top_macros, "Other"]],
        labels=[short_label(col, 30) for col in [*top_macros, "Other"]],
        colors=colors,
        alpha=0.88,
    )
    axes[0].set_ylabel("Macro exposure")
    axes[0].set_ylim(0, 1)
    axes[0].set_title(f"LVS dynamic taxonomy EDA under the {variant.label} taxonomy")
    axes[0].legend(ncol=2, fontsize=7.5, frameon=False, loc="upper left")

    for col, color in zip([c for c in meso_traj.columns if c not in {"Ticker", "Year"}], colors):
        axes[1].plot(meso_traj["Year"], meso_traj[col], marker="o", linewidth=1.6, label=short_label(col, 38), color=color)
    axes[1].set_ylabel("Meso exposure")
    axes[1].grid(axis="y", linestyle="--", alpha=0.25)
    axes[1].legend(ncol=2, fontsize=7.2, frameon=False, loc="upper left")

    axes[2].bar(
        summary["Year"].astype(int),
        summary["Vector_Distance_From_Previous"].fillna(0.0),
        color="#b55239",
        alpha=0.74,
        label="Vector distance from previous available filing",
    )
    ax2 = axes[2].twinx()
    ax2.plot(
        summary["Year"].astype(int),
        summary["Nearest_Peer_Cosine"],
        color="#214f80",
        marker="s",
        linewidth=1.7,
        label="Nearest-peer cosine",
    )
    axes[2].set_ylabel("Cosine distance")
    ax2.set_ylabel("Cosine similarity")
    axes[2].set_xlabel("Risk disclosure year")
    axes[2].grid(axis="y", linestyle="--", alpha=0.25)
    for _, row in summary.dropna(subset=["Nearest_Peer_Cosine"]).iterrows():
        if int(row["Year"]) in {2014, 2018, 2019, 2022, 2024}:
            ax2.annotate(
                str(row["Nearest_Peer"]),
                (int(row["Year"]), float(row["Nearest_Peer_Cosine"])),
                textcoords="offset points",
                xytext=(0, 7),
                ha="center",
                fontsize=7,
                color="#214f80",
            )
    handles1, labels1 = axes[2].get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    axes[2].legend(handles1 + handles2, labels1 + labels2, frameon=False, fontsize=8, loc="upper left")

    event_labels = {
        2019: "MBS expansion\nagreement",
        2020: "COVID\nshock",
        2021: "Las Vegas\nsale",
        2022: "Macao\nconcession",
    }
    for ax in axes:
        for year, label in event_labels.items():
            ax.axvline(year, color="#333333", linestyle=":", linewidth=0.8, alpha=0.55)
        ax.set_xlim(min(years) - 0.5, max(years) + 0.5)
    ymax = axes[0].get_ylim()[1]
    for year, label in event_labels.items():
        axes[0].text(year + 0.05, ymax * 0.96, label, fontsize=7, va="top", color="#333333")

    fig.tight_layout()
    fig.savefig(REPORT_FIGURES / "taxonomy_lvs_dynamic_eda.png", bbox_inches="tight")
    plt.close(fig)


def plot_lvs_vector_network(variant: VariantArtifact) -> None:
    summary, _, peers = build_lvs_case_summary(variant)
    meso = load_score_panel(variant.taxonomy_root / "risk_scores_meso_annual.csv")
    if summary.empty or peers.empty or meso.empty:
        return

    meso_cols = [c for c in meso.columns if c not in {"Ticker", "Year"}]
    matrix = meso[meso_cols].to_numpy(dtype=float)
    coords = PCA(n_components=2, random_state=42).fit_transform(matrix)
    coords_df = meso[["Ticker", "Year"]].copy()
    coords_df["PC1"] = coords[:, 0]
    coords_df["PC2"] = coords[:, 1]

    lvs_coords = coords_df[coords_df["Ticker"] == "LVS"].sort_values("Year")
    selected_years = [2014, 2018, 2019, 2022, 2024]
    nearest = peers[peers["Year"].isin(selected_years)].sort_values(["Year", "Cosine"], ascending=[True, False])
    nearest = nearest.groupby("Year", as_index=False).head(1)
    nearest_coords = coords_df.merge(
        nearest.rename(columns={"Peer": "Ticker"}),
        on=["Ticker", "Year"],
        how="inner",
    )

    fig, ax = plt.subplots(figsize=(10.5, 7.8), dpi=180)
    ax.scatter(coords_df["PC1"], coords_df["PC2"], s=18, color="#b8b8b8", alpha=0.28, label="Other firm-year vectors")
    ax.plot(lvs_coords["PC1"], lvs_coords["PC2"], color="#b55239", linewidth=2.0, marker="o", label="LVS vector path")
    label_offsets = {
        2008: (-18, 7),
        2013: (-20, -10),
        2014: (5, 9),
        2018: (5, -13),
        2019: (-10, -16),
        2022: (6, 8),
        2024: (7, -12),
    }
    for row in lvs_coords.itertuples(index=False):
        year = int(row.Year)
        if year in label_offsets:
            ax.annotate(
                str(year),
                (row.PC1, row.PC2),
                xytext=label_offsets[year],
                textcoords="offset points",
                fontsize=8,
                color="#6a2f24",
            )
    ax.scatter(nearest_coords["PC1"], nearest_coords["PC2"], s=70, marker="s", color="#214f80", alpha=0.9, label="Nearest semantic peer")
    for row in nearest_coords.itertuples(index=False):
        lvs = lvs_coords[lvs_coords["Year"] == row.Year]
        if not lvs.empty:
            ax.plot([float(lvs.iloc[0]["PC1"]), row.PC1], [float(lvs.iloc[0]["PC2"]), row.PC2], color="#214f80", alpha=0.45, linewidth=1.0)
        ax.annotate(f"{row.Ticker} {int(row.Year)}", (row.PC1, row.PC2), xytext=(5, -9), textcoords="offset points", fontsize=7, color="#214f80")

    ax.set_title("LVS risk-vector path and nearest semantic peers")
    ax.set_xlabel("PCA component 1 of Meso exposure vector")
    ax.set_ylabel("PCA component 2 of Meso exposure vector")
    focus = pd.concat(
        [
            coords_df[["PC1", "PC2"]],
            lvs_coords[["PC1", "PC2"]],
            nearest_coords[["PC1", "PC2"]],
        ],
        ignore_index=True,
    )
    x_low, x_high = focus["PC1"].quantile([0.01, 0.985])
    y_low, y_high = focus["PC2"].quantile([0.01, 0.985])
    ax.set_xlim(float(x_low) - 0.015, float(x_high) + 0.015)
    ax.set_ylim(float(y_low) - 0.015, float(y_high) + 0.015)
    ax.grid(linestyle="--", alpha=0.22)
    ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    fig.savefig(REPORT_FIGURES / "taxonomy_lvs_vector_network.png", bbox_inches="tight")
    plt.close(fig)


def plot_case_studies(variant: VariantArtifact) -> None:
    plot_lvs_dynamic_case_study(variant)
    plot_lvs_vector_network(variant)


def write_variant_summary(logs: pd.DataFrame, coverage: pd.DataFrame) -> None:
    if logs.empty:
        return
    summary_rows = []
    for variant_name, group in logs.groupby("Variant_Name", sort=False):
        final = group.sort_values("Year").iloc[-1]
        after_base = group[group["Year"] > 2006]
        cov = coverage[coverage["Variant_Name"] == variant_name]
        top_share = float(cov["Share"].max()) if not cov.empty else np.nan
        top_macro = str(cov.iloc[0]["Macro_Category"]) if not cov.empty else ""
        summary_rows.append(
            {
                "Variant": final["Variant"],
                "Variant_Name": variant_name,
                "Final_Meso_Categories": final["Final_Meso_Categories"],
                "Total_Risk_Factors": int(group["Total_Risk_Factors"].sum()),
                "Mean_Deviation_Percent_Post_Base": float(after_base["Deviation_Percent"].mean()),
                "ADD_Total": int(group["ADD"].sum()),
                "MERGE_Total": int(group["MERGE"].sum()),
                "REORGANIZE_Total": int(group["REORGANIZE"].sum()),
                "Top_2024_Macro_Category": top_macro,
                "Top_2024_Macro_Share": top_share,
            }
        )
    pd.DataFrame(summary_rows).to_csv(SENSITIVITY_OUT / "taxonomy_variant_summary.csv", index=False)


def main() -> int:
    REPORT_FIGURES.mkdir(parents=True, exist_ok=True)
    SENSITIVITY_OUT.mkdir(parents=True, exist_ok=True)

    variants = discover_variants()
    logs = pd.concat([load_taxonomy_logs(variant) for variant in variants], ignore_index=True)
    coverage = pd.concat([load_assignment_coverage(variant) for variant in variants], ignore_index=True)
    downstream = downstream_rows(variants)

    logs.to_csv(SENSITIVITY_OUT / "taxonomy_evolution_summary_default_theta040.csv", index=False)
    write_variant_summary(logs, coverage)
    plot_taxonomy_evolution(logs)
    plot_convergence(variants)
    plot_downstream_dashboard(downstream)
    plot_macro_coverage(coverage)

    best_variant = best_variant_for_topology(variants)
    plot_taxonomy_topology(best_variant)
    plot_case_studies(best_variant)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
