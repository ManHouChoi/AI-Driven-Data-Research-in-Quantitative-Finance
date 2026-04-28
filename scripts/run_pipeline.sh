#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python}"
LOG_DIR="${FYP_LOG_DIR:-${ROOT_DIR}/logs}"
mkdir -p "${LOG_DIR}"

export FYP_PROJECT_ROOT="${FYP_PROJECT_ROOT:-${ROOT_DIR}}"
export PYTHONPATH="${ROOT_DIR}/src/gat:${ROOT_DIR}/src/data:${ROOT_DIR}/src/taxonomy:${ROOT_DIR}/src/portfolio:${ROOT_DIR}/src/econometrics:${ROOT_DIR}:${PYTHONPATH:-}"

# Canonical repository-local paths. Individual environment variables may still
# override these when a reviewer wants to run against another artifact set.
export FYP_RISK_HTML_DIR="${FYP_RISK_HTML_DIR:-${ROOT_DIR}/data/raw/risk_factors_output}"
export FYP_MASTER_RISK_CSV="${FYP_MASTER_RISK_CSV:-${ROOT_DIR}/data/interim/model_input/all_risk_factors_master.csv}"
export FYP_TAXONOMY_JSON="${FYP_TAXONOMY_JSON:-${ROOT_DIR}/data/interim/taxonomy/taxonomy_base.json}"
export FYP_TAXONOMY_CSV="${FYP_TAXONOMY_CSV:-${ROOT_DIR}/data/interim/taxonomy/hierarchical_risk_categories.csv}"
export FYP_CLASSIFICATION_OUTPUT_DIR="${FYP_CLASSIFICATION_OUTPUT_DIR:-${ROOT_DIR}/data/interim/processed/classification_outputs}"
export FYP_SCORING_OUTPUT_DIR="${FYP_SCORING_OUTPUT_DIR:-${ROOT_DIR}/data/interim/scoring_outputs}"
export FYP_RISK_SCORES_MACRO_CSV="${FYP_RISK_SCORES_MACRO_CSV:-${FYP_SCORING_OUTPUT_DIR}/risk_scores_macro_annual.csv}"
export FYP_RISK_SCORES_MESO_CSV="${FYP_RISK_SCORES_MESO_CSV:-${FYP_SCORING_OUTPUT_DIR}/risk_scores_meso_annual.csv}"
export FYP_FIN_MATRIX_CSV="${FYP_FIN_MATRIX_CSV:-${FYP_SCORING_OUTPUT_DIR}/fin_data_matrix.csv}"
export FYP_FIN_MATRIX_ENHANCED_CSV="${FYP_FIN_MATRIX_ENHANCED_CSV:-${FYP_SCORING_OUTPUT_DIR}/fin_data_matrix_enhanced.csv}"
export FYP_FIN_MATRIX_DROP_LOG_CSV="${FYP_FIN_MATRIX_DROP_LOG_CSV:-${FYP_SCORING_OUTPUT_DIR}/fin_data_matrix_enhanced_drop_log.csv}"
export FYP_GAT_MACRO_OUTPUT_DIR="${FYP_GAT_MACRO_OUTPUT_DIR:-${ROOT_DIR}/outputs/gat/GAT_output_macro}"
export FYP_GAT_MESO_OUTPUT_DIR="${FYP_GAT_MESO_OUTPUT_DIR:-${ROOT_DIR}/outputs/gat/GAT_output_meso}"
export FYP_GAT_MESO_PANEL_CSV="${FYP_GAT_MESO_PANEL_CSV:-${FYP_GAT_MESO_OUTPUT_DIR}/ST_GAT_vs_Baseline_Panel_meso.csv}"
export FYP_PORTFOLIO_OUTPUT_DIR="${FYP_PORTFOLIO_OUTPUT_DIR:-${ROOT_DIR}/outputs/portfolio/GAT_portfolio_output}"
export FYP_DAV_OUTPUT_DIR="${FYP_DAV_OUTPUT_DIR:-${ROOT_DIR}/outputs/econometrics/dav_benchmark_analysis}"
export FYP_FMB_OUTPUT_DIR="${FYP_FMB_OUTPUT_DIR:-${ROOT_DIR}/outputs/econometrics/fmb_benchmark_analysis}"
export FYP_NETWORK_OUTPUT_DIR="${FYP_NETWORK_OUTPUT_DIR:-${ROOT_DIR}/outputs/econometrics/network_evolution}"

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/run_pipeline.sh <stage>

Stages:
  validate          Run lightweight artifact and leakage/timing validation.
  github-check      Check Git upload candidates for size and secret hygiene.
  sec-download      Download/extract SEC Item 1A HTML using src/data/data_pipeline.py.
  master-csv        Build all_risk_factors_master.csv from extracted Item 1A HTML.
  taxonomy          Rebuild the base taxonomy JSON/CSV. Requires DEEPSEEK_API_KEY.
  classify          Classify risk paragraphs using the taxonomy centroids.
  risk-scoring      Aggregate classified paragraphs into macro/meso exposures.
  financial         Rebuild the enhanced financial feature/target matrix.
  gat-objective     Run Macro and Meso Optuna searches.
  gat-forecast      Run Macro and Meso ST-GAT forecasts with fixed best params.
  multi-seed        Run final ST-GAT forecasts across seeds into outputs/gat/multi_seed.
  portfolio         Run the monthly portfolio backtest from Meso ST-GAT signals.
  econometrics      Run Fama-MacBeth, DAV/EGARCH-X, and network diagnostics.
  dav-peak-summary  Summarize figure-only DAV peak diagnostics into CSV/Markdown.
  robust-eval       Run robust OOS and portfolio inference addenda.
  report-figures    Generate report-local figures from current CSV outputs.
  full              Run all stages above in research-pipeline order.

