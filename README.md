

# IEDA4920 FYP: AI-Driven Data Research in Quantitative Finance

This repository contains the codebase and report materials for the IEDA4920 Final Year Project, **AI-Driven Data Research in Quantitative Finance**, developed as a corporate project with WorldQuant Consulting (Beijing) Co., Ltd.

The project converts SEC Item 1A `Risk Factors` disclosures into quantitative risk signals, dynamic semantic peer networks, graph neural network forecasts, econometric validation outputs, and portfolio backtesting results.

## Project Overview

The research pipeline consists of five major components:

1. **SEC 10-K risk disclosure extraction**  
   Download, parse, clean, and structure Item 1A risk-factor text from annual filings.

2. **Dynamic macro–meso risk taxonomy construction**  
   Build a base-year taxonomy using embeddings, UMAP, HDBSCAN, and LLM-assisted category refinement, then update the taxonomy dynamically as new risk themes emerge.

3. **Risk scoring and firm-year exposure construction**  
   Classify risk paragraphs into the evolved taxonomy and aggregate them into firm-year risk exposure vectors.

4. **ST-GAT forecasting**  
   Construct topology-only semantic peer graphs from risk exposure similarity and train Spatio-Temporal Graph Attention Networks for one-year-ahead return and volatility forecasting.

5. **Econometric and portfolio validation**  
   Validate the text-derived signals using DAV/EGARCH-X volatility models, Fama-MacBeth regressions, risk-contagion network analysis, and dynamic portfolio backtesting.

## Repository Structure

```text
IEDA4920_FYP/
├── README.md
├── requirements.txt
├── configs/
│   └── default.yaml
├── docs/
│   ├── data_dictionary.md
│   ├── experiment_manifest.md
│   ├── final_submission_changelog.md
│   ├── final_submission_validation_report.md
│   ├── output_manifest.md
│   └── project_readiness_report.md
├── .gitignore
├── .gitattributes
├── report/
│   ├── figures/              # Report-local figures generated from output CSVs
│   ├── IEDA4920_Final_Presentation.pptx
│   ├── Research_Report.pdf
│   └── Research_Report.tex
├── data/
│   ├── raw/                  # Raw data files; usually excluded from Git
│   ├── interim/              # Intermediate extracted/cleaned files
│   └── processed/            # Final model-ready CSV files
├── outputs/
│   ├── figures/              # Report and diagnostic figures
│   ├── tables/               # Exported result tables
│   ├── gat/                  # ST-GAT forecast outputs
│   ├── portfolio/            # Portfolio backtest outputs
│   └── econometrics/         # DAV/FMB/SAR outputs
├── scripts/
│   ├── check_github_ready.py         # GitHub upload preflight check
│   ├── evaluate_oos_robustness.py    # OOS paired/bootstrap diagnostics
│   ├── evaluate_portfolio_inference.py
│   ├── generate_final_presentation.py
│   ├── generate_report_figures.py
│   ├── run_multi_seed_forecasts.py
│   ├── summarize_dav_peak_analysis.py
│   ├── run_pipeline.sh               # Stage-based execution driver
│   └── validate_pipeline.py          # Lightweight artifact and timing validator
└── src/
    ├── data/                 # SEC extraction and financial-data pipelines
    ├── taxonomy/             # Taxonomy construction, classification, risk scoring
    ├── gat/                  # ST-GAT data pipeline, models, objectives, forecasts
    ├── portfolio/            # Dynamic portfolio backtesting logic
    └── econometrics/         # DAV, Fama-MacBeth, volatility, and network validation
```

## Code Modules

### `src/data/`

Contains scripts for downloading, extracting, cleaning, and merging textual and financial data.

Expected modules include:

```text
build_master_csv.py
build_enhanced_macro_data.py
data_pipeline.py
generate_fin_data.py
```

### `src/taxonomy/`

Contains taxonomy construction, paragraph classification, and risk-scoring logic.

Expected modules include:

```text
base_year_taxonomy.py
classification.py
risk_scoring.py
```

### `src/gat/`

Contains ST-GAT data preparation, model definitions, hyperparameter objectives, and forecasting scripts.

Expected modules include:

```text
GAT_data_pipeline.py
GAT_models.py
GAT_objective_macro.py
GAT_objective_meso.py
GAT_forecast_macro.py
GAT_forecast_meso.py
```

### `src/econometrics/`

Contains econometric validation scripts, including volatility modeling, Fama-MacBeth regressions, and risk-contagion/network diagnostics.

Expected modules include:

```text
fmb_risk_premium.py
st_gcn_volatility.py
network_evolution_analysis.py
plot_fmb.py
```

If the volatility model is maintained as a separate script, it should also be placed here.

### `src/portfolio/`

Contains dynamic portfolio backtesting scripts that convert annual ST-GAT predictions into monthly rebalanced long-only and long-short strategies.

## Data and Output Policy

