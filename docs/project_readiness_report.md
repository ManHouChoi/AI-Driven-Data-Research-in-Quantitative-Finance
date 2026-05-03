# Project Readiness Report

Generated after the repository audit and reproducibility upgrade pass.

## Executive Summary

This repository contains the final review-submission package for the IEDA4920
Final Year Project, **AI-Driven Data Research in Quantitative Finance**. The
project develops an end-to-end framework that converts SEC Item 1A `Risk
Factors` disclosures into hierarchical textual-risk exposures, semantic peer
networks, topology-only ST-GAT forecasts, econometric diagnostics, and academic
portfolio-backtesting outputs.

The central research contribution is a strict graph-topology ablation. Annual
10-K risk paragraphs are extracted from EDGAR filings, mapped into a dynamic
macro-meso taxonomy, aggregated into firm-year exposure vectors, and converted
into annual semantic peer graphs. The full ST-GAT model uses
`A_t = I + A_risk,t`, while the identity baseline uses `A_t = I`; therefore,
the main experiment isolates whether textual-risk peer topology adds predictive
information beyond each firm's own financial and market features.

The finalized report is conservative about the default Meso graph evidence.
On the exported 2021-2024 OOS review panel, the default Meso ST-GAT improves
return MAE and return rank correlation, but it does not dominate the identity
baseline on averaged OOS metrics. A full-window `theta040` taxonomy sensitivity
run gives stronger forecast-error evidence: averaged RMSE improves from 0.3523
to 0.3176 and averaged MAE improves from 0.2546 to 0.2012 relative to its
matched identity baseline, with the strongest gain in volatility RMSE.
Paired Macro-level runs are now included as sensitivity evidence: they are much
denser than Meso graphs but underperform identity baselines, supporting the
report's conclusion that broad coverage is not enough without selective
semantic resolution.

Graph-density diagnostics support the interpretation that taxonomy evolution
settings matter. During the OOS period, the default Meso graph retains 32-96
off-diagonal directed edges per year, while the `theta040` graph retains
100-630. The report therefore frames graph topology as a validated modeling
choice that must be sensitivity-tested, rather than as an automatically
beneficial preprocessing output.

The portfolio extension is presented as academic validation, not as live-trading
evidence. Annual Meso ST-GAT forecasts are held fixed over their July-to-June
forecast window, while portfolios are rebalanced monthly with 10 bps transaction
costs, 5 bps slippage, and SPY as benchmark. Under the default dynamic
taxonomy, the return-only long-short strategy reports 7.31% annualized return,
8.34% annualized volatility, Sharpe 0.88, Sortino 1.52, maximum drawdown of
-8.06%, and beta of 0.30. Its top-minus-bottom spread is 16.26% annualized with
conventional p=0.080 and HAC/Newey-West p=0.034 before multiple-testing
adjustment. The `theta040` variant improves forecast errors but has weaker raw
portfolio ranking than its identity baseline.

The final package is deliberately conservative about unsupported evidence.
Old taxonomy-coverage percentages, unsupported AAPL migration claims, DAV/EGARCH-X
BIC comparisons, Fama-MacBeth tables, and SAR/network regression claims are not
used as headline findings unless their source tables are regenerated and added
to the output manifest. The new 2024 category coverage and firm-level case-study
figures are source-backed by `outputs/taxonomy/sensitivity/*.csv`. The available DAV peak diagnostics are retained only as
event-local context: 93 figures were parsed, with 20 positive improvements, 73
negative improvements, and mean improvement of -2.40%.

Before GitHub cleanup, the complete local artifact set passed the lightweight
validation suite with 35 passes, 7 warnings, and 0 failures as of 2026-05-03.
The warnings are artifact-scope and research caveats rather than code crashes:
optional multi-seed, DAV, and taxonomy-interim files are absent from the
lightweight package; four financial feature values require downstream
train-period median imputation; and risk-year 2024 has a forward target window
ending on 2026-06-30. The committed GitHub
repository is a lightweight code, report, and documentation package; large raw
data, intermediate files, generated outputs, logs, and the local virtual
environment are excluded from version control and preserved outside the repo as
local artifacts.

## Repository Structure After Cleanup

```text
IEDA4920_FYP/
├── README.md
├── requirements.txt
├── .gitattributes
├── configs/default.yaml
├── docs/
│   ├── data_dictionary.md
│   ├── dav_peak_analysis_summary.md
│   ├── experiment_manifest.md
│   ├── output_manifest.md
│   └── project_readiness_report.md
├── report/
│   ├── figures/
│   ├── Research_Report.pdf
│   └── Research_Report.tex
├── scripts/
│   ├── check_github_ready.py
│   ├── evaluate_oos_robustness.py
│   ├── evaluate_portfolio_inference.py
│   ├── generate_report_figures.py
│   ├── summarize_dav_peak_analysis.py
│   ├── run_multi_seed_forecasts.py
│   ├── run_pipeline.sh
│   └── validate_pipeline.py
└── src/
    ├── data/
    ├── econometrics/
    ├── gat/
    ├── portfolio/
    ├── taxonomy/
    └── utils/
```

