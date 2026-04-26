#!/usr/bin/env bash
set -euo pipefail

# IEDA4920 FYP reproducible pipeline runner
# Run from the repository root:
#   bash scripts/run_pipeline.sh --smoke
#   bash scripts/run_pipeline.sh --full

MODE="${1:---smoke}"

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

check_file() {
  local path="$1"
  local description="$2"

  if [[ -f "$path" ]]; then
    echo "[OK] $description: $path"
  else
    echo "[MISSING] $description: $path"
  fi
}

check_dir() {
  local path="$1"
  local description="$2"

  if [[ -d "$path" ]]; then
    echo "[OK] $description: $path"
  else
    echo "[MISSING] $description: $path"
  fi
}

run_smoke() {
  log_step "Smoke check: repository structure"
  echo "Project root: $PROJECT_ROOT"
  echo "Python: $($PYTHON_BIN -c 'import sys; print(sys.executable)')"
  echo "Python version: $($PYTHON_BIN --version)"

  check_dir "src/data" "data source folder"
  check_dir "src/taxonomy" "taxonomy source folder"
  check_dir "src/gat" "ST-GAT source folder"
  check_dir "src/econometrics" "econometrics source folder"
  check_dir "src/portfolio" "portfolio source folder"
  check_dir "data/processed" "processed data folder"
  check_dir "outputs" "outputs folder"
  check_dir "report" "report folder"

  check_file "src/data/build_master_csv.py" "master CSV builder"
  check_file "src/data/generate_fin_data.py" "financial data generator"
  check_file "src/data/build_enhanced_macro_data.py" "enhanced macro data builder"
  check_file "src/taxonomy/base_year_taxonomy.py" "base taxonomy builder"
  check_file "src/taxonomy/classification.py" "semantic classifier"
  check_file "src/taxonomy/risk_scoring.py" "risk scoring script"
  check_file "src/gat/GAT_data_pipeline.py" "GAT data pipeline"
  check_file "src/gat/GAT_models.py" "GAT models"
  check_file "src/gat/GAT_objective_macro.py" "macro GAT objective"
  check_file "src/gat/GAT_objective_meso.py" "meso GAT objective"
  check_file "src/gat/GAT_forecast_macro.py" "macro GAT forecast"
  check_file "src/gat/GAT_forecast_meso.py" "meso GAT forecast"
  check_file "src/econometrics/fmb_risk_premium.py" "Fama-MacBeth validation"
  check_file "src/econometrics/st_gcn_volatility.py" "volatility validation"
  check_file "src/econometrics/network_evolution_analysis.py" "network evolution analysis"
  check_file "src/portfolio/portfolio_backtest.py" "portfolio backtest"

  log_step "Smoke check: Python syntax"
  "$PYTHON_BIN" -m compileall -q src
  echo "[OK] Python files compiled successfully."

  log_step "Smoke check finished"
  echo "Use 'bash scripts/run_pipeline.sh --full' only after required data files are available."
}

run_full() {
  log_step "Starting full IEDA4920 FYP pipeline"
  echo "Project root: $PROJECT_ROOT"
  echo "Python: $($PYTHON_BIN -c 'import sys; print(sys.executable)')"
  echo "Python version: $($PYTHON_BIN --version)"

  run_if_exists "src/data/build_master_csv.py" "Step 1A: Build master risk-disclosure CSV"
  run_if_exists "src/data/generate_fin_data.py" "Step 1B: Generate financial feature data"
  run_if_exists "src/data/build_enhanced_macro_data.py" "Step 1C: Build enhanced macro-financial data"

  run_if_exists "src/taxonomy/base_year_taxonomy.py" "Step 2A: Build base-year taxonomy"
  run_if_exists "src/taxonomy/classification.py" "Step 2B: Classify risk paragraphs"
  run_if_exists "src/taxonomy/risk_scoring.py" "Step 2C: Generate firm-year risk scores"

  run_if_exists "src/gat/GAT_objective_macro.py" "Step 3A: Optimize Macro ST-GAT"
  run_if_exists "src/gat/GAT_objective_meso.py" "Step 3B: Optimize Meso ST-GAT"
  run_if_exists "src/gat/GAT_forecast_macro.py" "Step 3C: Forecast with Macro ST-GAT"
  run_if_exists "src/gat/GAT_forecast_meso.py" "Step 3D: Forecast with Meso ST-GAT"

  run_if_exists "src/econometrics/fmb_risk_premium.py" "Step 4A: Run Fama-MacBeth risk-premium validation"
  run_if_exists "src/econometrics/st_gcn_volatility.py" "Step 4B: Run volatility validation model"
  run_if_exists "src/econometrics/network_evolution_analysis.py" "Step 4C: Run risk-contagion network analysis"
  run_if_exists "src/econometrics/plot_fmb.py" "Step 4D: Plot Fama-MacBeth outputs"

  run_if_exists "src/portfolio/portfolio_backtest.py" "Step 5: Run portfolio backtest"

  log_step "Full pipeline finished"
}

case "$MODE" in
  --smoke)
    run_smoke
    ;;
  --full)
    run_full
    ;;
  *)
    echo "Usage: bash scripts/run_pipeline.sh [--smoke|--full]"
    exit 1
    ;;
esac