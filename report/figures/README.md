# Report Figures

This directory stores report-local figures generated from verified local CSV
outputs. Refresh them from the repository root with:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh report-figures
```

The figure script intentionally reads existing output CSV files rather than
retraining models or recomputing portfolio results.

`portfolio_backtest_comparison.png` preserves the current exported portfolio
equity-curve comparison used in the final presentation/report materials. When
the full ignored portfolio output folder is available locally, the same plot can
be regenerated from `outputs/portfolio/GAT_portfolio_output/portfolio_equity_curves.png`
or by rerunning the portfolio pipeline.
