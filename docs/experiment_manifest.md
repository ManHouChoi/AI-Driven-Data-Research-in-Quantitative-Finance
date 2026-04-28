# Experiment Manifest

This manifest records the intended experiment design and reproducibility knobs.
It does not replace the scripts or output files; it is a reviewer-facing map.

## Core Research Identity

- SEC Item 1A risk disclosures are converted into macro and meso textual risk
  exposure vectors.
- Firm-year risk vectors form semantic peer graphs through cosine similarity.
- The main ST-GAT specification is topology-only: graph topology is used, while
  edge weights are retained for diagnostics and optional ablations.
- The identity baseline uses only self-loops, representing `A_t = I`.
- The full graph uses explicit self-loops plus risk-similarity edges,
  representing `A_t = I + A_risk,t`.

## Chronological Split

| Split | Years |
|---|---|
| Train | 2006-2016 |
| Validation | 2017-2020 |
| Test/OOS | 2021-2024 |

Validation warning:

- Risk year 2024 has a forward target window ending on 2026-06-30. Before that
  date, realized 2024 target claims should be caveated or excluded from strict
  OOS realized-performance claims.

## Feature and Target Timing

For risk year `t`:

- Node features use July 1 `t` through June 30 `t+1`.
- Forward return and volatility targets use July 1 `t+1` through June 30 `t+2`.
- Portfolio signals from forecast year `t` apply over July `t+1` through June
  `t+2`, with monthly rebalancing and next-month return realization.

## Randomness and Determinism

| Component | Current Setting |
|---|---|
| Base seed | 42 |
| Optuna sampler | TPE sampler with fixed seed in objective scripts |
| Torch deterministic flags | Enabled in GAT scripts |
| Validation smoke test | Python, NumPy, and Torch RNG repeat under seed 42 |
| Robust OOS addendum | Year-block bootstrap and annual-block paired error comparison in `scripts/evaluate_oos_robustness.py` |
| Portfolio inference addendum | HAC/Newey-West tests and Benjamini-Hochberg q-values in `scripts/evaluate_portfolio_inference.py` |
| Seed-stability addendum | Final forecast reruns across seeds in `scripts/run_multi_seed_forecasts.py`; canonical outputs are not overwritten |

## Canonical Commands

Validate current artifacts:

```bash
.venv/bin/python scripts/validate_pipeline.py --as-of 2026-04-27
```

Dry-run the full pipeline order:

```bash
DRY_RUN=1 PYTHON=.venv/bin/python bash scripts/run_pipeline.sh full
```

Run a specific stage:

```bash
PYTHON=.venv/bin/python bash scripts/run_pipeline.sh gat-forecast
```

## Configuration

The canonical local configuration lives at:

```text
configs/default.yaml
```

The runner exports environment variables from the current repository layout so
that legacy scripts expecting `FYP_*` variables can run without manual edits.
