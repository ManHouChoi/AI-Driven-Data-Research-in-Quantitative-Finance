# Taxonomy Update Integration Report

## Source Artifacts Used

- `May 2 update/Section4_Update.pdf` for the revised taxonomy narrative, including the 2006-only sensitivity table and non-expert embedding explanation.
- `May 2 update/build_taxonomy.py` for the authoritative base-year logic: `all-MiniLM-L6-v2`, UMAP, HDBSCAN, LLM labels, hybrid centroids, and nearest-centroid noise assignment.
- `May 2 update/dynamic_evolver.py` for annual evolution logic: nearest-centroid classification, deviation thresholding, deviation clustering, ADD/MERGE/REORGANIZE actions, and centroid persistence.
- `May 2 update/prompts.py` for macro, meso, and evolution prompt structure.
- `May 2 update/taxonomy/output_risk_factor_*/run_log.json` for verified annual counts, deviation rates, action counts, and final Meso category totals.
- `May 2 update/taxonomy/output_risk_factor_*/taxonomy_base.json` and `taxonomy_evolved.json` for taxonomy structure and centroid availability.
- `May 2 update/taxonomy/output_risk_factor_*/risk_vectors.csv` and `base_year_vectors.csv` for exposure-vector logic.
- `report/figures/taxonomy_semantic_decay_deviation_rate.jpg`, `taxonomy_lvs_composition_shift.jpg`, and `taxonomy_lvs_emerging_declining_risks.jpg` for Section 4 diagnostics.

## Taxonomy Logic Changed

- Rebuilt Section 4 around dynamic taxonomy evolution rather than a static K-Means-style taxonomy.
- Added explicit sentence-embedding, UMAP, HDBSCAN, cosine-similarity, hybrid-centroid, noise-resolution, and deviation-threshold equations.
- Clarified the Macro/Meso hierarchy and why Meso exposure vectors are the primary graph input.
- Clarified implemented actions: ADD, MERGE, and REORGANIZE are implemented; REMOVE is governance-only and not used in reported results.
- Used run logs, not the PDF narrative table, as the final source for full-window counts: 578,516 total risk factors processed across 2006-2024, 349 ADD actions, 56 MERGE actions, 0 REORGANIZE actions, and 475 final Meso categories.
- Added an expanded full-window sensitivity implementation for 2006-2024 variants through `scripts/run_taxonomy_sensitivity.py`, including Macro/Meso cluster sizes, UMAP settings, HDBSCAN minimum samples, centroid weights, merge weights, LLM prompt sample size, and seed variants.
- Added `scripts/build_taxonomy_variant_matrix.py` to turn annual variant `risk_vectors.csv` files into ST-GAT-ready firm-year Macro and Meso exposure matrices.
- Executed the full-window `theta040` sensitivity variant using real reconstructed yearly paragraph CSVs and API-backed LLM labeling. The variant reaches 258 final Meso categories by 2024, with 132 ADD, 69 MERGE, and 3 REORGANIZE actions.

## Report Sections Changed

- Section 3: expanded data architecture, source frequency, time period, granularity, transformations, and purpose.
- Section 4: rebuilt taxonomy methodology, expanded the full-window sensitivity protocol, and added best-tested taxonomy coverage/topology interpretation.
- Section 5: retained graph construction consistency with dynamic Meso exposure vectors.
- Section 6: consolidated tensor construction and experimental design to avoid repetition with the data chapter.
- Section 7: deepened the default and `theta040` forecasting comparison with paired Macro/Meso experiments, convergence discussion, graph-density mechanism, and downstream sensitivity interpretation.
- Section 8: added downstream `theta040` portfolio sensitivity and revised portfolio claims to match regenerated outputs.
- Limitations: framed the remaining sensitivity grid points as confirmatory extensions that require the same full-window LLM-assisted taxonomy procedure.
- Appendix A: added formula compendium.

## Figures Changed

- Added/retained taxonomy diagnostic figures:
  - `report/figures/taxonomy_semantic_decay_deviation_rate.jpg`
  - `report/figures/taxonomy_lvs_composition_shift.jpg`
  - `report/figures/taxonomy_lvs_emerging_declining_risks.jpg`
- Added new sensitivity figures:
  - `report/figures/taxonomy_category_evolution_default_theta040.png`
  - `report/figures/stgat_convergence_default_theta040.png`
  - `report/figures/taxonomy_downstream_sensitivity_dashboard.png`
  - `report/figures/taxonomy_macro_coverage_comparison.png`
  - `report/figures/taxonomy_topology_theta040.png`
  - `report/figures/taxonomy_case_study_macro_profiles.png`
- Replaced a missing portfolio-output path with committed figure `report/figures/portfolio_backtest_comparison.png`.
- Regenerated `report/figures/oos_metric_comparison.png`, `graph_density_macro_meso.png`, and `portfolio_top_bottom_spread.png` from current default/`theta040` outputs.
- Added a reproducible figure generator at `scripts/generate_sensitivity_report_artifacts.py`.

## Equations Changed

- Added text-to-context encoding, sentence embedding, cosine similarity, UMAP projection, HDBSCAN assignment, hybrid centroid, nearest-centroid assignment, dynamic deviation indicator, ADD/MERGE centroid update, exposure-vector normalization, expanded sensitivity grid, and paired Macro/Meso variant downstream improvement estimands.
- Fixed indicator notation from `\mathbbm{1}` to `\mathbf{1}` to avoid requiring an undeclared LaTeX package.
- Added appendix formulas for graph density, degree, Huber loss, regularization, RMSE, MAE, MSE, Spearman, R-squared, portfolio metrics, bootstrap intervals, Newey-West/HAC, and Fama-MacBeth inference.

## Downstream Sections Updated

- ST-GAT and portfolio sections now explicitly distinguish the default full-window taxonomy from the completed `theta040` variant.
- The new sensitivity workflow can propagate taxonomy variants into:
  - Macro and Meso exposure matrices,
  - Macro and Meso ST-GAT forecast panels,
  - monthly portfolio backtests.
- `theta040` was propagated through paired Macro/Meso forecast layers and the Meso portfolio layer. Remaining variants in the expanded grid are available through the runner but were not executed in this pass.
