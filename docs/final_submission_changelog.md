# Final Submission Changelog

## Report Edits

- Created backups:
  - `report/Research_Report_backup_before_finalization.tex`
  - `report/Research_Report_backup_before_finalization.pdf`
- Recompiled the final report to `report/Research_Report.pdf`.
- Removed all required WIP-marker hits from `report/Research_Report.tex`.
- Rewrote the 2024 target-window discussion into final review-submission language:
  - current 2021-2024 OOS review-panel results are retained;
  - final archival results can be refreshed after the full 2024 target window closes.
- Updated the abstract, contributions, research-gap summary, feature-target alignment, output verification map, limitations, and conclusion so they tell the same claim-safe story.
- Added paired Macro/Meso Section 7 sensitivity evidence and expanded the Section 4 taxonomy hyperparameter grid.
- Added best-tested taxonomy coverage, taxonomy-topology, an LVS dynamic taxonomy EDA, and Appendix A encoding/embedding examples to the report narrative.

## Claim-Safety Changes

- Removed unsupported taxonomy coverage percentages from headline contributions.
- Reintroduced taxonomy coverage only where backed by `outputs/taxonomy/sensitivity/taxonomy_macro_coverage_2024.csv`.
- Replaced the unsupported AAPL migration case with an event-aligned LVS taxonomy EDA backed by `outputs/taxonomy/sensitivity/taxonomy_lvs_dynamic_case_summary.csv`.
- Removed unsupported Fama-MacBeth numerical table claims from the appendix and kept only the methodology extension.
- Removed unsupported SAR coefficient, p-value, and R-squared claims from the appendix and kept only the network-validation framework.
- Removed aggregate DAV BIC-improvement claims because the benchmark metrics CSV is empty.
- Retained DAV peak-event diagnostics only as narrow event-local evidence.

## Figure And Table Changes

- Kept verified or source-traceable figures:
  - `report/figures/oos_metric_comparison.png`
  - `report/figures/graph_density_macro_meso.png`
  - `report/figures/taxonomy_macro_coverage_comparison.png`
  - `report/figures/taxonomy_topology_theta040.png`
  - `report/figures/taxonomy_lvs_dynamic_eda.png`
  - `report/figures/taxonomy_lvs_vector_network.png`
  - `outputs/portfolio/GAT_portfolio_output/portfolio_equity_curves.png`
  - `report/figures/portfolio_top_bottom_spread.png`
- Kept the old `outputs/figures/taxonomy_coverage_improvement.png` out of headline evidence; the new coverage figure is generated from source CSVs.
- Removed unsupported numerical interpretation from the Fama-MacBeth and SAR appendices.
- Updated the output verification map to use final-review wording:
  - "Verified for review panel"
  - "Deferred audit"
  - "Deferred validation"

## Repository Overview Media

- Added `docs/assets/overview/project-overview.mp4` as the compact GitHub README video overview.
- Added `docs/assets/overview/st-gat-demo.png`, `docs/assets/overview/st-gat-network.png`, and `docs/assets/overview/taxonomy-demo.png` as static repository overview previews.
- Linked the deployed interactive dashboard from `README.md`.
- Removed the generated presentation deck from the GitHub commit surface; the final public package keeps the report PDF, video overview, and demo instead.

## Validation Results

- Report compiled successfully with `latexmk`.
- Pipeline validation passed with 35 passed checks, 7 warnings, and 0 failures after the expanded Macro/Meso sensitivity edit.
- GitHub readiness check passed.
- Python compile check passed.
- Final report and repository overview files were scanned for the required WIP-marker phrases.

## Repository Cleanup For GitHub

- Moved local-only bulky folders out of the repository working tree:
  - `.venv/`
  - `data/raw/`, `data/interim/`, `data/cache/`, and `data/tmp/`
  - `outputs/`
  - `logs/`
- Removed `.DS_Store`, LaTeX auxiliary files, and pre-finalization report backups from the repository folder.
- Preserved the expected folder structure with lightweight `.gitkeep` placeholders under `data/` and `outputs/`.
- Removed the generated presentation deck from Git tracking and ignored future `.pptx` files.

## Remaining Limitations

- The current review package includes 2024 rows from existing outputs; final archival outputs can be refreshed after the 2024 target window fully closes on 2026-06-30.
- Additional sensitivity grid points beyond `theta040` require the same long-running LLM-assisted full-window taxonomy procedure before they should be treated as empirical results.
- Firm-level case studies are interpretability diagnostics, not cross-sectional proof of forecast value.
- Fama-MacBeth, DAV BIC, and SAR appendix modules require regenerated source tables for inferential claims.
- Portfolio performance remains an academic validation exercise, not a live-trading recommendation.