Large raw/intermediate data and generated output CSVs remain excluded by
`.gitignore`.

## Reproducibility Instructions

Install dependencies in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Validate current local artifacts:

```bash
.venv/bin/python scripts/validate_pipeline.py --as-of 2026-05-03
```

Refresh report-local figures from the current CSV outputs:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh report-figures
```

Refresh robust OOS and portfolio inference addenda:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh robust-eval
```

Refresh final-forecast seed-stability outputs:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh multi-seed
```

Summarize local DAV peak-event diagnostics:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh dav-peak-summary
```

Check GitHub upload readiness:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh github-check
```

Compile the report PDF:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=report report/Research_Report.tex
```

## Full Pipeline Execution Command

Dry-run the full pipeline order before launching long-running jobs:

```bash
DRY_RUN=1 PYTHON=.venv/bin/python bash scripts/run_pipeline.sh full
```

Run the full pipeline:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh full
```

SEC download requires `SEC_CONTACT_EMAIL`. Taxonomy construction requires
`DEEPSEEK_API_KEY`.

## Validation/Test Command

```bash
PYTHON=.venv/bin/python FYP_AS_OF_DATE=2026-05-03 bash scripts/run_pipeline.sh validate
```

Latest observed result:

```text
Summary: 35 passed, 7 warnings, 0 failed
```

Additional local checks completed:

```bash
.venv/bin/python -m compileall -q src scripts
git diff --check
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh github-check
rg -n "LaTeX Warning: (Reference|Citation|There were undefined)|Package natbib Warning|^!|referenced but does not exist" report/Research_Report.log
```

The Python compile check and whitespace check completed cleanly. The LaTeX log
search returned no unresolved citations, unresolved references, or hard compile
errors after rebuilding `report/Research_Report.pdf`.

## Key Methodological Checks Passed

- Chronological split: Train 2006-2016, validation 2017-2020, test/OOS
  2021-2024.
- Feature preprocessing statistics are fit on train years only.
- Meso graph tensors have stable annual snapshot shapes.
- Graph self-loop contract is enforced with one unit-weight self-loop per
  global node.
- Identity baseline contains only diagonal unit-weight edges.
- Forward target windows follow July-to-June alignment.
- Portfolio weights earn returns strictly after the rebalance date.
- Monthly portfolio return mapping uses the next available monthly return date.
- Transaction cost and slippage conversion is validated.
- Fixed random seeds reproduce Python, NumPy, and Torch RNG samples.

## Remaining Limitations

- Risk-year 2024 realized OOS target and portfolio evidence remains incomplete
  until the July 2025 to June 2026 target window closes on 2026-06-30.
- Four financial feature values are missing in the current enhanced financial
  matrix and are handled by train-period median imputation.
- Old taxonomy coverage percentages remain excluded; the new coverage figure is
  backed by `outputs/taxonomy/sensitivity/taxonomy_macro_coverage_2024.csv`.
- Firm-level case-study figures are retained as interpretability diagnostics,
  not proof of cross-sectional predictive value.
- DAV/EGARCH-X, Fama-MacBeth, and SAR/network appendix claims are treated as
  supplemental or unverified where source result tables are absent or empty.
- DAV peak-event diagnostics are now summarized from 93 local PNG figures:
  20 positive improvements, 73 negative improvements, mean improvement -2.40%.
  These are treated as event-local diagnostics rather than broad DAV evidence.
- Large data and output files are local artifacts rather than Git-tracked
  assets, so a reviewer needs the supplied local artifact set or must rerun the
  relevant stages.

## Verified Report Claims

| Claim Area | Source Output | Status |
|---|---|---|
| Macro ST-GAT OOS forecast metrics | `outputs/gat/GAT_output_macro/goodness_of_fit_metrics_macro_OOS.csv` | Verified to current CSV, with 2024 caveat |
| Meso ST-GAT OOS forecast metrics | `outputs/gat/GAT_output_meso/goodness_of_fit_metrics_meso_OOS.csv` | Verified to current CSV, with 2024 caveat |
| Identity baseline panel predictions | `outputs/gat/GAT_output_*/*Baseline*` and ST-GAT panel CSVs | Verified via validation contracts |
| Macro/Meso graph density diagnostics | `outputs/gat/GAT_output_*/graph_diagnostics_*` | Verified to current diagnostic CSVs |
| Portfolio summary metrics | `outputs/portfolio/GAT_portfolio_output/portfolio_performance_summary_ranked.csv` | Verified to current CSV, with 2024 caveat |
| Top-minus-bottom spread diagnostic | `outputs/portfolio/GAT_portfolio_output/top_bottom_spread_diagnostics.csv` | Verified to current CSV, with 2024 caveat |
| Portfolio timing and transaction costs | Portfolio weight/turnover files and `src/portfolio/portfolio_backtest.py` | Verified by validation suite |
| Robust OOS paired comparisons | `outputs/gat/robust_oos_evaluation.csv` | Generated from current OOS forecast panels, with 2024 caveat |
| Robust portfolio inference | `outputs/portfolio/GAT_portfolio_output/*robust_inference.csv` | Generated from current monthly spread and return files, with 2024 caveat |
| Seed-stability forecast replication | `outputs/gat/multi_seed/multi_seed_oos_summary.csv` | Generated from final forecast reruns across seeds 41, 42, and 43 |
| DAV peak-event diagnostic summary | `outputs/econometrics/dav_peak_analysis/dav_peak_summary.csv`; `docs/dav_peak_analysis_summary.md` | Figure-derived summary generated from 93 DAV peak PNGs |

## Unverified Or Weakened Claims

| Claim Area | Current Treatment |
|---|---|
| Old taxonomy coverage improvement values, including 94.7% and 98.5% | Removed from headline evidence; replaced by source-backed 2024 category coverage |
| AAPL firm-level taxonomy migration case study | Replaced by generated multi-firm taxonomy profile case studies |
| DAV/EGARCH-X BIC improvement values | Treated as supplemental/unverified because the aggregate metrics CSV is empty locally |
| Fama-MacBeth coefficient and significance table | Treated as supplemental/unverified until source tables are regenerated |
| SAR/network regression claims | Treated as supplemental/unverified until source result tables are regenerated |
| CRSP/Compustat/Stooq sourcing language | Corrected or caveated to match current implemented/local artifacts |

## Recommended Future Work

- Execute the remaining expanded taxonomy sensitivity grid points end-to-end
  before treating them as empirical results.
- Recompute DAV/EGARCH-X, Fama-MacBeth, and SAR/network result tables with
  machine-readable CSV outputs.
- Re-run final OOS and portfolio evaluation after 2026-06-30 so risk-year 2024
  targets are fully observed.
- Add a small CI job that runs `scripts/validate_pipeline.py` on a minimal
  fixture dataset.

## Modified Files

- `README.md`
- `.gitattributes`
- `report/Research_Report.pdf`
- `report/Research_Report.tex`
- `src/data/build_enhanced_macro_data.py`
- `src/data/build_master_csv.py`
- `src/data/data_pipeline.py`
- `src/data/generate_fin_data.py`
- `src/econometrics/fmb_risk_premium.py`
- `src/econometrics/network_evolution_analysis.py`
- `src/econometrics/plot_fmb.py`
- `src/econometrics/st_gcn_volatility.py`
- `src/econometrics/volatility_model.py`
- `src/gat/GAT_forecast_macro.py`
- `src/gat/GAT_forecast_meso.py`
- `src/gat/GAT_objective_macro.py`
- `src/gat/GAT_objective_meso.py`
- `src/portfolio/portfolio_backtest.py`
- `src/taxonomy/base_year_taxonomy.py`
- `src/taxonomy/classification.py`
- `src/taxonomy/risk_scoring.py`
- `scripts/run_pipeline.sh`

## New Files

- `configs/default.yaml`
- `docs/data_dictionary.md`
- `docs/experiment_manifest.md`
- `docs/output_manifest.md`
- `docs/project_readiness_report.md`
- `report/figures/README.md`
- `report/figures/graph_density_macro_meso.png`
- `report/figures/oos_metric_comparison.png`
- `report/figures/portfolio_top_bottom_spread.png`
- `scripts/generate_report_figures.py`
- `scripts/check_github_ready.py`
- `scripts/summarize_dav_peak_analysis.py`
- `scripts/evaluate_oos_robustness.py`
- `scripts/evaluate_portfolio_inference.py`
- `scripts/validate_pipeline.py`
- `scripts/run_multi_seed_forecasts.py`
- `src/utils/__init__.py`
- `src/utils/io.py`
- `src/utils/logging_utils.py`
- `src/utils/paths.py`
- `src/utils/seeding.py`

## Suggested Git Commit Message

```text
Improve reproducibility validation, robustness checks, and report traceability
```
