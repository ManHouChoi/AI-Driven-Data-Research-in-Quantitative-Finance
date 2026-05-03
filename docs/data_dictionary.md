# Data Dictionary

This document records the canonical local artifacts used by the current project
state. Large raw/intermediate files may be excluded from Git, but their schemas
should remain stable for reproducibility.

## SEC Item 1A Text Artifacts

### `data/raw/risk_factors_output/`

Extracted Item 1A HTML snippets.

Expected filename pattern:

```text
ITEM1A_RISK_FACTORS_{TICKER}_{YEAR}.html
```

### `data/interim/model_input/all_risk_factors_master.csv`

Paragraph-level risk disclosure table used by taxonomy construction and
classification.

Required columns:

| Column | Description |
|---|---|
| `Company` | Ticker or company identifier parsed from the source file. |
| `Year` | Filing/report year used as the risk disclosure year. |
| `No.` | Paragraph or risk-factor sequence number. |
| `Main Title` | Heuristic main heading. |
| `Sub-Title` | Heuristic subheading. |
| `Paragraph Text` | Extracted paragraph text. |
| `full_text` | Concatenated text used for embedding/classification. |

## Taxonomy Artifacts

### `data/interim/taxonomy/taxonomy_base.json`

Hierarchical macro/meso taxonomy with category centroids.

Expected top-level keys:

| Key | Description |
|---|---|
| `macro_categories` | Macro risk categories and centroid vectors. |
| `meso_categories` | Meso risk categories, parent macro links, and centroid vectors. |

### `data/interim/taxonomy/hierarchical_risk_categories.csv`

Reviewer-readable taxonomy table. This file should mirror the JSON taxonomy
names and parent-child structure.

## Risk Exposure Matrices

### `data/interim/scoring_outputs/risk_scores_macro_annual.csv`

Firm-year macro exposure matrix.

Required columns:

| Column | Description |
|---|---|
| `Ticker` | Equity ticker. |
| `Year` | Risk disclosure year. |
| macro exposure columns | Normalized disclosure intensity by macro category. Positive rows should sum to one. |

### `data/interim/scoring_outputs/risk_scores_meso_annual.csv`

Firm-year meso exposure matrix.

Required columns:

| Column | Description |
|---|---|
| `Ticker` | Equity ticker. |
| `Year` | Risk disclosure year. |
| meso exposure columns | Normalized disclosure intensity by macro-to-meso category. Positive rows should sum to one. |

## Financial Feature Matrix

### `data/interim/scoring_outputs/fin_data_matrix_enhanced.csv`

Annual firm-year financial features and one-period-ahead targets.

Required columns:

| Column | Description |
|---|---|
| `Year` | Risk disclosure year `t`. |
| `Ticker` | Equity ticker. |
| `Vol` | Annualized volatility over July `t` through June `t+1`. |
| `Downside_Vol` | Downside volatility over the feature window. |
| `MA_200_Ratio` | Price relative to 200-day moving average near feature-window end. |
| `Momentum_11M` | 11-month momentum ending before the target window. |
| `Dollar_Volume` | Average dollar volume over the feature window. |
| `Log_Dollar_Volume` | Log transformed dollar volume. |
| `Target_Ret` | Forward return over July `t+1` through June `t+2`. |
| `Target_Vol` | Forward realized volatility over July `t+1` through June `t+2`. |
| `SP500_Ret` | S&P 500 return proxy over the feature window. |
| `SP500_Vol` | S&P 500 volatility proxy over the feature window. |
| `VIX_Avg` | Average VIX over the feature window. |
| `VIX_Change` | VIX change over the feature window. |
| `TenY_Yield_Avg` | Average 10-year Treasury yield proxy. |
| `TenY_Yield_Change` | Change in 10-year Treasury yield proxy. |

Timing convention:

| Risk Year | Feature Window | Target Window |
|---|---|---|
| `t` | July 1 `t` to June 30 `t+1` | July 1 `t+1` to June 30 `t+2` |

As of 2026-05-03, the 2024 target window has not fully closed.

## Forecast Panels

### `outputs/gat/GAT_output_macro/ST_GAT_vs_Baseline_Panel_macro.csv`
### `outputs/gat/GAT_output_meso/ST_GAT_vs_Baseline_Panel_meso.csv`

Firm-year prediction panels.

Required columns:

| Column | Description |
|---|---|
| `Ticker` | Equity ticker. |
| `Year` | Forecast risk year. |
| `Dataset` | `Train`, `Validation`, or `Test (OOS)`. |
| `Actual_Ret` | Realized forward return target. |
| `Actual_Vol` | Realized forward volatility target. |
| `GAT_Pred_Ret` | ST-GAT predicted return. |
| `GAT_Pred_Vol` | ST-GAT predicted volatility. |
| `Base_Pred_Ret` | Identity-baseline predicted return. |
| `Base_Pred_Vol` | Identity-baseline predicted volatility. |

## Portfolio Artifacts

### `outputs/portfolio/GAT_portfolio_output/monthly_returns.csv`

Monthly realized return panel used by the portfolio backtest.

### `outputs/portfolio/GAT_portfolio_output/weights_*.csv`

Monthly target holdings.

Required columns:

| Column | Description |
|---|---|
| `Rebalance_Date` | Month-end date on which weights are formed. |
| `Holding_Return_Date` | Next available monthly return date earned by the rebalance. |
| `Ticker` | Held equity ticker. |
| `Weight` | Portfolio weight after rebalancing. |
| `Score_Method` | Ranking score specification. |
| `Model_Prefix` | `GAT` or `Base`. |

### `outputs/portfolio/GAT_portfolio_output/top_bottom_spread_diagnostics.csv`

Cross-sectional top-minus-bottom spread diagnostics by model and score method.
