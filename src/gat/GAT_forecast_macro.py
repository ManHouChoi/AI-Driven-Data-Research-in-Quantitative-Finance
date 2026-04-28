# GAT_forecast_macro.py
import os
import random
import copy
import warnings
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error

from GAT_data_pipeline import FinancialGraphBuilder
from GAT_models import ST_GAT_Forecaster

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


CONFIG = {
    "level": "macro",
    "output_dir": os.getenv(
        "FYP_GAT_MACRO_OUTPUT_DIR",
        os.path.join(PROJECT_ROOT, "outputs", "gat", "GAT_output_macro"),
    ),
    "best_params_path": os.getenv(
        "FYP_GAT_MACRO_PARAMS_JSON",
        os.path.join(
            os.getenv("FYP_GAT_MACRO_OUTPUT_DIR", os.path.join(PROJECT_ROOT, "outputs", "gat", "GAT_output_macro")),
            "optuna_best_params_macro.json",
        ),
    ),
    "tau": 0.8127797829415244,
    "heads": 1,
    "dropout": 0.36878822920584453,
    "lr": 0.006694123858161636,
    "spatial_dim": 16,
    "max_epochs": env_int("FYP_GAT_MAX_EPOCHS", 300),
    "patience": env_int("FYP_GAT_PATIENCE", 40),
    "min_delta": 1e-6,
    "weight_decay": 1.9762569165678324e-05,
    "grad_clip": 1.0,
    "seed": env_int("FYP_GAT_SEED", 42),
    "train_end_year": env_int("FYP_TRAIN_END_YEAR", 2016),
    "val_end_year": env_int("FYP_VALIDATION_END_YEAR", 2020),
    "use_edge_attr": False,
    "edge_weight_mode": "cosine",
    "include_self_loops": True,
    "self_loop_weight": 1.0,
}


