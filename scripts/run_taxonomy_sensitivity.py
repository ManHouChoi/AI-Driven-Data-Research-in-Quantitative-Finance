#!/usr/bin/env python3
"""Run full-window taxonomy sensitivity variants and optional downstream tests.

The script is intentionally orchestration-only: it makes the long 2006-2024
variant workflow reproducible without hiding the runtime cost. Use --dry-run to
inspect commands before launching LLM and embedding jobs.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Variant:
    name: str
    macro_min_size: int = 50
    meso_min_size: int = 15
    umap_neighbors: int = 15
    deviation_threshold: float = 0.45
    macro_min_samples: int = 5
    meso_min_samples: int = 3
    macro_umap_components: int = 5
    meso_umap_neighbors: int = 8
    meso_umap_components: int = 8
    macro_umap_min_dist: float = 0.1
    meso_umap_min_dist: float = 0.2
    centroid_llm_weight: float = 0.3
    evolution_umap_neighbors: int = 5
    evolution_umap_components: int = 5
    evolution_umap_min_dist: float = 0.1
    evolution_min_samples: int = 1
    add_centroid_llm_weight: float = 0.3
    merge_old_centroid_weight: float = 0.8
    label_sample_size: int = 5
    random_seed: int = 42


VARIANTS = [
    Variant("default"),
    Variant("macro20", macro_min_size=20),
    Variant("macro30", macro_min_size=30),
    Variant("macro40", macro_min_size=40),
    Variant("macro70", macro_min_size=70),
    Variant("macro90", macro_min_size=90),
    Variant("meso8", meso_min_size=8),
    Variant("meso10", meso_min_size=10),
    Variant("meso20", meso_min_size=20),
    Variant("meso25", meso_min_size=25),
    Variant("umap8", umap_neighbors=8),
    Variant("umap10", umap_neighbors=10),
    Variant("umap20", umap_neighbors=20),
    Variant("umap30", umap_neighbors=30),
    Variant("theta035", deviation_threshold=0.35),
    Variant("theta040", deviation_threshold=0.40),
    Variant("theta050", deviation_threshold=0.50),
    Variant("theta055", deviation_threshold=0.55),
    Variant("macro_samples3", macro_min_samples=3),
    Variant("macro_samples8", macro_min_samples=8),
    Variant("meso_samples1", meso_min_samples=1),
    Variant("meso_samples5", meso_min_samples=5),
    Variant("meso_umap5", meso_umap_neighbors=5),
    Variant("meso_umap12", meso_umap_neighbors=12),
    Variant("components3", macro_umap_components=3, meso_umap_components=3, evolution_umap_components=3),
    Variant("components10", macro_umap_components=10, meso_umap_components=10, evolution_umap_components=10),
    Variant("centroid20", centroid_llm_weight=0.20, add_centroid_llm_weight=0.20),
    Variant("centroid40", centroid_llm_weight=0.40, add_centroid_llm_weight=0.40),
    Variant("evol_umap3", evolution_umap_neighbors=3),
    Variant("evol_umap8", evolution_umap_neighbors=8),
    Variant("merge075", merge_old_centroid_weight=0.75),
    Variant("merge090", merge_old_centroid_weight=0.90),
    Variant("seed43", random_seed=43),
]


def parse_csv_list(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def command_output_marker(cmd: list[str], env: dict[str, str] | None = None) -> Path | None:
    script_name = Path(cmd[1]).name if len(cmd) > 1 else ""
    if script_name == "dynamic_base_year_taxonomy.py":
        output_dir = Path(cmd[cmd.index("--output") + 1])
        return output_dir / "taxonomy_base.json"
    if script_name == "dynamic_taxonomy_evolver.py":
        output_dir = Path(cmd[cmd.index("--output") + 1])
        return output_dir / "taxonomy_evolved.json"
    if script_name == "build_taxonomy_variant_matrix.py":
        if "--output-meso" in cmd:
            return Path(cmd[cmd.index("--output-meso") + 1])
        if "--output" in cmd:
            return Path(cmd[cmd.index("--output") + 1])
    if script_name == "GAT_forecast_macro.py" and env is not None:
        return Path(env["FYP_GAT_MACRO_OUTPUT_DIR"]) / "goodness_of_fit_metrics_macro_OOS.csv"
    if script_name == "GAT_forecast_meso.py" and env is not None:
        return Path(env["FYP_GAT_MESO_OUTPUT_DIR"]) / "goodness_of_fit_metrics_meso_OOS.csv"
    if script_name == "portfolio_backtest.py" and env is not None:
        return Path(env["FYP_PORTFOLIO_OUTPUT_DIR"]) / "portfolio_performance_summary_ranked.csv"
    return None


def run_command(cmd: list[str], dry_run: bool, env: dict[str, str] | None = None, reuse_existing: bool = False) -> None:
    marker = command_output_marker(cmd, env=env)
    if reuse_existing and marker is not None and marker.exists():
        print(f"# skip existing: {marker}")
        return
    print(" ".join(str(part) for part in cmd))
    if not dry_run:
        subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def choose_variants(names: list[str]) -> list[Variant]:
    if not names:
        return VARIANTS
    by_name = {variant.name: variant for variant in VARIANTS}
    unknown = sorted(set(names).difference(by_name))
    if unknown:
        raise ValueError(f"Unknown variant(s): {unknown}. Available: {sorted(by_name)}")
    return [by_name[name] for name in names]


def taxonomy_commands(args: argparse.Namespace, variant: Variant) -> list[list[str]]:
    variant_root = args.output_root / variant.name
    commands: list[list[str]] = []

    base_input = args.input_dir / f"risk_factor_{args.base_year}.csv"
    base_output = variant_root / f"output_risk_factor_{args.base_year}"
    commands.append([
        args.python,
        str(args.builder_script),
        "--input",
        str(base_input),
        "--macro-min-size",
        str(variant.macro_min_size),
        "--meso-min-size",
        str(variant.meso_min_size),
        "--umap-neighbors",
        str(variant.umap_neighbors),
        "--macro-min-samples",
        str(variant.macro_min_samples),
        "--meso-min-samples",
        str(variant.meso_min_samples),
        "--macro-umap-components",
        str(variant.macro_umap_components),
        "--meso-umap-neighbors",
        str(variant.meso_umap_neighbors),
        "--meso-umap-components",
        str(variant.meso_umap_components),
        "--macro-umap-min-dist",
        str(variant.macro_umap_min_dist),
        "--meso-umap-min-dist",
        str(variant.meso_umap_min_dist),
        "--centroid-llm-weight",
        str(variant.centroid_llm_weight),
        "--label-sample-size",
        str(variant.label_sample_size),
        "--random-seed",
        str(variant.random_seed),
        "--output",
        str(base_output),
    ])

    for year in range(args.base_year + 1, args.end_year + 1):
        prev_dir = variant_root / f"output_risk_factor_{year - 1}"
        prev_taxonomy = prev_dir / "taxonomy_evolved.json"
        if year - 1 == args.base_year:
            prev_taxonomy = prev_dir / "taxonomy_base.json"

        commands.append([
            args.python,
            str(args.evolver_script),
            "--input",
            str(args.input_dir / f"risk_factor_{year}.csv"),
            "--taxonomy",
            str(prev_taxonomy),
            "--output",
            str(variant_root / f"output_risk_factor_{year}"),
            "--threshold",
            str(variant.deviation_threshold),
            "--min-cluster-size",
            str(variant.meso_min_size),
            "--umap-neighbors",
            str(variant.evolution_umap_neighbors),
            "--umap-components",
            str(variant.evolution_umap_components),
            "--umap-min-dist",
            str(variant.evolution_umap_min_dist),
            "--min-samples",
            str(variant.evolution_min_samples),
            "--add-centroid-llm-weight",
            str(variant.add_centroid_llm_weight),
            "--merge-old-centroid-weight",
            str(variant.merge_old_centroid_weight),
            "--label-sample-size",
            str(variant.label_sample_size),
            "--random-seed",
            str(variant.random_seed),
        ])

    return commands


def forecast_output_dir(args: argparse.Namespace, variant: Variant, level: str) -> Path:
    paired = args.gat_output_root / f"{variant.name}_{level}"
    if level == "meso" and args.reuse_existing:
        legacy = args.gat_output_root / variant.name
        legacy_marker = legacy / "goodness_of_fit_metrics_meso_OOS.csv"
        if legacy_marker.exists():
            return legacy
    return paired


def downstream_commands(args: argparse.Namespace, variant: Variant) -> list[tuple[list[str], dict[str, str] | None]]:
    variant_root = args.output_root / variant.name
    meso_matrix_path = variant_root / "risk_scores_meso_annual.csv"
    macro_matrix_path = variant_root / "risk_scores_macro_annual.csv"
    commands: list[tuple[list[str], dict[str, str] | None]] = [
        ([
            args.python,
            str(ROOT / "scripts" / "build_taxonomy_variant_matrix.py"),
            "--variant-root",
            str(variant_root),
            "--output-meso",
            str(meso_matrix_path),
            "--output-macro",
            str(macro_matrix_path),
            "--base-year",
            str(args.base_year),
            "--end-year",
            str(args.end_year),
        ], None)
    ]

    if args.downstream in {"forecast", "portfolio", "all"}:
        levels = parse_csv_list(args.levels)
        for level, matrix_path, forecast_script, output_env, csv_env in [
            (
                "macro",
                macro_matrix_path,
                ROOT / "src" / "gat" / "GAT_forecast_macro.py",
                "FYP_GAT_MACRO_OUTPUT_DIR",
                "FYP_RISK_SCORES_MACRO_CSV",
            ),
            (
                "meso",
                meso_matrix_path,
                ROOT / "src" / "gat" / "GAT_forecast_meso.py",
                "FYP_GAT_MESO_OUTPUT_DIR",
                "FYP_RISK_SCORES_MESO_CSV",
            ),
        ]:
            if level not in levels:
                continue
            gat_output = forecast_output_dir(args, variant, level)
            env = os.environ.copy()
            env["FYP_PROJECT_ROOT"] = str(ROOT)
            env[csv_env] = str(matrix_path)
            env[output_env] = str(gat_output)
            commands.append(([args.python, str(forecast_script)], env))

    if args.downstream in {"portfolio", "all"}:
        if "meso" not in parse_csv_list(args.levels):
            raise ValueError("--downstream portfolio/all requires --levels to include meso.")
        port_output = args.portfolio_output_root / variant.name
        env = os.environ.copy()
        env["FYP_PROJECT_ROOT"] = str(ROOT)
        env["FYP_GAT_MESO_PANEL_CSV"] = str(
            forecast_output_dir(args, variant, "meso") / "ST_GAT_vs_Baseline_Panel_meso.csv"
        )
        env["FYP_PORTFOLIO_OUTPUT_DIR"] = str(port_output)
        commands.append(([args.python, str(ROOT / "src" / "portfolio" / "portfolio_backtest.py")], env))

    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data" / "interim" / "taxonomy_sensitivity" / "input")
    parser.add_argument("--output-root", type=Path, default=ROOT / "outputs" / "taxonomy" / "sensitivity")
    parser.add_argument("--gat-output-root", type=Path, default=ROOT / "outputs" / "gat" / "taxonomy_sensitivity")
    parser.add_argument("--portfolio-output-root", type=Path, default=ROOT / "outputs" / "portfolio" / "taxonomy_sensitivity")
    parser.add_argument("--builder-script", type=Path, default=ROOT / "src" / "taxonomy" / "dynamic_base_year_taxonomy.py")
    parser.add_argument("--evolver-script", type=Path, default=ROOT / "src" / "taxonomy" / "dynamic_taxonomy_evolver.py")
    parser.add_argument("--base-year", type=int, default=2006)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--variant", action="append", default=[], help="Variant name. Repeat to run a subset.")
    parser.add_argument("--downstream", choices=["none", "matrix", "forecast", "portfolio", "all"], default="none")
    parser.add_argument("--levels", default="macro,meso", help="Forecast levels for downstream runs: macro, meso, or macro,meso.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reuse-existing", action="store_true", help="Skip taxonomy/matrix commands when their output marker already exists.")
    args = parser.parse_args()

    levels = parse_csv_list(args.levels)
    unknown_levels = sorted(set(levels).difference({"macro", "meso"}))
    if unknown_levels:
        raise ValueError(f"Unknown level(s): {unknown_levels}. Expected macro, meso, or macro,meso.")
    if args.downstream in {"forecast", "portfolio", "all"} and not levels:
        raise ValueError("--levels must include at least one forecast level for downstream forecast/portfolio runs.")

    variants = choose_variants(args.variant)
    for variant in variants:
        print(f"\n# Variant: {variant.name}")
        for cmd in taxonomy_commands(args, variant):
            run_command(cmd, dry_run=args.dry_run, reuse_existing=args.reuse_existing)
        if args.downstream != "none":
            for cmd, env in downstream_commands(args, variant):
                run_command(cmd, dry_run=args.dry_run, env=env, reuse_existing=args.reuse_existing)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
