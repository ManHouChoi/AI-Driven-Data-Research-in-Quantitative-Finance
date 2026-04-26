#!/usr/bin/env bash
set -euo pipefail

# IEDA4920 FYP reproducible pipeline runner
# Run from the repository root:
#   bash scripts/run_pipeline.sh

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "[ERROR] Neither python3 nor python was found on PATH."
  echo "Create/activate a virtual environment first, for example:"
  echo "  python3 -m venv .venv"
  echo "  source .venv/bin/activate"
  echo "  python3 -m pip install -r requirements.txt"
  exit 1
fi

log_step() {
  echo
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

run_if_exists() {
  local script_path="$1"
  local description="$2"

  if [[ -f "$script_path" ]]; then
    log_step "$description"
    "$PYTHON_BIN" "$script_path"
  else
    echo "[SKIP] $script_path not found"
  fi
}

log_step "Starting IEDA4920 FYP pipeline"
echo "Project root: $PROJECT_ROOT"
echo "Python: $($PYTHON_BIN -c 'import sys; print(sys.executable)')"
echo "Python version: $($PYTHON_BIN --version)"

# -------------------------------------------------------------------
# 1. Data extraction and financial feature construction
# -------------------------------------------------------------------
run_if_exists "src/data/build_master_csv.py" "Step 1A: Build master risk-disclosure CSV"
run_if_exists "src/data/generate_fin_data.py" "Step 1B: Generate financial feature data"
run_if_exists "src/data/build_enhanced_macro_data.py" "Step 1C: Build enhanced macro-financial data"

# -------------------------------------------------------------------
# 2. Taxonomy construction, classification, and risk scoring
# -------------------------------------------------------------------
run_if_exists "src/taxonomy/base_year_taxonomy.py" "Step 2A: Build base-year taxonomy"
run_if_exists "src/taxonomy/classification.py" "Step 2B: Classify risk paragraphs"
run_if_exists "src/taxonomy/risk_scoring.py" "Step 2C: Generate firm-year risk scores"

# -------------------------------------------------------------------
# 3. ST-GAT optimization and forecasting
# -------------------------------------------------------------------
run_if_exists "src/gat/GAT_objective_macro.py" "Step 3A: Optimize Macro ST-GAT"
run_if_exists "src/gat/GAT_objective_meso.py" "Step 3B: Optimize Meso ST-GAT"
run_if_exists "src/gat/GAT_forecast_macro.py" "Step 3C: Forecast with Macro ST-GAT"
run_if_exists "src/gat/GAT_forecast_meso.py" "Step 3D: Forecast with Meso ST-GAT"

# -------------------------------------------------------------------
# 4. Econometric validation
# -------------------------------------------------------------------
run_if_exists "src/econometrics/fmb_risk_premium.py" "Step 4A: Run Fama-MacBeth risk-premium validation"
run_if_exists "src/econometrics/st_gcn_volatility.py" "Step 4B: Run volatility validation model"
run_if_exists "src/econometrics/network_evolution_analysis.py" "Step 4C: Run risk-contagion network analysis"
run_if_exists "src/econometrics/plot_fmb.py" "Step 4D: Plot Fama-MacBeth outputs"

# -------------------------------------------------------------------
# 5. Portfolio backtesting
# -------------------------------------------------------------------
if [[ -d "src/portfolio" ]]; then
  portfolio_script="$(find src/portfolio -maxdepth 1 -type f -name '*.py' | sort | head -n 1 || true)"
  if [[ -n "$portfolio_script" ]]; then
    run_if_exists "$portfolio_script" "Step 5: Run portfolio backtest"
  else
    echo "[SKIP] No Python portfolio backtest script found under src/portfolio"
  fi
else
  echo "[SKIP] src/portfolio directory not found"
fi

log_step "Pipeline finished"
