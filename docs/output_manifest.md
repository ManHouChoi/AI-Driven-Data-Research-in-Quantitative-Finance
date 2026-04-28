# Output Manifest

This manifest maps major reported outputs to their generating scripts and
current validation status. It should be updated whenever outputs are
regenerated.

| Artifact | Generating Script | Purpose | Current Validation Notes |
|---|---|---|---|
| `data/interim/model_input/all_risk_factors_master.csv` | `src/data/build_master_csv.py` | Paragraph-level Item 1A corpus | Schema documented; not regenerated in Phase 7. |
| `data/interim/taxonomy/taxonomy_base.json` | `src/taxonomy/base_year_taxonomy.py` | Macro/meso taxonomy and centroids | Present in interim taxonomy folder. |
| `data/interim/taxonomy/hierarchical_risk_categories.csv` | `src/taxonomy/base_year_taxonomy.py` | Human-readable taxonomy table | Present in interim taxonomy folder. |
| `data/interim/processed/classification_outputs/*.csv` | `src/taxonomy/classification.py` | Paragraph-level macro/meso labels | Present locally; large set not exhaustively validated by Phase 6. |
| `data/interim/scoring_outputs/risk_scores_macro_annual.csv` | `src/taxonomy/risk_scoring.py` | Firm-year macro exposure vectors | Validator confirms required keys and normalized positive rows. |
| `data/interim/scoring_outputs/risk_scores_meso_annual.csv` | `src/taxonomy/risk_scoring.py` | Firm-year meso exposure vectors | Validator confirms required keys and normalized positive rows. |
| `data/interim/scoring_outputs/fin_data_matrix_enhanced.csv` | `src/data/generate_fin_data.py` | Financial features and forward targets | Validator confirms schema and train-only downstream imputation; warns on 4 missing feature values and incomplete 2024 target window as of 2026-04-27. |
| `outputs/gat/GAT_output_macro/optuna_best_params_macro.json` | `src/gat/GAT_objective_macro.py` | Macro graph Optuna best params | Present; forecast script loads this file when available. |
| `outputs/gat/GAT_output_meso/optuna_best_params_meso.json` | `src/gat/GAT_objective_meso.py` | Meso graph Optuna best params | Present; forecast script and validator use its tau when available. |
| `outputs/gat/GAT_output_macro/ST_GAT_vs_Baseline_Panel_macro.csv` | `src/gat/GAT_forecast_macro.py` | Macro ST-GAT and identity panel predictions | Validator confirms schema, required values, and chronological split. |
| `outputs/gat/GAT_output_meso/ST_GAT_vs_Baseline_Panel_meso.csv` | `src/gat/GAT_forecast_meso.py` | Meso ST-GAT and identity panel predictions | Validator confirms schema, required values, and chronological split. |
| `outputs/gat/GAT_output_macro/goodness_of_fit_metrics_macro_OOS.csv` | `src/gat/GAT_forecast_macro.py` | Macro OOS metrics | File presence checked; numerical claims still require report-level trace review. |
| `outputs/gat/GAT_output_meso/goodness_of_fit_metrics_meso_OOS.csv` | `src/gat/GAT_forecast_meso.py` | Meso OOS metrics | File presence checked; numerical claims still require report-level trace review. |
| `outputs/gat/robust_oos_evaluation.csv` | `scripts/evaluate_oos_robustness.py` | Year-block bootstrap and annual-block paired comparisons versus identity baseline | Generated from current ST-GAT panel outputs; 2024 target-window caveat still applies. |
| `outputs/gat/robust_oos_annual_loss_differences.csv` | `scripts/evaluate_oos_robustness.py` | Annual mean squared/absolute error improvements versus identity baseline | Generated from current ST-GAT panel outputs. |
| `outputs/gat/multi_seed/multi_seed_oos_metrics.csv` | `scripts/run_multi_seed_forecasts.py` | Final forecast metrics across random seeds | Generated from validation-selected Optuna params without overwriting canonical headline outputs. |
| `outputs/gat/multi_seed/multi_seed_oos_summary.csv` | `scripts/run_multi_seed_forecasts.py` | Mean/std/min/max OOS metrics across seeds | Generated from the multi-seed forecast directories. |
| `outputs/gat/GAT_output_macro/graph_diagnostics_macro_*.csv` | `src/gat/GAT_objective_macro.py`, `src/gat/GAT_forecast_macro.py` | Macro graph-density diagnostics | Present; not all tables are currently referenced in README. |
| `outputs/gat/GAT_output_meso/graph_diagnostics_meso_*.csv` | `src/gat/GAT_objective_meso.py`, `src/gat/GAT_forecast_meso.py` | Meso graph-density diagnostics | Present; not all tables are currently referenced in README. |
| `outputs/portfolio/GAT_portfolio_output/portfolio_performance_summary_ranked.csv` | `src/portfolio/portfolio_backtest.py` | Ranked portfolio performance summary | Validator confirms schema. |
| `outputs/portfolio/GAT_portfolio_output/top_bottom_spread_diagnostics.csv` | `src/portfolio/portfolio_backtest.py` | Top-minus-bottom spread diagnostics | Validator confirms schema and timing through the weight files. |
| `outputs/portfolio/GAT_portfolio_output/top_bottom_spread_robust_inference.csv` | `scripts/evaluate_portfolio_inference.py` | HAC/Newey-West and Benjamini-Hochberg inference for spread diagnostics | Generated from existing monthly spread files. |
| `outputs/portfolio/GAT_portfolio_output/strategy_return_robust_inference.csv` | `scripts/evaluate_portfolio_inference.py` | HAC/Newey-West and Benjamini-Hochberg inference for monthly strategy returns | Generated from existing strategy return files. |
| `outputs/portfolio/GAT_portfolio_output/weights_*.csv` | `src/portfolio/portfolio_backtest.py` | Monthly portfolio weights | Validator confirms next-month holding dates for the canonical long-short return-only file. |
| `report/figures/oos_metric_comparison.png` | `scripts/generate_report_figures.py` | Report plot comparing Macro/Meso ST-GAT and identity OOS metrics | Generated from current `goodness_of_fit_metrics_*_OOS.csv` files. |
| `report/figures/graph_density_macro_meso.png` | `scripts/generate_report_figures.py` | Report plot comparing Macro/Meso OOS graph density | Generated from current graph-diagnostic CSV files. |
| `report/figures/portfolio_top_bottom_spread.png` | `scripts/generate_report_figures.py` | Report plot for top-minus-bottom ranking diagnostic | Generated from current `top_bottom_spread_diagnostics.csv`. |
| `outputs/econometrics/dav_benchmark_analysis/benchmark_metrics.csv` | `src/econometrics/volatility_model.py` | DAV/EGARCH-X benchmark table | Present locally; report claims need explicit trace checking before they are treated as verified. |
| `outputs/econometrics/dav_peak_analysis/dav_peak_summary.csv` | `scripts/summarize_dav_peak_analysis.py` | Figure-derived DAV peak-event summary | Generated from 93 `*_multi_peak.png` diagnostics; all 93 title-level improvement values parsed by OCR. This supports event-local diagnostics only, not broad DAV dominance. |
| `docs/dav_peak_analysis_summary.md` | `scripts/summarize_dav_peak_analysis.py` | Committed Markdown audit summary for DAV peak diagnostics | Derived from the local figure set so the report's DAV peak numbers remain traceable even though large PNG outputs are ignored. |
| `outputs/econometrics/fmb_risk_premiums.png` | `src/econometrics/plot_fmb.py` | Fama-MacBeth visualization | Figure present; source CSV trace should be confirmed in Phase 8/9. |
| `outputs/econometrics/network_evolution/*` | `src/econometrics/network_evolution_analysis.py` | Network topology/drift diagnostics | Current output directory may need regeneration because the runner now points to a canonical path. |
| `report/IEDA4920_Final_Presentation.pptx` | `scripts/generate_final_presentation.py` | Final 20-minute review presentation deck | Generated from final report narrative, verified output CSVs, and available repository figures. |
| `docs/final_submission_validation_report.md` | Manual finalization audit | Final submission validation record | Records files inspected, validation commands, report/PPTX status, and remaining review risks. |
| `docs/final_submission_changelog.md` | Manual finalization audit | Final submission changelog | Summarizes final report edits, claim-safety changes, deck generation, and limitations. |

Known current caveat:

- As of 2026-04-27, realized target claims for risk year 2024 are not fully
  supportable because the July 2025 to June 2026 target window has not closed.
