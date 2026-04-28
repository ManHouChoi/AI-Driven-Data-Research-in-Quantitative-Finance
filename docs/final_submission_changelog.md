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

## Claim-Safety Changes

- Removed taxonomy coverage percentages from headline contributions.
- Reframed the taxonomy coverage figure as a conceptual diagnostic because the standalone source table is absent.
- Reframed the AAPL migration case as a feasible case-study design rather than an empirical result.
- Removed unsupported Fama-MacBeth numerical table claims from the appendix and kept only the methodology extension.
- Removed unsupported SAR coefficient, p-value, and R-squared claims from the appendix and kept only the network-validation framework.
- Removed aggregate DAV BIC-improvement claims because the benchmark metrics CSV is empty.
- Retained DAV peak-event diagnostics only as narrow event-local evidence.

## Figure And Table Changes

- Kept verified or source-traceable figures:
  - `report/figures/oos_metric_comparison.png`
  - `report/figures/graph_density_macro_meso.png`
  - `outputs/portfolio/GAT_portfolio_output/portfolio_equity_curves.png`
  - `report/figures/portfolio_top_bottom_spread.png`
- Kept `outputs/figures/taxonomy_coverage_improvement.png` only as a conceptual diagnostic.
- Removed unsupported numerical interpretation from the Fama-MacBeth and SAR appendices.
- Updated the output verification map to use final-review wording:
  - "Verified for review panel"
  - "Deferred audit"
  - "Deferred validation"

## Presentation Deck Construction

- Added `scripts/generate_final_presentation.py`.
- Added `python-pptx>=1.0.2` to `requirements.txt`.
- Generated `report/IEDA4920_Final_Presentation.pptx`.
- Regenerated the final deck after inspecting the newer reference deck `report/IEDA4000E_Presentation_Deck_1126.pptx`.
- Added a data-derived cover background at `report/figures/final_deck_cover_background.png`, generated from the current ST-GAT long-short return series.
- Built a 28-slide final research presentation with the requested storyline:
  - motivation and problem statement;
  - data sources, SEC extraction, risk scoring, and financial feature/target construction;
  - taxonomy and risk-vector construction;
  - semantic peer graphs and topology-only ST-GAT;
  - identity baseline and chronological split;
  - OOS forecasting results;
  - graph density diagnostics;
  - portfolio setup, equity curves, and spread diagnostics;
  - limitations, validation, conclusion, and Q&A.
- Reworked the deck style toward the newer reference's presentation rhythm:
  - finance-style dark cover;
  - Times New Roman typography;
  - navy/gold accent system;
  - assertion-style slide titles;
  - evidence-led chart/table layouts;
  - bottom takeaway lines instead of repetitive footer navigation.

## Validation Results

- Report compiled successfully with `latexmk`.
- Pipeline validation passed with 45 passed checks, 2 warnings, and 0 failures.
- GitHub readiness check passed.
- Python compile check passed.
- PPTX package integrity check passed.
- Final report and final deck were scanned for the required WIP-marker phrases.

## Repository Cleanup For GitHub

- Moved local-only bulky folders out of the repository working tree:
  - `.venv/`
  - `data/raw/`, `data/interim/`, `data/cache/`, and `data/tmp/`
  - `outputs/`
  - `logs/`
- Removed `.DS_Store`, LaTeX auxiliary files, and pre-finalization report backups from the repository folder.
- Preserved the expected folder structure with lightweight `.gitkeep` placeholders under `data/` and `outputs/`.

## Remaining Limitations

- The current review package includes 2024 rows from existing outputs; final archival outputs can be refreshed after the 2024 target window fully closes on 2026-06-30.
- Taxonomy coverage percentages require a standalone reproducible source table before they should be treated as empirical findings.
- AAPL firm-level taxonomy migration requires regenerated source artifacts before becoming a case-study result.
- Fama-MacBeth, DAV BIC, and SAR appendix modules require regenerated source tables for inferential claims.
- Portfolio performance remains an academic validation exercise, not a live-trading recommendation.
