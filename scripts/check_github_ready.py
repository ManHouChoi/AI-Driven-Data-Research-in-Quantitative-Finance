#!/usr/bin/env python3
"""Pre-upload checks for keeping the GitHub repository lightweight and safe."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


DEFAULT_SIZE_LIMIT_MB = 95
REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    ".gitignore",
    ".gitattributes",
    "report/Research_Report.pdf",
    "report/Research_Report.tex",
    "scripts/run_pipeline.sh",
    "scripts/validate_pipeline.py",
]
SECRET_NAME_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"(^|/)\.env($|\.)",
        r"secret",
        r"credential",
        r"(^|/).*\.pem$",
        r"(^|/).*\.key$",
    ]
]
SECRET_VALUE_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"sk-[A-Za-z0-9_\-]{20,}",
        r"AKIA[0-9A-Z]{16}",
        r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*['\"][^'\"]{12,}['\"]",
    ]
]
TEXT_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".tex",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def run_git(args: list[str], root: Path) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return result.stdout


def upload_candidates(root: Path) -> list[Path]:
    """Return tracked and untracked files not excluded by .gitignore."""

    raw = run_git(["ls-files", "-co", "--exclude-standard", "-z"], root)
    return sorted(root / name.decode("utf-8") for name in raw.split(b"\0") if name)


def is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES and path.stat().st_size <= 1_000_000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--size-limit-mb",
        type=int,
        default=DEFAULT_SIZE_LIMIT_MB,
        help="Maximum allowed size for a Git upload candidate.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    candidates = upload_candidates(root)
    size_limit = args.size_limit_mb * 1024 * 1024

    failures: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            failures.append(f"missing required repository file: {rel}")

    for path in candidates:
        rel = path.relative_to(root).as_posix()
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            continue

        if size > size_limit:
            failures.append(f"upload candidate exceeds {args.size_limit_mb} MB: {rel}")

        if any(pattern.search(rel) for pattern in SECRET_NAME_PATTERNS):
            failures.append(f"secret-like filename is not ignored: {rel}")

        if is_text_candidate(path):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in SECRET_VALUE_PATTERNS:
                if pattern.search(text):
                    failures.append(f"secret-like value detected in: {rel}")
                    break

    tracked_raw = run_git(["ls-files", "-z"], root)
    tracked = [name for name in tracked_raw.split(b"\0") if name]
    if not tracked:
        warnings.append("no tracked files found; initialize Git tracking before upload")

    print(f"Checked {len(candidates)} Git upload candidate files.")
    print(f"Size limit: {args.size_limit_mb} MB per file.")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("GitHub readiness check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
