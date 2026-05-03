# Research Validation Report

## Verified Sections

- Section 3 data architecture was checked against `README.md`, `docs/output_manifest.md`, `scripts/run_pipeline.sh`, and the GAT/portfolio source modules.
- Section 4 taxonomy logic was checked against the dynamic-taxonomy scripts and annual run logs.
- Section 5 graph/ST-GAT logic was checked against `src/gat/GAT_data_pipeline.py`, `src/gat/GAT_models.py`, and forecast/objective scripts.
- Section 7 OOS metrics were regenerated from paired Macro/Meso default panels and paired Macro/Meso full-window `theta040` sensitivity panels.
- Section 8 portfolio timing, turnover, transaction costs, and metrics were checked against `src/portfolio/portfolio_backtest.py`, then rerun for both default Meso and `theta040`.
- Portfolio HAC/Newey-West inference was regenerated with `scripts/evaluate_portfolio_inference.py`.

## Rewritten Conservative Sections

- OOS and portfolio results are explicitly tied to the default full-window taxonomy and the completed `theta040` sensitivity variant.
- DAV, Fama-MacBeth, and SAR appendices remain methodology/diagnostic sections unless source output tables are present.
- The report no longer claims unconditional Meso ST-GAT dominance. Default-taxonomy OOS results are described as mixed; `theta040` forecast improvements are described as stronger but portfolio-sensitive.
- Macro ST-GAT outputs are now treated as paired sensitivity evidence where local source CSVs exist; Optuna, multi-seed, and DAV source tables are not treated as headline evidence unless present.

## Formula Additions

- Added a formula compendium appendix covering forecast metrics, graph diagnostics, loss/regularization, portfolio metrics, bootstrap intervals, Newey-West/HAC, and Fama-MacBeth inference.
- Fixed the dynamic deviation indicator notation to avoid a missing LaTeX dependency.
- Added explicit full-window sensitivity and paired Macro/Meso downstream robustness estimands.

## Data-Source Additions

- Expanded Section 3 to document textual SEC data, financial market data, macro proxies, graph data, forecast outputs, portfolio data, validation outputs, and derived features.
- Added source/frequency/granularity/purpose/transformations discussion for each data family.
- Clarified that large raw, intermediate, and generated CSV artifacts are excluded from version control and documented through manifests.

## Taxonomy Improvements

- Integrated the dynamic-taxonomy source artifacts as the empirical basis for Section 4.
- Added full non-expert explanation of embeddings, semantic similarity, clustering, hierarchy, LLM labeling, centroid evolution, and noise handling.
- Verified default full-window logs for 2006-2024: 578,516 total risk factors, 475 final Meso categories, 349 ADD actions, 56 MERGE actions, and 0 REORGANIZE actions.
- Executed a full-window `theta040` sensitivity run on real reconstructed paragraph inputs: 578,516 total risk factors, 258 final Meso categories, 132 ADD actions, 69 MERGE actions, and 3 REORGANIZE actions.
- Built default and `theta040` ST-GAT-ready Macro and Meso exposure matrices with `scripts/build_taxonomy_variant_matrix.py`.
- Generated 2024 category coverage, taxonomy-topology, and LVS dynamic taxonomy EDA artifacts with `scripts/generate_sensitivity_report_artifacts.py`.

## Statistical Improvements

- Added explicit formulas and intuition for RMSE, MAE, MSE, Spearman, graph density, Sharpe, Sortino, maximum drawdown, beta, turnover, Newey-West/HAC, bootstrap confidence intervals, and Fama-MacBeth inference.
- Clarified that short OOS windows make bootstrap and HAC tests diagnostic rather than definitive.
- Kept nominal and adjusted portfolio inference interpretations distinct.
- Regenerated robust OOS diagnostics for paired Macro/Meso panels. Default Meso does not show stable OOS improvement; `theta040` Meso volatility improvements have positive bootstrap intervals. Macro graphs are much denser but underperform identity baselines.
- Regenerated portfolio inference. Default ST-GAT return-only spread is 16.26% annualized with HAC `p=0.034` and BH `q=0.076`; `theta040` ST-GAT return-only spread is 9.33% annualized with HAC `p=0.007` and BH `q=0.044`, but below its identity return-only spread of 11.68%.

## Remaining Risks

- The remaining sensitivity grid points beyond `theta040` require the same long-running full-window LLM-assisted evolution procedure before they can be treated as empirical results.
- The local dynamic-taxonomy source directory is 1.4 GB and contains files above GitHub’s normal 100 MB limit; it is therefore ignored locally rather than committed.
- Large generated CSV outputs are ignored for GitHub readiness; numerical claims are copied into the report and validation docs from the regenerated local outputs.
- Risk-year 2024 final target-window caveat remains because the July 2025-June 2026 window is not fully closed as of the validation context.
- LLM labeling can introduce semantic style drift, and category removal is not implemented.

## Final Confidence Level

High confidence for report compilation, formula coverage, taxonomy-methodology integration, paired Macro/Meso default outputs, and the executed `theta040` sensitivity path.

Moderate confidence for broad investment conclusions because the OOS window is short and portfolio ranking is taxonomy-sensitive.
