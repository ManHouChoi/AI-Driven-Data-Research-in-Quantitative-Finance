# Final Submission Validation Report

Generated for the IEDA4920 FYP final review package.

## Files Inspected

- `README.md`
- `requirements.txt`
- `configs/default.yaml`
- `docs/output_manifest.md`
- `docs/experiment_manifest.md`
- `docs/data_dictionary.md`
- `docs/project_readiness_report.md`
- `report/Research_Report.tex`
- `report/Research_Report.pdf`
- `report/IEDA4920_Presentation_Deck_0301.pdf`
- `report/figures/`
- `outputs/figures/`
- `outputs/gat/`
- `outputs/portfolio/`
- `outputs/econometrics/`
- `data/interim/scoring_outputs/`
- `scripts/`
- `src/`

## Final Outputs Generated

- `report/Research_Report.tex`
- `report/Research_Report.pdf`
- `report/IEDA4920_Final_Presentation.pptx`
- `report/Research_Report_backup_before_finalization.tex`
- `report/Research_Report_backup_before_finalization.pdf`
- `docs/final_submission_validation_report.md`
- `docs/final_submission_changelog.md`

## Report Compilation Status

The final LaTeX report was compiled successfully with:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=report report/Research_Report.tex
```

Compilation status:

- PDF generated successfully at `report/Research_Report.pdf`.
- No undefined references or undefined citations were found in the final log scan.
- Remaining LaTeX typography warnings are minor underfull boxes plus one harmless 1.72443 pt overfull box on the title page.

## Presentation Generation Status

The final presentation was generated with:

```bash
.venv/bin/python scripts/generate_final_presentation.py
```

Presentation status:

- PowerPoint generated successfully at `report/IEDA4920_Final_Presentation.pptx`.
- The deck contains 28 slides after adding a fuller data-pipeline sequence from the research report.
- `unzip -t report/IEDA4920_Final_Presentation.pptx` returned no package errors.
- Slide XML was scanned for WIP markers; no matches remained.
- Quick Look generated a cover thumbnail at `data/tmp/final_deck_preview/IEDA4920_Final_Presentation.pptx.png`. Full multi-slide rendering was not available through the headless tooling without launching a presentation application, so the deck was also checked by PPTX package inspection and text extraction.

## Reference Deck Style Extraction

The additional style reference `report/IEDA4000E_Presentation_Deck_1126.pptx` was inspected with `python-pptx` and Quick Look thumbnail rendering. The deck contains 27 widescreen slides and uses:

- full-bleed finance imagery on the cover;
- Times New Roman typography;
- dark navy, muted gold, and occasional red accents;
- top-left title/subtitle hierarchy;
- objective/evidence/takeaway slide rhythm;
- figure-led layouts and concise explanatory text.

The final IEDA4920 deck was regenerated to follow that rhythm more closely. The old repeated navigation/footer treatment was replaced with cleaner section labels, assertion-style slide titles, evidence-led charts/tables, and a bottom takeaway line on most content slides. A dark cover background was generated from the current portfolio return series rather than borrowing unrelated imagery from the reference deck.

## Validation Commands Run

```bash
PYTHON=.venv/bin/python FYP_AS_OF_DATE=2026-05-03 bash scripts/run_pipeline.sh validate
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh github-check
.venv/bin/python -m compileall -q src scripts
git diff --check
unzip -t report/IEDA4920_Final_Presentation.pptx
```

Validation results:

- Pipeline validation: 35 passed, 7 warnings, 0 failed.
- GitHub readiness check: passed; 91 upload candidate files checked after repository cleanup.
- Python compile check: passed.
- Git whitespace check: passed.
- PPTX package check: passed.

The validation warnings are retained transparently:

- 4 missing financial feature values are expected to be imputed downstream using training-year medians only.
- The current review panel includes 2024 rows whose final archival target window closes on 2026-06-30.

## Claims Rewritten As Limitations Or Deferred Validation

The final report and deck no longer use unsupported claims as headline findings. The following items were reframed:

- unsupported taxonomy coverage percentages from the old conceptual figure;
- unsupported single-firm migration claims without generated case-study source tables;
- Fama-MacBeth coefficient and significance tables;
- DAV/EGARCH-X aggregate BIC improvement claims;
- SAR/network regression coefficients, p-values, and R-squared claims.

These topics are now described as conceptual diagnostics, methodology extensions, or deferred validation tasks when their source tables are absent from the output manifest.

## Verified Or Review-Accepted Headline Results

The final report and deck retain the verified/review-accepted results supported by current artifacts:

- Default Meso ST-GAT improves return MAE and return rank, but not averaged OOS RMSE.
- Full-window `theta040` Meso sensitivity improves averaged RMSE from 0.3523 to 0.3176 relative to its identity baseline.
- `theta040` volatility RMSE improves from 0.2082 to 0.1555 and volatility Spearman improves from -0.1906 to 0.1212.
- Paired Macro ST-GAT sensitivity runs are much denser but underperform identity baselines, supporting the report's Macro-versus-Meso resolution interpretation.
- 2024 taxonomy coverage is now backed by `outputs/taxonomy/sensitivity/taxonomy_macro_coverage_2024.csv`; `theta040` is more concentrated, with its largest Macro family covering 56.21% of assigned paragraphs.
- Default Meso graph is very sparse in the OOS period; `theta040` is denser and materially changes downstream behavior.
- Default Meso ST-GAT return-only long-short portfolio has Sharpe 0.88 and 7.31% annualized return.
- Default return-only top-minus-bottom spread is 16.26% annualized with conventional p=0.080 and HAC q=0.076.
- DAV peak-event diagnostics are mixed: 93 figures parsed, 20 positive, 73 negative, mean improvement -2.40%.

## Reviewer-Facing Notes

- The final package is suitable for review submission under the current exported dataset.
- Portfolio results should be interpreted as academic backtest evidence, not investment advice or live-trading deployability.
- Supplemental econometric modules are useful for future validation but are not headline evidence unless their source CSV outputs are regenerated and added to the manifest.
