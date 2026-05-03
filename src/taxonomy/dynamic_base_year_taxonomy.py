#!/usr/bin/env python3
"""Build the 2006 dynamic macro-meso taxonomy using UMAP, HDBSCAN, and LLM labels."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import hdbscan
import numpy as np
import pandas as pd
import umap
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import taxonomy_prompts as prompts
from llm_service import LLMService


os.environ["TOKENIZERS_PARALLELISM"] = "false"
np.random.seed(42)

DEFAULT_N_NEIGHBORS = 15
DEFAULT_MIN_CLUSTER_SIZE_MACRO = 50
DEFAULT_MIN_CLUSTER_SIZE_MESO = 15
DEFAULT_MACRO_MIN_SAMPLES = 5
DEFAULT_MESO_MIN_SAMPLES = 3
DEFAULT_MACRO_UMAP_COMPONENTS = 5
DEFAULT_MESO_UMAP_NEIGHBORS = 8
DEFAULT_MESO_UMAP_COMPONENTS = 8
DEFAULT_MACRO_UMAP_MIN_DIST = 0.1
DEFAULT_MESO_UMAP_MIN_DIST = 0.2
DEFAULT_CENTROID_LLM_WEIGHT = 0.3
DEFAULT_LABEL_SAMPLE_SIZE = 5
DEFAULT_RANDOM_SEED = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", required=True, type=Path)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--macro-min-size", type=int, default=DEFAULT_MIN_CLUSTER_SIZE_MACRO)
    parser.add_argument("--meso-min-size", type=int, default=DEFAULT_MIN_CLUSTER_SIZE_MESO)
    parser.add_argument("--umap-neighbors", type=int, default=DEFAULT_N_NEIGHBORS)
    parser.add_argument("--macro-min-samples", type=int, default=DEFAULT_MACRO_MIN_SAMPLES)
    parser.add_argument("--meso-min-samples", type=int, default=DEFAULT_MESO_MIN_SAMPLES)
    parser.add_argument("--macro-umap-components", type=int, default=DEFAULT_MACRO_UMAP_COMPONENTS)
    parser.add_argument("--meso-umap-neighbors", type=int, default=DEFAULT_MESO_UMAP_NEIGHBORS)
    parser.add_argument("--meso-umap-components", type=int, default=DEFAULT_MESO_UMAP_COMPONENTS)
    parser.add_argument("--macro-umap-min-dist", type=float, default=DEFAULT_MACRO_UMAP_MIN_DIST)
    parser.add_argument("--meso-umap-min-dist", type=float, default=DEFAULT_MESO_UMAP_MIN_DIST)
    parser.add_argument("--centroid-llm-weight", type=float, default=DEFAULT_CENTROID_LLM_WEIGHT)
    parser.add_argument("--label-sample-size", type=int, default=DEFAULT_LABEL_SAMPLE_SIZE)
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED)
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    positive_ints = {
        "macro_min_size": args.macro_min_size,
        "meso_min_size": args.meso_min_size,
        "umap_neighbors": args.umap_neighbors,
        "macro_min_samples": args.macro_min_samples,
        "meso_min_samples": args.meso_min_samples,
        "macro_umap_components": args.macro_umap_components,
        "meso_umap_neighbors": args.meso_umap_neighbors,
        "meso_umap_components": args.meso_umap_components,
        "label_sample_size": args.label_sample_size,
    }
    invalid = [name for name, value in positive_ints.items() if value < 1]
    if invalid:
        raise ValueError(f"Expected positive integer hyperparameter(s): {invalid}")
    if not 0.0 <= args.macro_umap_min_dist <= 1.0:
        raise ValueError("--macro-umap-min-dist must be in [0, 1].")
    if not 0.0 <= args.meso_umap_min_dist <= 1.0:
        raise ValueError("--meso-umap-min-dist must be in [0, 1].")
    if not 0.0 <= args.centroid_llm_weight <= 1.0:
        raise ValueError("--centroid-llm-weight must be in [0, 1].")


def clean_taxonomy_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = re.sub(r"\*\*", "", text).strip(" -:–\n\t")
    text = re.sub(r"\s{2,}", " ", text).replace("..", ".").replace(",,", ",")
    return text[0].upper() + text[1:] if len(text) > 1 else text


def parse_llm_output(response: str) -> tuple[str, str, str]:
    name_match = re.search(r"(?:Name|Category\s*Name|Subcategory)\s*:\s*(.+)", response, re.IGNORECASE)
    def_match = re.search(r"(?:Definition|Description)\s*:\s*(.+)", response, re.IGNORECASE)
    sum_match = re.search(r"(?:Centroid_Summary|Summary)\s*:\s*(.+)", response, re.S | re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else "Unclassified"
    definition = def_match.group(1).strip() if def_match else "N/A"
    summary = sum_match.group(1).strip() if sum_match else name
    return clean_taxonomy_text(name), clean_taxonomy_text(definition), summary


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
    )
    return df


def bounded_umap_neighbors(requested: int, n_samples: int) -> int:
    return max(2, min(requested, max(2, n_samples - 1)))


def bounded_umap_components(requested: int, n_samples: int) -> int:
    return max(2, min(requested, max(2, n_samples - 2)))


def sample_texts(texts: list[str], sample_size: int, rng: np.random.Generator) -> list[str]:
    if len(texts) <= sample_size:
        return texts
    indices = rng.choice(len(texts), size=sample_size, replace=False)
    return [texts[int(i)] for i in indices]


def build_output_dir(args: argparse.Namespace) -> Path:
    if args.output:
        return args.output
    base_name = args.input.stem
    suffix = ""
    if args.macro_min_size != DEFAULT_MIN_CLUSTER_SIZE_MACRO:
        suffix = f"_macro{args.macro_min_size}"
    elif args.meso_min_size != DEFAULT_MIN_CLUSTER_SIZE_MESO:
        suffix = f"_meso{args.meso_min_size}"
    elif args.umap_neighbors != DEFAULT_N_NEIGHBORS:
        suffix = f"_umap{args.umap_neighbors}"
    return Path(f"output_{base_name}{suffix}")


def main() -> int:
    args = parse_args()
    validate_args(args)
    np.random.seed(args.random_seed)
    rng = np.random.default_rng(args.random_seed)
    output_dir = build_output_dir(args)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
    df = prepare_context(df, fallback_company=args.input.stem)
    print(f"Encoding {len(df):,} risk factors from {args.input}")

    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = embed_model.encode(df["full_context"].tolist(), show_progress_bar=True)

    umap_macro = umap.UMAP(
        n_neighbors=bounded_umap_neighbors(args.umap_neighbors, len(df)),
        min_dist=args.macro_umap_min_dist,
        n_components=bounded_umap_components(args.macro_umap_components, len(df)),
        random_state=args.random_seed,
    ).fit_transform(embeddings)
    macro_labels = hdbscan.HDBSCAN(
        min_cluster_size=args.macro_min_size,
        min_samples=args.macro_min_samples,
    ).fit_predict(umap_macro)
    df["macro_cluster_id"] = macro_labels
    df["macro_category"] = pd.NA
    df["meso_category"] = pd.NA

    taxonomy = {"macro_categories": [], "meso_categories": []}
    llm = LLMService()
    w_llm = float(args.centroid_llm_weight)
    w_data = 1.0 - w_llm

    for macro_id in [x for x in sorted(set(macro_labels)) if x != -1]:
        macro_idx = df.index[macro_labels == macro_id]
        macro_texts = df.loc[macro_idx, "full_context"].tolist()
        sampled = sample_texts(macro_texts, args.label_sample_size, rng)
        macro_response = llm.call_llm(prompts.SYSTEM_MSG, prompts.get_macro_prompt(sampled))
        macro_name, macro_def, macro_summary = parse_llm_output(macro_response)

        math_centroid = np.mean(embeddings[macro_idx], axis=0)
        semantic_centroid = embed_model.encode([macro_summary])[0]
        macro_centroid = (w_data * math_centroid) + (w_llm * semantic_centroid)
        taxonomy["macro_categories"].append({
            "id": int(macro_id),
            "name": macro_name,
            "definition": macro_def,
            "summary": macro_summary,
            "centroid": macro_centroid.tolist(),
        })
        df.loc[macro_idx, "macro_category"] = macro_name

        macro_positions = [df.index.get_loc(i) for i in macro_idx]
        macro_embeddings = embeddings[macro_positions]
        umap_meso = umap.UMAP(
            n_neighbors=bounded_umap_neighbors(args.meso_umap_neighbors, len(macro_embeddings)),
            min_dist=args.meso_umap_min_dist,
            n_components=bounded_umap_components(args.meso_umap_components, len(macro_embeddings)),
            random_state=args.random_seed,
        ).fit_transform(macro_embeddings)
        meso_labels = hdbscan.HDBSCAN(
            min_cluster_size=args.meso_min_size,
            min_samples=args.meso_min_samples,
        ).fit_predict(umap_meso)

        for meso_id in [x for x in sorted(set(meso_labels)) if x != -1]:
            sub_idx = macro_idx[meso_labels == meso_id]
            sub_texts = df.loc[sub_idx, "full_context"].tolist()
            sampled_sub = sample_texts(sub_texts, args.label_sample_size, rng)
            meso_response = llm.call_llm(prompts.SYSTEM_MSG, prompts.get_meso_prompt(sampled_sub, macro_name))
            meso_name, meso_def, meso_summary = parse_llm_output(meso_response)

            meso_math = np.mean(embeddings[sub_idx], axis=0)
            meso_semantic = embed_model.encode([meso_summary])[0]
            meso_centroid = (w_data * meso_math) + (w_llm * meso_semantic)
            df.loc[sub_idx, "meso_category"] = meso_name
            taxonomy["meso_categories"].append({
                "id": f"{macro_id}_{meso_id}",
                "parent_macro": macro_name,
                "name": meso_name,
                "definition": meso_def,
                "summary": meso_summary,
                "centroid": meso_centroid.tolist(),
            })

    if not taxonomy["meso_categories"]:
        raise ValueError(
            "No Meso categories were discovered. Adjust --macro-min-size, --meso-min-size, "
            "or UMAP/HDBSCAN sensitivity settings."
        )

    if taxonomy["meso_categories"]:
        meso_centroids = np.array([m["centroid"] for m in taxonomy["meso_categories"]])
        meso_names = [m["name"] for m in taxonomy["meso_categories"]]
        macro_parents = [m["parent_macro"] for m in taxonomy["meso_categories"]]
        noise_mask = df["meso_category"].isna()
        if noise_mask.any():
            sims = cosine_similarity(embeddings[noise_mask], meso_centroids)
            best = np.argmax(sims, axis=1)
            df.loc[noise_mask, "meso_category"] = [meso_names[i] for i in best]
            df.loc[noise_mask, "macro_category"] = [macro_parents[i] for i in best]

    total = len(df)
    macro_noise = int((macro_labels == -1).sum())
    log_data = {
        "input_file": str(args.input),
        "output_dir": str(output_dir),
        "total_risk_factors": total,
        "macro_clusters": len(taxonomy["macro_categories"]),
        "meso_clusters": len(taxonomy["meso_categories"]),
        "macro_noise_points": macro_noise,
        "macro_coverage_percent": round((total - macro_noise) / total * 100, 2) if total else 0.0,
        "meso_assigned_points": int(df["meso_category"].notna().sum()),
        "meso_coverage_percent": round(df["meso_category"].notna().sum() / total * 100, 2) if total else 0.0,
        "hyperparameters": {
            "N_NEIGHBORS": args.umap_neighbors,
            "MIN_CLUSTER_SIZE_MACRO": args.macro_min_size,
            "MIN_CLUSTER_SIZE_MESO": args.meso_min_size,
            "MACRO_MIN_SAMPLES": args.macro_min_samples,
            "MESO_MIN_SAMPLES": args.meso_min_samples,
            "MACRO_UMAP_COMPONENTS": args.macro_umap_components,
            "MESO_UMAP_NEIGHBORS": args.meso_umap_neighbors,
            "MESO_UMAP_COMPONENTS": args.meso_umap_components,
            "MACRO_UMAP_MIN_DIST": args.macro_umap_min_dist,
            "MESO_UMAP_MIN_DIST": args.meso_umap_min_dist,
            "CENTROID_LLM_WEIGHT": args.centroid_llm_weight,
            "LABEL_SAMPLE_SIZE": args.label_sample_size,
            "RANDOM_SEED": args.random_seed,
        },
    }

    df.to_csv(output_dir / "hierarchical_risk_categories.csv", index=False)
    (output_dir / "taxonomy_base.json").write_text(json.dumps(taxonomy, indent=4), encoding="utf-8")
    (output_dir / "run_log.json").write_text(json.dumps(log_data, indent=4), encoding="utf-8")

    if "meso_category" in df.columns:
        firm_totals = df.groupby("Company").size()
        vector_pivot = df.groupby(["Company", "meso_category"]).size().unstack(fill_value=0)
        exposure_vectors = vector_pivot.div(firm_totals, axis=0)
        exposure_vectors.to_csv(output_dir / "base_year_vectors.csv")

    print(f"Base taxonomy complete: {log_data}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
