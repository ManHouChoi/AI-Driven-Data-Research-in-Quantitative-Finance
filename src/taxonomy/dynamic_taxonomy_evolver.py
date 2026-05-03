#!/usr/bin/env python3
"""Evolve an existing dynamic taxonomy with a new annual risk-factor CSV."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

import hdbscan
import numpy as np
import pandas as pd
import umap
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import taxonomy_prompts as prompts
from llm_service import LLMService


os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
np.random.seed(42)

DEFAULT_DEVIATION_THRESHOLD = 0.45
DEFAULT_MIN_CLUSTER_SIZE_MESO = 15
DEFAULT_DEVIATION_UMAP_NEIGHBORS = 5
DEFAULT_DEVIATION_UMAP_COMPONENTS = 5
DEFAULT_DEVIATION_UMAP_MIN_DIST = 0.1
DEFAULT_DEVIATION_MIN_SAMPLES = 1
DEFAULT_ADD_CENTROID_LLM_WEIGHT = 0.3
DEFAULT_MERGE_OLD_CENTROID_WEIGHT = 0.8
DEFAULT_LABEL_SAMPLE_SIZE = 5
DEFAULT_RANDOM_SEED = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", required=True, type=Path)
    parser.add_argument("--taxonomy", "-t", required=True, type=Path)
    parser.add_argument("--output", "-o", required=True, type=Path)
    parser.add_argument("--threshold", "-th", type=float, default=DEFAULT_DEVIATION_THRESHOLD)
    parser.add_argument("--min-cluster-size", type=int, default=DEFAULT_MIN_CLUSTER_SIZE_MESO)
    parser.add_argument("--umap-neighbors", type=int, default=DEFAULT_DEVIATION_UMAP_NEIGHBORS)
    parser.add_argument("--umap-components", type=int, default=DEFAULT_DEVIATION_UMAP_COMPONENTS)
    parser.add_argument("--umap-min-dist", type=float, default=DEFAULT_DEVIATION_UMAP_MIN_DIST)
    parser.add_argument("--min-samples", type=int, default=DEFAULT_DEVIATION_MIN_SAMPLES)
    parser.add_argument("--add-centroid-llm-weight", type=float, default=DEFAULT_ADD_CENTROID_LLM_WEIGHT)
    parser.add_argument("--merge-old-centroid-weight", type=float, default=DEFAULT_MERGE_OLD_CENTROID_WEIGHT)
    parser.add_argument("--label-sample-size", type=int, default=DEFAULT_LABEL_SAMPLE_SIZE)
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED)
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    positive_ints = {
        "min_cluster_size": args.min_cluster_size,
        "umap_neighbors": args.umap_neighbors,
        "umap_components": args.umap_components,
        "min_samples": args.min_samples,
        "label_sample_size": args.label_sample_size,
    }
    invalid = [name for name, value in positive_ints.items() if value < 1]
    if invalid:
        raise ValueError(f"Expected positive integer hyperparameter(s): {invalid}")
    if not 0.0 <= args.threshold <= 1.0:
        raise ValueError("--threshold must be in [0, 1].")
    if not 0.0 <= args.umap_min_dist <= 1.0:
        raise ValueError("--umap-min-dist must be in [0, 1].")
    if not 0.0 <= args.add_centroid_llm_weight <= 1.0:
        raise ValueError("--add-centroid-llm-weight must be in [0, 1].")
    if not 0.0 <= args.merge_old_centroid_weight <= 1.0:
        raise ValueError("--merge-old-centroid-weight must be in [0, 1].")


def parse_evolution_output(response: str, existing_names: set[str]) -> dict[str, str]:
    decision = re.search(r"Decision:\s*([A-E])", response)
    name = re.search(r"Recommended_Name:\s*(.+)", response)
    parent = re.search(r"Parent_Macro:\s*(.+)", response)
    reasoning = re.search(r"Reasoning:\s*(.+)", response, re.DOTALL)

    dec = decision.group(1) if decision else "A"
    rec_name = name.group(1).strip() if name else "New Theme"
    rec_parent = parent.group(1).strip() if parent else "General Business Risk"
    rec_reasoning = reasoning.group(1).strip() if reasoning else "No reasoning provided."
    if dec == "C" and rec_name not in existing_names:
        dec = "A"
        rec_reasoning = f"Fallback from REORGANIZE because target '{rec_name}' does not exist. {rec_reasoning}"
    return {"decision": dec, "name": rec_name, "parent": rec_parent, "reasoning": rec_reasoning}


def prepare_context(df: pd.DataFrame, fallback_company: str) -> pd.DataFrame:
    df = df[df["Raw Text"].astype(str).str.len() < 5000].reset_index(drop=True)
    for col in ["Headings", "Subheadings", "Raw Text"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    if "Company" not in df.columns:
        df["Company"] = fallback_company
    df["Company"] = df["Company"].fillna(fallback_company).astype(str)
    df["full_context"] = (
        "Heading: " + df["Headings"] + " | "
        + "Subheading: " + df["Subheadings"] + " | "
        + "Description: " + df["Raw Text"]
    ).astype(str)
    return df


def bounded_umap_neighbors(requested: int, n_samples: int) -> int:
    return max(2, min(requested, max(2, n_samples - 1)))


def bounded_umap_components(requested: int, n_samples: int) -> int:
    return max(2, min(requested, max(2, n_samples - 2)))


def meso_parent_lookup(taxonomy: dict) -> dict[str, str]:
    return {
        str(meso.get("name", "")).strip(): str(meso.get("parent_macro", "Unmapped Macro Risk")).strip()
        for meso in taxonomy.get("meso_categories", [])
        if str(meso.get("name", "")).strip()
    }


def add_category(
    taxonomy: dict,
    df_new: pd.DataFrame,
    target_indices,
    dev_embeddings,
    d_idx,
    name,
    parent,
    embed_model,
    llm_weight: float,
):
    math_centroid = np.mean(dev_embeddings[d_idx], axis=0)
    semantic_centroid = embed_model.encode([name])[0]
    centroid = ((1.0 - llm_weight) * math_centroid) + (llm_weight * semantic_centroid)
    taxonomy["meso_categories"].append({
        "id": f"NEW_{int(time.time())}_{np.random.randint(100, 999)}",
        "parent_macro": parent,
        "name": name,
        "definition": "Detected during dynamic evolution.",
        "centroid": centroid.tolist(),
    })
    df_new.loc[target_indices, "meso_category"] = name
    df_new.loc[target_indices, "macro_category"] = parent


def main() -> int:
    args = parse_args()
    validate_args(args)
    np.random.seed(args.random_seed)
    args.output.mkdir(parents=True, exist_ok=True)

    taxonomy = json.loads(args.taxonomy.read_text(encoding="utf-8"))
    if not taxonomy.get("meso_categories"):
        raise ValueError(f"Taxonomy has no meso_categories: {args.taxonomy}")

    df_new = prepare_context(pd.read_csv(args.input), fallback_company=args.input.stem)
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    new_embeddings = embed_model.encode(df_new["full_context"].tolist(), show_progress_bar=True)

    meso_centroids = np.array([m["centroid"] for m in taxonomy["meso_categories"]], dtype=float)
    meso_names = [m["name"] for m in taxonomy["meso_categories"]]
    meso_parents = [m.get("parent_macro", "Unmapped Macro Risk") for m in taxonomy["meso_categories"]]
    sim_matrix = cosine_similarity(new_embeddings, meso_centroids)
    max_sims = np.max(sim_matrix, axis=1)
    best_match_indices = np.argmax(sim_matrix, axis=1)
    df_new["meso_category"] = [meso_names[i] for i in best_match_indices]
    df_new["macro_category"] = [meso_parents[i] for i in best_match_indices]
    df_new["sim_score"] = max_sims
    df_new["is_deviation"] = max_sims < args.threshold

    deviations = df_new[df_new["is_deviation"]]
    dev_embeddings = np.atleast_2d(new_embeddings[df_new["is_deviation"].to_numpy()])
    changes_log = []

    if len(deviations) >= args.min_cluster_size:
        dev_umap = umap.UMAP(
            n_neighbors=bounded_umap_neighbors(args.umap_neighbors, len(dev_embeddings)),
            min_dist=args.umap_min_dist,
            n_components=bounded_umap_components(args.umap_components, len(dev_embeddings)),
            random_state=args.random_seed,
            low_memory=True,
            n_jobs=1,
        ).fit_transform(dev_embeddings)
        dev_labels = hdbscan.HDBSCAN(
            min_cluster_size=args.min_cluster_size,
            min_samples=args.min_samples,
        ).fit_predict(dev_umap)
        llm = LLMService()

        for dev_id in [x for x in sorted(set(dev_labels)) if x != -1]:
            d_idx = np.where(dev_labels == dev_id)[0]
            target_indices = deviations.index.to_numpy()[d_idx]
            cluster_avg = np.mean(dev_embeddings[d_idx], axis=0).reshape(1, -1)
            cluster_sims = cosine_similarity(cluster_avg, meso_centroids)[0]
            top_3_idx = np.argsort(cluster_sims)[-3:][::-1]
            closest_info = [f"{meso_names[i]} (Sim: {cluster_sims[i]:.2f})" for i in top_3_idx]
            sample_texts = deviations.iloc[d_idx]["full_context"].sample(
                min(args.label_sample_size, len(d_idx)),
                random_state=args.random_seed + int(dev_id),
            ).tolist()
            taxonomy_summary = [f"{m['name']} (parent: {m['parent_macro']})" for m in taxonomy["meso_categories"]]

            response = llm.call_llm(
                prompts.SYSTEM_MSG,
                prompts.get_evolution_prompt(sample_texts, closest_info, taxonomy_summary),
            )
            decision = parse_evolution_output(response, existing_names=set(meso_names))

            if decision["decision"] == "A":
                add_category(
                    taxonomy,
                    df_new,
                    target_indices,
                    dev_embeddings,
                    d_idx,
                    decision["name"],
                    decision["parent"],
                    embed_model,
                    args.add_centroid_llm_weight,
                )
                changes_log.append({
                    "Action": "ADD",
                    "Category": decision["name"],
                    "Details": f"New category under macro: {decision['parent']}",
                    "Reasoning": decision["reasoning"],
                })
            elif decision["decision"] == "B":
                target_name = meso_names[top_3_idx[0]]
                for meso in taxonomy["meso_categories"]:
                    if meso["name"] == target_name:
                        old_centroid = np.array(meso["centroid"])
                        new_math = np.mean(dev_embeddings[d_idx], axis=0)
                        old_weight = float(args.merge_old_centroid_weight)
                        meso["centroid"] = ((old_weight * old_centroid) + ((1.0 - old_weight) * new_math)).tolist()
                        break
                df_new.loc[target_indices, "meso_category"] = target_name
                df_new.loc[target_indices, "macro_category"] = meso_parent_lookup(taxonomy).get(
                    target_name,
                    "Unmapped Macro Risk",
                )
                changes_log.append({
                    "Action": "MERGE",
                    "Category": target_name,
                    "Details": "Absorbed deviation cluster into existing category.",
                    "Reasoning": decision["reasoning"],
                })
            elif decision["decision"] == "C":
                found = False
                for meso in taxonomy["meso_categories"]:
                    if meso["name"] == decision["name"]:
                        old_parent = meso.get("parent_macro", "Unknown")
                        meso["parent_macro"] = decision["parent"]
                        found = True
                        break
                if found:
                    df_new.loc[target_indices, "meso_category"] = decision["name"]
                    df_new.loc[target_indices, "macro_category"] = decision["parent"]
                    changes_log.append({
                        "Action": "REORGANIZE",
                        "Category": decision["name"],
                        "Details": f"Moved from macro '{old_parent}' to '{decision['parent']}'",
                        "Reasoning": decision["reasoning"],
                    })

    parent_map = meso_parent_lookup(taxonomy)
    df_new["macro_category"] = df_new["meso_category"].map(parent_map).fillna("Unmapped Macro Risk")

    firm_totals = df_new.groupby("Company").size()
    vector_pivot = df_new.groupby(["Company", "meso_category"]).size().unstack(fill_value=0)
    all_current_categories = [m["name"] for m in taxonomy["meso_categories"]]
    vector_pivot = vector_pivot.reindex(columns=all_current_categories, fill_value=0)
    exposure_vectors = vector_pivot.div(firm_totals, axis=0)

    (args.output / "taxonomy_evolved.json").write_text(json.dumps(taxonomy, indent=4), encoding="utf-8")
    df_new.to_csv(args.output / "classified_risk_factors.csv", index=False)
    exposure_vectors.to_csv(args.output / "risk_vectors.csv")

    if changes_log:
        pd.DataFrame(changes_log).to_csv(args.output / "evolution_summary.csv", index=False)
        reasoning = [{"action": c["Action"], "category": c["Category"], "reasoning": c["Reasoning"]} for c in changes_log]
        (args.output / "llm_reasoning_log.json").write_text(json.dumps(reasoning, indent=4), encoding="utf-8")

    log_data = {
        "input_file": str(args.input),
        "base_taxonomy": str(args.taxonomy),
        "output_dir": str(args.output),
        "deviation_threshold": args.threshold,
        "total_new_factors": len(df_new),
        "deviation_count": int(len(deviations)),
        "deviation_percent": round(len(deviations) / len(df_new) * 100, 2) if len(df_new) else 0.0,
        "actions_taken": changes_log,
        "final_meso_categories": len(taxonomy["meso_categories"]),
        "hyperparameters": {
            "DEVIATION_THRESHOLD": args.threshold,
            "MIN_CLUSTER_SIZE_MESO": args.min_cluster_size,
            "DEVIATION_UMAP_NEIGHBORS": args.umap_neighbors,
            "DEVIATION_UMAP_COMPONENTS": args.umap_components,
            "DEVIATION_UMAP_MIN_DIST": args.umap_min_dist,
            "DEVIATION_MIN_SAMPLES": args.min_samples,
            "ADD_CENTROID_LLM_WEIGHT": args.add_centroid_llm_weight,
            "MERGE_OLD_CENTROID_WEIGHT": args.merge_old_centroid_weight,
            "LABEL_SAMPLE_SIZE": args.label_sample_size,
            "RANDOM_SEED": args.random_seed,
        },
    }
    (args.output / "run_log.json").write_text(json.dumps(log_data, indent=4), encoding="utf-8")
    print(f"Dynamic taxonomy evolution complete: {log_data}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
