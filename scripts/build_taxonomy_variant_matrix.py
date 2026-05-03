#!/usr/bin/env python3
"""Build model-ready Macro and Meso exposure matrices from taxonomy outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


def normalize_category_name(name: str) -> str:
    """Undo pandas duplicate-column suffixes so duplicate labels can be summed."""
    text = re.sub(r"\.\d+$", "", str(name))
    text = re.sub(r"\*\*", "", text)
    return re.sub(r"\s+", " ", text).strip()


def taxonomy_path(year_dir: Path, base_year: int, year: int) -> Path:
    filename = "taxonomy_base.json" if year == base_year else "taxonomy_evolved.json"
    return year_dir / filename


def vector_path(year_dir: Path, base_year: int, year: int) -> Path:
    filename = "base_year_vectors.csv" if year == base_year else "risk_vectors.csv"
    return year_dir / filename


def load_meso_parent_map(year_dir: Path, base_year: int, year: int) -> dict[str, str]:
    path = taxonomy_path(year_dir, base_year, year)
    if not path.exists():
        raise FileNotFoundError(f"Missing taxonomy file for {year}: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for meso in payload.get("meso_categories", []):
        name = normalize_category_name(meso.get("name", ""))
        parent = normalize_category_name(meso.get("parent_macro", "Unmapped Macro Risk"))
        if name:
            mapping.setdefault(name, parent or "Unmapped Macro Risk")
    if not mapping:
        raise ValueError(f"No meso category mapping found in {path}")
    return mapping


def read_year_vectors(path: Path, year: int) -> tuple[pd.DataFrame, list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing vector file for {year}: {path}")

    df = pd.read_csv(path)
    if "Company" not in df.columns:
        first = df.columns[0]
        df = df.rename(columns={first: "Company"})

    tickers = df["Company"].astype(str).str.upper().str.strip()
    raw_risk_columns = [c for c in df.columns if c != "Company"]
    risk_block = df.drop(columns=["Company"]).copy()
    rename_map = {c: normalize_category_name(c) for c in risk_block.columns}
    risk_block = risk_block.rename(columns=rename_map)

    # Some LLM labels repeat across annual additions. Sum duplicate categories
    # within the same firm-year so each column is one exposure dimension.
    id_block = pd.DataFrame({"Ticker": tickers, "Year": year})
    risk_block = risk_block.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    risk_block = risk_block.T.groupby(level=0).sum().T
    return pd.concat([id_block, risk_block], axis=1), [normalize_category_name(c) for c in raw_risk_columns]


def normalize_rows(matrix: pd.DataFrame) -> pd.DataFrame:
    risk_cols = [c for c in matrix.columns if c not in {"Ticker", "Year"}]
    matrix[risk_cols] = matrix[risk_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    row_sums = matrix[risk_cols].sum(axis=1)
    positive = row_sums > 0.0
    matrix.loc[positive, risk_cols] = matrix.loc[positive, risk_cols].div(row_sums[positive], axis=0)
    return matrix


def finalize_matrix(frames: list[pd.DataFrame]) -> pd.DataFrame:
    matrix = pd.concat(frames, ignore_index=True, sort=False).fillna(0.0)
    matrix = normalize_rows(matrix)
    risk_cols = [c for c in matrix.columns if c not in {"Ticker", "Year"}]
    matrix = matrix.sort_values(["Year", "Ticker"]).reset_index(drop=True)
    return matrix[["Ticker", "Year", *sorted(risk_cols)]]


def build_matrices(variant_root: Path, base_year: int, end_year: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    meso_frames: list[pd.DataFrame] = []
    macro_frames: list[pd.DataFrame] = []
    audit_records: list[dict[str, object]] = []

    for year in range(base_year, end_year + 1):
        year_dir = variant_root / f"output_risk_factor_{year}"
        meso_frame, raw_columns = read_year_vectors(vector_path(year_dir, base_year, year), year)
        meso_frames.append(meso_frame)

        parent_map = load_meso_parent_map(year_dir, base_year, year)
        risk_cols = [c for c in meso_frame.columns if c not in {"Ticker", "Year"}]
        unmapped = sorted(c for c in risk_cols if c not in parent_map)
        macro_block = meso_frame[risk_cols].rename(
            columns={c: parent_map.get(c, "Unmapped Macro Risk") for c in risk_cols}
        )
        macro_block = macro_block.T.groupby(level=0).sum().T
        macro_frames.append(pd.concat([meso_frame[["Ticker", "Year"]], macro_block], axis=1))

        audit_records.append(
            {
                "Year": year,
                "Raw_Vector_Columns": len(raw_columns),
                "Unique_Meso_Columns": len(risk_cols),
                "Macro_Columns": len(macro_block.columns),
                "Unmapped_Meso_Columns": len(unmapped),
                "Unmapped_Examples": "; ".join(unmapped[:5]),
            }
        )

    return finalize_matrix(meso_frames), finalize_matrix(macro_frames), pd.DataFrame(audit_records)


def default_macro_output(output: Path) -> Path:
    text = str(output)
    if "meso" in text:
        return Path(text.replace("meso", "macro"))
    return output.with_name(f"{output.stem}_macro{output.suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant-root", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="Backward-compatible Meso output path.")
    parser.add_argument("--output-meso", type=Path)
    parser.add_argument("--output-macro", type=Path)
    parser.add_argument("--audit-output", type=Path)
    parser.add_argument("--level", choices=["meso", "macro", "both"], default="both")
    parser.add_argument("--base-year", type=int, default=2006)
    parser.add_argument("--end-year", type=int, default=2024)
    args = parser.parse_args()

    if args.output is None and args.output_meso is None and args.output_macro is None:
        raise SystemExit("Provide --output, --output-meso, or --output-macro.")

    meso_output = args.output_meso or args.output
    macro_output = args.output_macro or (default_macro_output(meso_output) if meso_output else args.output_macro)
    audit_output = args.audit_output or (
        (meso_output or macro_output).with_name("taxonomy_matrix_build_audit.csv")
    )

    if args.level in {"meso", "both"} and meso_output is None:
        raise SystemExit("--level meso/both requires --output or --output-meso.")
    if args.level in {"macro", "both"} and macro_output is None:
        raise SystemExit("--level macro/both requires --output-macro or a Meso --output path.")

    meso_matrix, macro_matrix, audit = build_matrices(args.variant_root, args.base_year, args.end_year)

    if args.level in {"meso", "both"}:
        meso_output.parent.mkdir(parents=True, exist_ok=True)
        meso_matrix.to_csv(meso_output, index=False)
        risk_cols = [c for c in meso_matrix.columns if c not in {"Ticker", "Year"}]
        non_empty_rows = int((meso_matrix[risk_cols].sum(axis=1) > 0).sum()) if risk_cols else 0
        print(f"Wrote Meso matrix: {len(meso_matrix):,} rows, {len(risk_cols):,} risk columns -> {meso_output}")
        print(f"Meso rows with positive exposure mass: {non_empty_rows:,}")

    if args.level in {"macro", "both"}:
        macro_output.parent.mkdir(parents=True, exist_ok=True)
        macro_matrix.to_csv(macro_output, index=False)
        risk_cols = [c for c in macro_matrix.columns if c not in {"Ticker", "Year"}]
        non_empty_rows = int((macro_matrix[risk_cols].sum(axis=1) > 0).sum()) if risk_cols else 0
        print(f"Wrote Macro matrix: {len(macro_matrix):,} rows, {len(risk_cols):,} risk columns -> {macro_output}")
        print(f"Macro rows with positive exposure mass: {non_empty_rows:,}")

    audit_output.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(audit_output, index=False)
    if int(audit["Unmapped_Meso_Columns"].sum()) > 0:
        print(f"WARNING: found unmapped Meso columns. See {audit_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
