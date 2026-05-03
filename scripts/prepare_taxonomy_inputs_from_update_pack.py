#!/usr/bin/env python3
"""Reconstruct annual taxonomy input CSVs from the May 2 update-pack outputs.

The update pack stores the real paragraph text inside annual classified output
files. This helper extracts only the raw input columns needed by the dynamic
taxonomy builder/evolver so sensitivity runs can be launched from real text
without committing the large update pack or generated CSVs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


INPUT_COLUMNS = ["Company", "Headings", "Subheadings", "Raw Text"]


def source_file(update_pack_taxonomy_dir: Path, year: int, base_year: int) -> Path:
    year_dir = update_pack_taxonomy_dir / f"output_risk_factor_{year}"
    if year == base_year:
        return year_dir / "hierarchical_risk_categories.csv"
    return year_dir / "classified_risk_factors.csv"


def prepare_year(update_pack_taxonomy_dir: Path, output_dir: Path, year: int, base_year: int) -> tuple[Path, int]:
    src = source_file(update_pack_taxonomy_dir, year, base_year)
    if not src.exists():
        raise FileNotFoundError(f"Missing update-pack source for {year}: {src}")

    df = pd.read_csv(src, usecols=lambda c: c in INPUT_COLUMNS)
    missing = [col for col in INPUT_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"{src} is missing required input column(s): {missing}")

    df = df[INPUT_COLUMNS].copy()
    for col in INPUT_COLUMNS:
        df[col] = df[col].fillna("").astype(str)

    # The dynamic taxonomy scripts filter very long paragraphs themselves; this
    # file intentionally preserves the real update-pack text before that filter.
    out = output_dir / f"risk_factor_{year}.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out, len(df)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-pack-taxonomy-dir",
        type=Path,
        default=Path("May 2 update") / "taxonomy",
        help="Directory containing output_risk_factor_YYYY folders.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data") / "interim" / "taxonomy_sensitivity" / "input",
    )
    parser.add_argument("--base-year", type=int, default=2006)
    parser.add_argument("--end-year", type=int, default=2024)
    args = parser.parse_args()

    total_rows = 0
    for year in range(args.base_year, args.end_year + 1):
        out, rows = prepare_year(args.update_pack_taxonomy_dir, args.output_dir, year, args.base_year)
        total_rows += rows
        print(f"{year}: wrote {rows:,} rows to {out}")

    print(f"Prepared {total_rows:,} real paragraph rows for {args.base_year}-{args.end_year}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