Useful environment variables:
  PYTHON=/path/to/python
  DRY_RUN=1
  FYP_AS_OF_DATE=2026-04-27
  SEC_CONTACT_EMAIL=your.name@example.com

Examples:
  bash scripts/run_pipeline.sh validate
  DRY_RUN=1 bash scripts/run_pipeline.sh full
  PYTHON=.venv/bin/python bash scripts/run_pipeline.sh gat-forecast
USAGE
}

run_cmd() {
  local name="$1"
  shift
  local timestamp
  timestamp="$(date +%Y%m%d_%H%M%S)"
  local log_file="${LOG_DIR}/${timestamp}_${name}.log"

  echo
  echo "==> ${name}"
  printf '    '
  printf '%q ' "$@"
  echo
  echo "    log: ${log_file}"

  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    return 0
  fi

  "$@" 2>&1 | tee "${log_file}"
}

run_python() {
  local name="$1"
  local script="$2"
  shift 2
  run_cmd "${name}" "${PYTHON_BIN}" "${ROOT_DIR}/${script}" "$@"
}

validate() {
  run_python "validate_pipeline" "scripts/validate_pipeline.py" --as-of "${FYP_AS_OF_DATE:-$(date +%Y-%m-%d)}"
}

github_check() {
  run_python "github_ready" "scripts/check_github_ready.py"
}

sec_download() {
  run_python "sec_download" "src/data/data_pipeline.py"
}

master_csv() {
  run_python "master_csv" "src/data/build_master_csv.py"
}

taxonomy() {
  run_python "taxonomy" "src/taxonomy/base_year_taxonomy.py"
}

classify() {
  run_python "classify" "src/taxonomy/classification.py"
}

risk_scoring() {
  run_python "risk_scoring" "src/taxonomy/risk_scoring.py"
}

financial() {
  run_python "financial_matrix" "src/data/generate_fin_data.py"
}

gat_objective() {
  run_python "gat_objective_macro" "src/gat/GAT_objective_macro.py"
  run_python "gat_objective_meso" "src/gat/GAT_objective_meso.py"
}

gat_forecast() {
  run_python "gat_forecast_macro" "src/gat/GAT_forecast_macro.py"
  run_python "gat_forecast_meso" "src/gat/GAT_forecast_meso.py"
}

multi_seed() {
  run_python "multi_seed_forecasts" "scripts/run_multi_seed_forecasts.py" ${FYP_MULTI_SEED_ARGS:-}
}

portfolio() {
  run_python "portfolio_backtest" "src/portfolio/portfolio_backtest.py"
}

econometrics() {
  run_python "fama_macbeth" "src/econometrics/fmb_risk_premium.py"
  run_python "dav_egarch_x" "src/econometrics/volatility_model.py"
  run_python "network_evolution" "src/econometrics/network_evolution_analysis.py"
}

dav_peak_summary() {
  run_python "dav_peak_summary" "scripts/summarize_dav_peak_analysis.py"
}

robust_eval() {
  run_python "robust_oos_evaluation" "scripts/evaluate_oos_robustness.py"
  run_python "portfolio_inference" "scripts/evaluate_portfolio_inference.py"
}

report_figures() {
  run_python "report_figures" "scripts/generate_report_figures.py"
}

full() {
  sec_download
  master_csv
  taxonomy
  classify
  risk_scoring
  financial
  gat_objective
  gat_forecast
  portfolio
  econometrics
  dav_peak_summary
  robust_eval
  report_figures
  validate
}

stage="${1:-help}"
case "${stage}" in
  help|--help|-h)
    usage
    ;;
  validate)
    validate
    ;;
  github-check)
    github_check
    ;;
  sec-download)
    sec_download
    ;;
  master-csv)
    master_csv
    ;;
  taxonomy)
    taxonomy
    ;;
  classify)
    classify
    ;;
  risk-scoring)
    risk_scoring
    ;;
  financial)
    financial
    ;;
  gat-objective)
    gat_objective
    ;;
  gat-forecast)
    gat_forecast
    ;;
  multi-seed)
    multi_seed
    ;;
  portfolio)
    portfolio
    ;;
  econometrics)
    econometrics
    ;;
  dav-peak-summary)
    dav_peak_summary
    ;;
  robust-eval)
    robust_eval
    ;;
  report-figures)
    report_figures
    ;;
  full)
    full
    ;;
  *)
    echo "Unknown stage: ${stage}" >&2
    usage >&2
    exit 2
    ;;
esac