def load_best_params_if_available() -> None:
    """Keep forecast settings synchronized with the latest Optuna output."""
    params_path = CONFIG["best_params_path"]
    if not os.path.exists(params_path):
        print(f"Best-parameter file not found; using CONFIG defaults: {params_path}")
        return

    try:
        with open(params_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        best_params = payload.get("best_params", {})
    except Exception as exc:
        print(f"Warning: could not read {params_path}; using CONFIG defaults. Error: {exc}")
        return

    for key in ("tau", "heads", "dropout", "lr", "spatial_dim", "weight_decay"):
        if key in best_params:
            CONFIG[key] = best_params[key]
    print(f"Loaded Macro Optuna best parameters from {params_path}.")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def masked_huber_loss(
    preds: torch.Tensor,
    targets: torch.Tensor,
    active_masks: torch.Tensor,
    year_indices: list[int],
    delta: float = 1.0,
) -> torch.Tensor:
    total_loss = preds.new_tensor(0.0)
    valid_years = 0

    for t in year_indices:
        active_nodes = active_masks[t]
        if active_nodes.any():
            total_loss = total_loss + F.huber_loss(
                preds[active_nodes, t, :],
                targets[active_nodes, t, :],
                delta=delta,
            )
            valid_years += 1

    if valid_years == 0:
        raise ValueError("No active firm-years found for the requested split.")

    return total_loss / valid_years


def safe_spearman(actual: pd.Series, pred: pd.Series) -> float:
    if actual.nunique(dropna=True) <= 1 or pred.nunique(dropna=True) <= 1:
        return np.nan
    corr, _ = spearmanr(actual, pred)
    return float(corr)


def build_model(in_features: int) -> ST_GAT_Forecaster:
    return ST_GAT_Forecaster(
        in_features=in_features,
        spatial_dim=CONFIG["spatial_dim"],
        out_dim=2,
        heads=CONFIG["heads"],
        dropout=CONFIG["dropout"],
        positive_volatility=False,
        use_edge_attr=CONFIG["use_edge_attr"],
    )


def train_and_extract(risk_csv_path: str, fin_csv_path: str):
    set_seed(CONFIG["seed"])
    level = CONFIG["level"]
    output_dir = CONFIG["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    load_best_params_if_available()

    print(f"Initializing {level.upper()} ST-GAT forecasting pipeline...")
    risk_df = pd.read_csv(risk_csv_path)
    fin_df = pd.read_csv(fin_csv_path)

    builder = FinancialGraphBuilder(
        risk_df,
        fin_df,
        train_year_end=CONFIG["train_end_year"],
        standardize_features=True,
        impute_active_missing=True,
        edge_weight_mode=CONFIG["edge_weight_mode"],
        include_self_loops=CONFIG["include_self_loops"],
        self_loop_weight=CONFIG["self_loop_weight"],
    )
    snapshots, active_masks = builder.build_signal(tau=CONFIG["tau"])
    graph_diagnostics = builder.compute_graph_diagnostics(tau=CONFIG["tau"])
    graph_diagnostics.to_csv(
        os.path.join(output_dir, f"graph_diagnostics_{level}_forecast_tau.csv"),
        index=False,
    )
    snapshots_baseline, active_masks_baseline = builder.build_identity_signal()

    if not torch.equal(active_masks, active_masks_baseline):
        raise ValueError("Full-graph and identity-baseline active masks do not match.")

    targets = torch.stack([s.y for s in snapshots], dim=1)
    tickers = builder.tickers
    years = builder.years
    in_features = builder.in_features

    train_indices = [t for t, year in enumerate(years) if year <= CONFIG["train_end_year"]]
    val_indices = [t for t, year in enumerate(years) if CONFIG["train_end_year"] < year <= CONFIG["val_end_year"]]
    test_indices = [t for t, year in enumerate(years) if year > CONFIG["val_end_year"]]

    if not train_indices or not val_indices or not test_indices:
        raise ValueError(
            f"Invalid chronological split. Train={train_indices}, Val={val_indices}, Test={test_indices}"
        )

    print(f"Graph/data summary: {builder.describe()}")

    features_used = builder.feature_cols
    with open(os.path.join(output_dir, f"{level}_features_list.txt"), "w") as f:
        f.write(f"{level.upper()} ST-GAT node features used as inputs:\n")
        f.write("-" * 60 + "\n")
        for feat in features_used:
            f.write(f"- {feat}\n")

    fin_df[["Ticker", "Year"] + features_used].to_csv(
        os.path.join(output_dir, f"{level}_data_demonstration.csv"),
        index=False,
    )

    gat_model = build_model(in_features)
    base_model = build_model(in_features)

    opt_gat = torch.optim.Adam(
        gat_model.parameters(),
        lr=CONFIG["lr"],
        weight_decay=CONFIG["weight_decay"],
    )
    opt_base = torch.optim.Adam(
        base_model.parameters(),
        lr=CONFIG["lr"],
        weight_decay=CONFIG["weight_decay"],
    )

    best_gat_state = copy.deepcopy(gat_model.state_dict())
    best_base_state = copy.deepcopy(base_model.state_dict())
    best_gat_val = float("inf")
    best_base_val = float("inf")
    stale_epochs = 0

    history = {
        "epoch": [],
        "gat_train_loss": [],
        "base_train_loss": [],
        "gat_val_loss": [],
        "base_val_loss": [],
    }

    print("Training full ST-GAT and identity baseline with validation early stopping...")
    for epoch in range(CONFIG["max_epochs"]):
        gat_model.train()
        base_model.train()
        opt_gat.zero_grad()
        opt_base.zero_grad()

        preds_gat = gat_model(snapshots)
        preds_base = base_model(snapshots_baseline)

        loss_gat = masked_huber_loss(preds_gat, targets, active_masks, train_indices)
        loss_base = masked_huber_loss(preds_base, targets, active_masks, train_indices)

        loss_gat.backward()
        loss_base.backward()
        torch.nn.utils.clip_grad_norm_(gat_model.parameters(), max_norm=CONFIG["grad_clip"])
        torch.nn.utils.clip_grad_norm_(base_model.parameters(), max_norm=CONFIG["grad_clip"])
        opt_gat.step()
        opt_base.step()

        gat_model.eval()
        base_model.eval()
        with torch.no_grad():
            val_preds_gat = gat_model(snapshots)
            val_preds_base = base_model(snapshots_baseline)
            val_loss_gat = masked_huber_loss(val_preds_gat, targets, active_masks, val_indices)
            val_loss_base = masked_huber_loss(val_preds_base, targets, active_masks, val_indices)

        history["epoch"].append(epoch + 1)
        history["gat_train_loss"].append(loss_gat.item())
        history["base_train_loss"].append(loss_base.item())
        history["gat_val_loss"].append(val_loss_gat.item())
        history["base_val_loss"].append(val_loss_base.item())

        improved = False
        if val_loss_gat.item() < best_gat_val - CONFIG["min_delta"]:
            best_gat_val = val_loss_gat.item()
            best_gat_state = copy.deepcopy(gat_model.state_dict())
            improved = True

        if val_loss_base.item() < best_base_val - CONFIG["min_delta"]:
            best_base_val = val_loss_base.item()
            best_base_state = copy.deepcopy(base_model.state_dict())
            improved = True

        stale_epochs = 0 if improved else stale_epochs + 1
        if stale_epochs >= CONFIG["patience"]:
            print(f"Early stopping at epoch {epoch + 1}.")
            break

    gat_model.load_state_dict(best_gat_state)
    base_model.load_state_dict(best_base_state)

    history_df = pd.DataFrame(history)
    history_df.to_csv(os.path.join(output_dir, f"training_convergence_{level}.csv"), index=False)

    plt.figure(figsize=(10, 6))
    plt.plot(history_df["epoch"], history_df["gat_train_loss"], label="ST-GAT Train Loss", linewidth=2)
    plt.plot(history_df["epoch"], history_df["base_train_loss"], label="Identity Baseline Train Loss", linewidth=2)
    plt.plot(history_df["epoch"], history_df["gat_val_loss"], label="ST-GAT Validation Loss", linestyle="--", linewidth=2)
    plt.plot(history_df["epoch"], history_df["base_val_loss"], label="Identity Baseline Validation Loss", linestyle="--", linewidth=2)
    plt.title(f"Neural Network Convergence ({level.upper()})", fontsize=14, fontweight="bold")
    plt.xlabel("Epoch", fontsize=12)
    plt.ylabel("Huber Loss", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"loss_convergence_curve_{level}.png"), dpi=300)
    plt.close()

    print("Extracting panel predictions across all regimes...")
    gat_model.eval()
    base_model.eval()

    all_records = []
    with torch.no_grad():
        final_preds_gat = gat_model(snapshots).detach().cpu().numpy()
        final_preds_base = base_model(snapshots_baseline).detach().cpu().numpy()
        targets_np = targets.detach().cpu().numpy()

        for t, year in enumerate(years):
            if t in train_indices:
                dataset_label = "Train"
            elif t in val_indices:
                dataset_label = "Validation"
            else:
                dataset_label = "Test (OOS)"

            active_idx = np.where(active_masks[t].cpu().numpy())[0]
            for i in active_idx:
                all_records.append({
                    "Ticker": tickers[i],
                    "Year": year,
                    "Dataset": dataset_label,
                    "Actual_Ret": targets_np[i, t, 0],
                    "Actual_Vol": targets_np[i, t, 1],
                    "GAT_Pred_Ret": final_preds_gat[i, t, 0],
                    "GAT_Pred_Vol": final_preds_gat[i, t, 1],
                    "Base_Pred_Ret": final_preds_base[i, t, 0],
                    "Base_Pred_Vol": final_preds_base[i, t, 1],
                })

    results_df = pd.DataFrame(all_records)
    results_df.to_csv(os.path.join(output_dir, f"ST_GAT_vs_Baseline_Panel_{level}.csv"), index=False)

    print("Calculating out-of-sample goodness-of-fit metrics...")
    df_clean = results_df[results_df["Dataset"] == "Test (OOS)"].copy()
    if df_clean.empty:
        raise ValueError("No OOS test rows available for metric calculation.")

    metrics = []
    for target in ["Ret", "Vol"]:
        actual = df_clean[f"Actual_{target}"]
        gat_pred = df_clean[f"GAT_Pred_{target}"]
        base_pred = df_clean[f"Base_Pred_{target}"]

        metrics.append({
            "Target": target,
            "Model": "ST-GAT",
            "RMSE": np.sqrt(mean_squared_error(actual, gat_pred)),
            "MAE": mean_absolute_error(actual, gat_pred),
            "Spearman_Rank": safe_spearman(actual, gat_pred),
        })
        metrics.append({
            "Target": target,
            "Model": "Identity Baseline",
            "RMSE": np.sqrt(mean_squared_error(actual, base_pred)),
            "MAE": mean_absolute_error(actual, base_pred),
            "Spearman_Rank": safe_spearman(actual, base_pred),
        })

    metrics_df = pd.DataFrame(metrics)
    avg_metrics = metrics_df.groupby("Model", as_index=False)[["RMSE", "MAE", "Spearman_Rank"]].mean()
    avg_metrics["Target"] = "Averaged (Ret & Vol)"
    final_metrics_df = pd.concat([metrics_df, avg_metrics], ignore_index=True)
    final_metrics_df = final_metrics_df[["Target", "Model", "RMSE", "MAE", "Spearman_Rank"]]
    final_metrics_df.to_csv(os.path.join(output_dir, f"goodness_of_fit_metrics_{level}_OOS.csv"), index=False)
    final_metrics_df.to_csv(os.path.join(output_dir, f"goodness_of_fit_metrics_{level}.csv"), index=False)

    print("\n" + "=" * 60)
    print(f"Run complete. Best validation losses: ST-GAT={best_gat_val:.6f}, Identity={best_base_val:.6f}")
    print(f"All outputs saved in '{output_dir}'.")
    print("=" * 60)


if __name__ == "__main__":
    MACRO_CSV = os.getenv(
        "FYP_RISK_SCORES_MACRO_CSV",
        os.path.join(PROJECT_ROOT, "data", "interim", "scoring_outputs", "risk_scores_macro_annual.csv"),
    )
    FIN_CSV = os.getenv(
        "FYP_FIN_MATRIX_ENHANCED_CSV",
        os.path.join(PROJECT_ROOT, "data", "interim", "scoring_outputs", "fin_data_matrix_enhanced.csv"),
    )

    train_and_extract(MACRO_CSV, FIN_CSV)
