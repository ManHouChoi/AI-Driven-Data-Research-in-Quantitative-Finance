# Report Figures

This directory stores report-local figures generated from verified local CSV
outputs. Refresh them from the repository root with:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh report-figures
```

The figure script intentionally reads existing output CSV files rather than
retraining models or recomputing portfolio results.
