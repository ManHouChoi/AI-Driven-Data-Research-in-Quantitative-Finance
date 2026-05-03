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
| `data/interim/scoring_outputs/risk_scores_macro_annual.csv` | `src/taxonomy/risk_scoring.py` | Firm-year macro exposure vectors | Optional archival artifact; not required for the default Meso report claims. |
| `data/interim/scoring_outputs/risk_scores_meso_annual.csv` | `src/taxonomy/risk_scoring.py` | Firm-year meso exposure vectors | Validator confirms required keys and normalized positive rows. |
| `data/interim/scoring_outputs/fin_data_matrix_enhanced.csv` | `src/data/generate_fin_data.py` | Financial features and forward targets | Validator confirms schema and train-only downstream imputation; warns on incomplete 2024 target window as of current validation. |
| `outputs/gat/GAT_output_macro/optuna_best_params_macro.json` | `src/gat/GAT_objective_macro.py` | Macro graph Optuna best params | Optional archival artifact; absent from the default validation set. |
| `outputs/gat/GAT_output_meso/optuna_best_params_meso.json` | `src/gat/GAT_objective_meso.py` | Meso graph Optuna best params | Optional; forecast script uses built-in defaults when absent. |
| `outputs/gat/GAT_output_macro/ST_GAT_vs_Baseline_Panel_macro.csv` | `src/gat/GAT_forecast_macro.py` | Macro ST-GAT and identity panel predictions | Present and included in paired Macro/Meso Section 7 sensitivity comparison. |
| `outputs/gat/GAT_output_meso/ST_GAT_vs_Baseline_Panel_meso.csv` | `src/gat/GAT_forecast_meso.py` | Meso ST-GAT and identity panel predictions | Regenerated in this pass and validated. |
| `outputs/gat/taxonomy_sensitivity/theta040/ST_GAT_vs_Baseline_Panel_meso.csv` | `src/gat/GAT_forecast_meso.py` via `scripts/run_taxonomy_sensitivity.py` | `theta040` sensitivity Meso prediction panel | Regenerated in this pass from real full-window taxonomy sensitivity outputs. |
| `outputs/gat/taxonomy_sensitivity/theta040_macro/ST_GAT_vs_Baseline_Panel_macro.csv` | `src/gat/GAT_forecast_macro.py` via `scripts/run_taxonomy_sensitivity.py` | `theta040` sensitivity Macro prediction panel | Present and included in paired Macro/Meso Section 7 sensitivity comparison. |
| `outputs/gat/GAT_output_macro/goodness_of_fit_metrics_macro_OOS.csv` | `src/gat/GAT_forecast_macro.py` | Macro OOS metrics | Present and used in paired Macro/Meso Section 7 sensitivity comparison. |
| `outputs/gat/GAT_output_meso/goodness_of_fit_metrics_meso_OOS.csv` | `src/gat/GAT_forecast_meso.py` | Meso OOS metrics | Regenerated in this pass and traced into Section 7. |
| `outputs/gat/taxonomy_sensitivity/theta040_macro/goodness_of_fit_metrics_macro_OOS.csv` | `src/gat/GAT_forecast_macro.py` via `scripts/run_taxonomy_sensitivity.py` | `theta040` Macro OOS metrics | Present and traced into Section 7 paired Macro/Meso comparison. |
| `outputs/gat/taxonomy_sensitivity/theta040/goodness_of_fit_metrics_meso_OOS.csv` | `src/gat/GAT_forecast_meso.py` via `scripts/run_taxonomy_sensitivity.py` | `theta040` Meso OOS metrics | Regenerated in this pass and traced into Section 7. |
| `outputs/gat/robust_oos_evaluation.csv` | `scripts/evaluate_oos_robustness.py` | Year-block bootstrap and annual-block paired comparisons versus identity baseline | Generated from current ST-GAT panel outputs; 2024 target-window caveat still applies. |
| `outputs/gat/robust_oos_annual_loss_differences.csv` | `scripts/evaluate_oos_robustness.py` | Annual mean squared/absolute error improvements versus identity baseline | Generated from current ST-GAT panel outputs. |
| `outputs/gat/multi_seed/multi_seed_oos_metrics.csv` | `scripts/run_multi_seed_forecasts.py` | Final forecast metrics across random seeds | Optional protocol; not regenerated in this pass. |
| `outputs/gat/multi_seed/multi_seed_oos_summary.csv` | `scripts/run_multi_seed_forecasts.py` | Mean/std/min/max OOS metrics across seeds | Optional protocol; not regenerated in this pass. |
| `outputs/gat/GAT_output_macro/graph_diagnostics_macro_*.csv` | `src/gat/GAT_objective_macro.py`, `src/gat/GAT_forecast_macro.py` | Macro graph-density diagnostics | Used to show broad Macro topology over-connects the OOS graph. |
| `outputs/gat/GAT_output_meso/graph_diagnostics_meso_*.csv` | `src/gat/GAT_objective_meso.py`, `src/gat/GAT_forecast_meso.py` | Meso graph-density diagnostics | Regenerated for default Meso. |
| `outputs/gat/taxonomy_sensitivity/theta040/graph_diagnostics_meso_forecast_tau.csv` | `src/gat/GAT_forecast_meso.py` via `scripts/run_taxonomy_sensitivity.py` | `theta040` Meso graph-density diagnostics | Regenerated and traced into Section 7. |
| `outputs/gat/taxonomy_downstream_sensitivity_summary.csv` | `scripts/generate_sensitivity_report_artifacts.py` | Paired Macro/Meso downstream sensitivity summary | Regenerated from default and `theta040` forecast, graph, and portfolio outputs. |
| `outputs/taxonomy/sensitivity/taxonomy_variant_summary.csv` | `scripts/generate_sensitivity_report_artifacts.py` | Dynamic taxonomy evolution summary by completed variant | Includes final Meso counts, action totals, deviation rates, and top 2024 Macro coverage. |
| `outputs/taxonomy/sensitivity/taxonomy_macro_coverage_2024.csv` | `scripts/generate_sensitivity_report_artifacts.py` | 2024 Macro category coverage comparison | Source table for the taxonomy coverage figure and report interpretation. |
| `outputs/taxonomy/sensitivity/taxonomy_lvs_dynamic_case_summary.csv` | `scripts/generate_sensitivity_report_artifacts.py` | LVS dynamic taxonomy case-study summary | Source table for event-aligned vector movement, nearest-peer similarity, and top category interpretation. |
| `outputs/taxonomy/sensitivity/taxonomy_lvs_meso_trajectory.csv` | `scripts/generate_sensitivity_report_artifacts.py` | LVS selected Meso exposure trajectories | Source table for the LVS dynamic taxonomy EDA figure. |
| `outputs/taxonomy/sensitivity/taxonomy_lvs_nearest_peers.csv` | `scripts/generate_sensitivity_report_artifacts.py` | LVS annual nearest semantic peers | Source table for the vector-network EDA figure. |
| `outputs/portfolio/GAT_portfolio_output/portfolio_performance_summary_ranked.csv` | `src/portfolio/portfolio_backtest.py` | Ranked portfolio performance summary | Validator confirms schema. |
| `outputs/portfolio/GAT_portfolio_output/top_bottom_spread_diagnostics.csv` | `src/portfolio/portfolio_backtest.py` | Top-minus-bottom spread diagnostics | Validator confirms schema and timing through the weight files. |
| `outputs/portfolio/GAT_portfolio_output/top_bottom_spread_robust_inference.csv` | `scripts/evaluate_portfolio_inference.py` | HAC/Newey-West and Benjamini-Hochberg inference for spread diagnostics | Generated from existing monthly spread files. |
| `outputs/portfolio/GAT_portfolio_output/strategy_return_robust_inference.csv` | `scripts/evaluate_portfolio_inference.py` | HAC/Newey-West and Benjamini-Hochberg inference for monthly strategy returns | Generated from existing strategy return files. |
| `outputs/portfolio/GAT_portfolio_output/weights_*.csv` | `src/portfolio/portfolio_backtest.py` | Monthly portfolio weights | Validator confirms next-month holding dates for the canonical long-short return-only file. |
| `report/figures/oos_metric_comparison.png` | `scripts/generate_report_figures.py` | Report plot comparing Macro and Meso ST-GAT/identity OOS metrics under default and `theta040` taxonomies | Regenerated from current default and `theta040` OOS CSV files. |
| `report/figures/graph_density_macro_meso.png` | `scripts/generate_report_figures.py` | Report plot comparing Macro and Meso OOS graph density under default and `theta040` taxonomies | Regenerated from current graph-diagnostic CSV files. |
| `report/figures/taxonomy_macro_coverage_comparison.png` | `scripts/generate_sensitivity_report_artifacts.py` | Coverage comparison for final default and `theta040` risk categories | Regenerated from 2024 classified taxonomy outputs. |
| `report/figures/taxonomy_topology_theta040.png` | `scripts/generate_sensitivity_report_artifacts.py` | Topological visualization of the best-tested `theta040` taxonomy | Regenerated from the 2024 taxonomy JSON and classified outputs. |
| `report/figures/taxonomy_lvs_dynamic_eda.png` | `scripts/generate_sensitivity_report_artifacts.py` | LVS dynamic taxonomy EDA | Regenerated from annual Macro/Meso risk-vector outputs. |
| `report/figures/taxonomy_lvs_vector_network.png` | `scripts/generate_sensitivity_report_artifacts.py` | LVS vector path and nearest semantic peers | Regenerated from annual Meso risk-vector outputs. |
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

- As of 2026-05-03, realized target claims for risk year 2024 are not fully
  supportable because the July 2025 to June 2026 target window has not closed.
