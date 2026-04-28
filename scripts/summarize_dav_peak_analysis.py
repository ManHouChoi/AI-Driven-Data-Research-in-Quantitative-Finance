#!/usr/bin/env python3
"""Summarize DAV peak-analysis figures into auditable tables.

The current `dav_peak_analysis` artifact set contains PNG diagnostics rather
than a machine-readable result table. This script parses ticker/risk labels from
file names and, when Tesseract OCR is available, extracts the title-level
``Overall Peak Accuracy Improvement`` percentage from each figure. The output is
a reproducibility bridge: it makes the existing figure-only experiment traceable
without pretending it is a substitute for the original model-level source code.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median, pstdev

from PIL import Image, ImageOps


DEFAULT_INPUT_DIR = Path("outputs/econometrics/dav_peak_analysis")
DEFAULT_CSV = Path("outputs/econometrics/dav_peak_analysis/dav_peak_summary.csv")
DEFAULT_MD = Path("docs/dav_peak_analysis_summary.md")


@dataclass(frozen=True)
class PeakRow:
    ticker: str
    macro_risk: str
    meso_risk: str
    improvement_pct: float | None
    figure: str
    ocr_text: str


def humanize(label: str) -> str:
    label = label.replace("&", " & ")
    label = label.replace(",", ", ")
    label = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", label)
    for connector in ("and", "of", "for"):
        label = re.sub(rf"([a-z]){connector}(?=\s+[A-Z])", rf"\1 {connector}", label)
    label = re.sub(r"\s+", " ", label)
    return label.strip()


def parse_filename(path: Path) -> tuple[str, str, str]:
    stem = path.stem
    if not stem.endswith("_multi_peak"):
        raise ValueError(f"unexpected DAV peak filename: {path.name}")
    payload = stem.removesuffix("_multi_peak")
    ticker, risk = payload.split("_", 1)
    macro, meso = risk.split("->", 1)
    return ticker, humanize(macro), humanize(meso)


def extract_title_text(path: Path, work_dir: Path, tesseract_bin: str) -> str:
    image = Image.open(path).convert("L")
    # The two-line figure title sits above the subplot grid. Cropping avoids
    # axis tick labels, and local files avoid a macOS/Tesseract /tmp path issue.
    crop = image.crop((250, 32, 1250, 78))
    crop = ImageOps.autocontrast(crop).resize((crop.width * 3, crop.height * 3))
    crop_path = work_dir / f"{path.stem[:80]}.png"
    crop.save(crop_path)
    result = subprocess.run(
        [tesseract_bin, str(crop_path), "stdout", "--psm", "7", "--dpi", "300"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def parse_improvement(text: str) -> float | None:
    match = re.search(r"([-+][0-9]+(?:\.[0-9]+)?)\s*%", text)
    if not match:
        return None
    return float(match.group(1))


def collect_rows(input_dir: Path) -> tuple[list[PeakRow], list[str]]:
    figures = sorted(input_dir.glob("*_multi_peak.png"))
    tesseract_bin = shutil.which("tesseract")
    warnings: list[str] = []
    rows: list[PeakRow] = []

    if not figures:
        warnings.append(f"no DAV peak figures found under {input_dir}")
        return rows, warnings

    if not tesseract_bin:
        warnings.append("tesseract not found; wrote filename metadata without improvement percentages")

    with tempfile.TemporaryDirectory(dir=".") as tmp:
        work_dir = Path(tmp)
        for fig in figures:
            ticker, macro, meso = parse_filename(fig)
            text = ""
            improvement = None
            if tesseract_bin:
                text = extract_title_text(fig, work_dir, tesseract_bin)
                improvement = parse_improvement(text)
                if improvement is None:
                    warnings.append(f"could not OCR improvement percentage from {fig.name}: {text!r}")
            rows.append(
                PeakRow(
                    ticker=ticker,
                    macro_risk=macro,
                    meso_risk=meso,
                    improvement_pct=improvement,
                    figure=fig.as_posix(),
                    ocr_text=text,
                )
            )

    return rows, warnings


def write_csv(rows: list[PeakRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "ticker",
                "macro_risk",
                "meso_risk",
                "improvement_pct",
                "figure",
                "ocr_text",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "ticker": row.ticker,
                    "macro_risk": row.macro_risk,
                    "meso_risk": row.meso_risk,
                    "improvement_pct": "" if row.improvement_pct is None else row.improvement_pct,
                    "figure": row.figure,
                    "ocr_text": row.ocr_text,
                }
            )


def summary_stats(rows: list[PeakRow]) -> dict[str, float | int]:
    vals = [row.improvement_pct for row in rows if row.improvement_pct is not None]
    if not vals:
        return {
            "n": len(rows),
            "parsed": 0,
            "positive": 0,
            "negative": 0,
            "mean": float("nan"),
            "median": float("nan"),
            "std": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
        }
    return {
        "n": len(rows),
        "parsed": len(vals),
        "positive": sum(v > 0 for v in vals),
        "negative": sum(v < 0 for v in vals),
        "mean": mean(vals),
        "median": median(vals),
        "std": pstdev(vals),
        "min": min(vals),
        "max": max(vals),
    }


def fmt(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if value != value:
        return "NA"
    return f"{value:.2f}"


def write_markdown(rows: list[PeakRow], output_path: Path, warnings: list[str]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats = summary_stats(rows)
    parsed = [row for row in rows if row.improvement_pct is not None]
    top = sorted(parsed, key=lambda row: row.improvement_pct or 0, reverse=True)[:10]
    bottom = sorted(parsed, key=lambda row: row.improvement_pct or 0)[:5]

    lines = [
        "# DAV Peak-Analysis Summary",
        "",
        "This table is derived from the existing PNG diagnostics in",
        "`outputs/econometrics/dav_peak_analysis/`. It is a figure-derived",
        "audit artifact, not a replacement for the original model-estimation CSV.",
        "",
        "## Aggregate Diagnostics",
        "",
        f"- Figures scanned: {stats['n']}",
        f"- Improvements parsed by OCR: {stats['parsed']}",
        f"- Positive improvements: {stats['positive']}",
        f"- Negative improvements: {stats['negative']}",
        f"- Mean improvement: {fmt(stats['mean'])}%",
        f"- Median improvement: {fmt(stats['median'])}%",
        f"- Standard deviation: {fmt(stats['std'])} percentage points",
        f"- Range: {fmt(stats['min'])}% to {fmt(stats['max'])}%",
        "",
        "## Top Positive Peak Improvements",
        "",
        "| Ticker | Macro Risk | Meso Risk | Improvement |",
        "|---|---|---|---:|",
    ]
    for row in top:
        lines.append(
            f"| {row.ticker} | {row.macro_risk} | {row.meso_risk} | {row.improvement_pct:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Largest Negative Peak Improvements",
            "",
            "| Ticker | Macro Risk | Meso Risk | Improvement |",
            "|---|---|---|---:|",
        ]
    )
    for row in bottom:
        lines.append(
            f"| {row.ticker} | {row.macro_risk} | {row.meso_risk} | {row.improvement_pct:.2f}% |"
        )

    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    rows, warnings = collect_rows(args.input_dir)
    write_csv(rows, args.output_csv)
    write_markdown(rows, args.output_md, warnings)

    stats = summary_stats(rows)
    print(
        "DAV peak summary: "
        f"{stats['parsed']}/{stats['n']} improvements parsed; "
        f"positive={stats['positive']}, negative={stats['negative']}, "
        f"mean={fmt(stats['mean'])}%"
    )
    print(f"Wrote {args.output_csv}")
    print(f"Wrote {args.output_md}")
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    return 1 if warnings and stats["parsed"] == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