Large raw datasets, downloaded filings, API outputs, intermediate caches, and model artifacts should generally not be committed to GitHub. Keep them under local `data/` or `outputs/` folders and exclude them through `.gitignore` unless they are small, anonymized, and necessary for reproducibility.

Recommended commit policy:

- Commit source code, README, requirements, lightweight configuration files, and the final report PDF.
- Do not commit raw SEC HTML files, large CSV extracts, model checkpoints, API keys, or local cache files.
- Commit selected final figures and tables only if they are used directly in the report or README.

## GitHub Upload Readiness

Before uploading the folder to GitHub, run the preflight check:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh github-check
```

The checker scans Git upload candidates, not ignored local data, and fails if a
candidate file exceeds the default 95 MB limit or if common secret-like files
are not ignored. The repository is intended to upload code, docs, configuration,
report source/PDF, and selected report figures. Large local folders such as
`.venv/`, `data/`, `outputs/`, and `logs/` are excluded by `.gitignore`.

## Environment Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Reproducibility Commands

Validate the current local artifacts without rerunning expensive stages:

```bash
.venv/bin/python scripts/validate_pipeline.py --as-of 2026-04-27
```

Equivalent runner command:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh validate
```

Check GitHub upload hygiene:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh github-check
```

Dry-run the full research pipeline order before launching long-running jobs:

```bash
DRY_RUN=1 PYTHON=.venv/bin/python bash scripts/run_pipeline.sh full
```

Run a specific stage:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh gat-forecast
```

The runner sets canonical `FYP_*` environment variables for the current
repository layout, including:

```text
data/interim/model_input/
data/interim/taxonomy/
data/interim/scoring_outputs/
outputs/gat/GAT_output_macro/
outputs/gat/GAT_output_meso/
outputs/portfolio/GAT_portfolio_output/
```

## Suggested Execution Order

The full pipeline is modular. Depending on available data, the typical run order is:

```bash
# 1. SEC Item 1A download/extraction, then master paragraph CSV
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh sec-download
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh master-csv

# 2. Taxonomy construction, paragraph classification, and risk scoring
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh taxonomy
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh classify
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh risk-scoring

# 3. Financial feature/target matrix
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh financial

# 4. ST-GAT optimization and forecasting
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh gat-objective
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh gat-forecast

# Optional: final-forecast seed stability, written separately under outputs/gat/multi_seed/
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh multi-seed

# 5. Portfolio and econometric validation
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh portfolio
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh econometrics

# 6. Robust inference addenda, report figures, and final validation
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh robust-eval
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh report-figures
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh dav-peak-summary
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh validate
```

Some stages require network access or credentials. SEC download should set
`SEC_CONTACT_EMAIL`; taxonomy construction requires `DEEPSEEK_API_KEY`.

## Main Report

The final research report should be placed under:

```text
report/Research_Report.pdf
report/IEDA4920_Final_Presentation.pptx
```

Report-local figures that are generated from current CSV outputs can be
refreshed with:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh report-figures
```

The final presentation deck can be regenerated with:

```bash
.venv/bin/python scripts/generate_final_presentation.py
```

Robust OOS and portfolio-inference addenda can be refreshed with:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh robust-eval
```

DAV peak-event figure diagnostics can be summarized with:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh dav-peak-summary
```

This optional stage uses local Tesseract OCR if available to extract the
title-level peak-improvement percentages from the existing DAV PNG diagnostics.

Final forecast seed-stability runs can be refreshed with:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh multi-seed
```

To customize seeds without changing source code:

```bash
FYP_MULTI_SEED_ARGS="--seeds 40,41,42,43,44" PYTHON=.venv/bin/python bash scripts/run_pipeline.sh multi-seed
```

The report documents the full methodology, including dynamic taxonomy construction, topology-only ST-GAT formulation, macro-versus-meso graph diagnostics, out-of-sample forecasting performance, portfolio backtesting, and supplemental econometric validation.

## Reproducibility Notes

- The ST-GAT experiments use chronological splits: training years 2006–2016, validation years 2017–2020, and out-of-sample test years 2021–2024.
- Node features are standardized using training-year statistics only.
- The Meso ST-GAT is the primary model specification for portfolio construction.
- Annual forecasts are held fixed over the July-to-June forecast window, while portfolio weights are rebalanced monthly.
- As of 2026-04-27, the risk-year 2024 forward target window has not fully closed because the July 2025 to June 2026 target window ends on 2026-06-30. Treat any realized 2024 OOS target or backtest claim as caveated until that window closes.
- See `configs/default.yaml`, `docs/data_dictionary.md`, `docs/output_manifest.md`, and `docs/experiment_manifest.md` for the current reproducibility map.

## Authors

- CHAN Ho Lam hlmchan@connect.ust.hk
- CHOI Man Hou mhchoiaf@connect.ust.hk
- TSOI Ching Yi cytsoiaa@connect.ust.hk

Dual Degree Program in Technology and Management, HKUST.
