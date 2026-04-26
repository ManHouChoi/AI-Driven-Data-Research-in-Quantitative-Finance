

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
├── .gitignore
├── report/
│   └── First_Draft_Final.pdf
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
│   └── run_pipeline.sh       # Optional end-to-end execution script
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

## Suggested Execution Order

The full pipeline is modular. Depending on available data, the typical run order is:

```bash
# 1. Build / update extracted risk disclosure data
python src/data/build_master_csv.py

# 2. Build enhanced financial and macro feature panel
python src/data/generate_fin_data.py
python src/data/build_enhanced_macro_data.py

# 3. Build or update the taxonomy
python src/taxonomy/base_year_taxonomy.py
python src/taxonomy/classification.py
python src/taxonomy/risk_scoring.py

# 4. Run ST-GAT optimization and forecasting
python src/gat/GAT_objective_macro.py
python src/gat/GAT_objective_meso.py
python src/gat/GAT_forecast_macro.py
python src/gat/GAT_forecast_meso.py

# 5. Run econometric validation
python src/econometrics/fmb_risk_premium.py
python src/econometrics/st_gcn_volatility.py
python src/econometrics/network_evolution_analysis.py

# 6. Run portfolio backtest if included
python src/portfolio/<portfolio_backtest_script>.py
```

Some scripts may require local file paths or API credentials to be configured before execution.

## Main Report

The final research report should be placed under:

```text
report/First_Draft_Final.pdf
```

The report documents the full methodology, including dynamic taxonomy construction, topology-only ST-GAT formulation, macro-versus-meso graph diagnostics, out-of-sample forecasting performance, portfolio backtesting, and supplemental econometric validation.

## Reproducibility Notes

- The ST-GAT experiments use chronological splits: training years 2006–2016, validation years 2017–2020, and out-of-sample test years 2021–2024.
- Node features are standardized using training-year statistics only.
- The Meso ST-GAT is the primary model specification for portfolio construction.
- Annual forecasts are held fixed over the July-to-June forecast window, while portfolio weights are rebalanced monthly.

## Authors

- CHAN Ho Lam
- CHOI Man Hou
- TSOI Ching Yi

Dual Degree Program in Technology and Management, HKUST.