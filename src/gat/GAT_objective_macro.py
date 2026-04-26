# GAT_objective_macro.py
import copy
import json
import os
import random
import warnings

import matplotlib.pyplot as plt
import numpy as np
import optuna
import optuna.visualization.matplotlib as ovm
import pandas as pd
import torch
import torch.nn.functional as F

from GAT_data_pipeline import FinancialGraphBuilder
from GAT_models import ST_GAT_Forecaster

warnings.filterwarnings("ignore")


CONFIG = {
    "level": "macro",
    "risk_csv": os.getenv(
        "FYP_RISK_SCORES_MACRO_CSV",
        os.path.join(os.getenv("FYP_PROJECT_ROOT", os.getcwd()), "data", "processed", "risk_scores_macro_annual.csv"),
    ),
    "fin_csv": os.getenv(
        "FYP_FIN_MATRIX_ENHANCED_CSV",
        os.path.join(os.getenv("FYP_PROJECT_ROOT", os.getcwd()), "data", "processed", "fin_data_matrix_enhanced.csv"),
    ),
    "output_dir": os.getenv(
        "FYP_GAT_MACRO_OUTPUT_DIR",
        os.path.join(os.getenv("FYP_PROJECT_ROOT", os.getcwd()), "outputs", "gat", "macro"),
    ),
    "n_trials": 50,
    "max_epochs": 200,
    "patience": 25,
    "min_delta": 1e-6,
    "grad_clip": 1.0,
    "base_seed": 42,
    "train_end_year": 2016,
    "val_end_year": 2020,
    "use_edge_attr": False,
    "edge_weight_mode": "cosine",
    "include_self_loops": True,
    "self_loop_weight": 1.0,
}


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


def build_model(
    in_features: int,
    spatial_dim: int,
    heads: int,
    dropout: float,
) -> ST_GAT_Forecaster:
    return ST_GAT_Forecaster(
        in_features=in_features,
        spatial_dim=spatial_dim,
        out_dim=2,
        heads=heads,
        dropout=dropout,
        positive_volatility=False,
        use_edge_attr=CONFIG["use_edge_attr"],
    )


def objective(trial: optuna.Trial, risk_df: pd.DataFrame, fin_df: pd.DataFrame) -> float:
    set_seed(CONFIG["base_seed"] + trial.number)

    tau = trial.suggest_float("tau", 0.75, 0.95)
    heads = trial.suggest_categorical("heads", [1, 2, 4, 8])
    spatial_dim = trial.suggest_categorical("spatial_dim", [8, 16, 32])
    dropout = trial.suggest_float("dropout", 0.10, 0.50)
    lr = trial.suggest_float("lr", 1e-4, 1e-2, log=True)
    weight_decay = trial.suggest_float("weight_decay", 1e-6, 1e-3, log=True)

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
    snapshots, active_masks = builder.build_signal(tau=tau)
    if trial.number == 0:
        diagnostics = builder.compute_graph_diagnostics(tau=tau)
        diagnostics_dir = CONFIG["output_dir"]
        os.makedirs(diagnostics_dir, exist_ok=True)
        diagnostics.to_csv(
            os.path.join(diagnostics_dir, "graph_diagnostics_macro_initial_trial.csv"),
            index=False,
        )
    targets = torch.stack([s.y for s in snapshots], dim=1)
    years = builder.years

    train_indices = [t for t, year in enumerate(years) if year <= CONFIG["train_end_year"]]
    val_indices = [
        t for t, year in enumerate(years)
        if CONFIG["train_end_year"] < year <= CONFIG["val_end_year"]
    ]

    if not train_indices or not val_indices:
        raise ValueError(f"Invalid chronological split. Train={train_indices}, Val={val_indices}")

    model = build_model(
        in_features=builder.in_features,
        spatial_dim=spatial_dim,
        heads=heads,
        dropout=dropout,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    best_val_loss = float("inf")
    best_state = copy.deepcopy(model.state_dict())
    stale_epochs = 0

    history = {
        "epoch": [],
        "train_loss": [],
        "val_loss": [],
    }

    for epoch in range(CONFIG["max_epochs"]):
        model.train()
        optimizer.zero_grad()

        preds = model(snapshots)
        train_loss = masked_huber_loss(preds, targets, active_masks, train_indices)
        train_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=CONFIG["grad_clip"])
        optimizer.step()

        model.eval()
        with torch.no_grad():
            val_preds = model(snapshots)
            val_loss = masked_huber_loss(val_preds, targets, active_masks, val_indices)

        train_loss_value = float(train_loss.item())
        val_loss_value = float(val_loss.item())
        history["epoch"].append(epoch + 1)
        history["train_loss"].append(train_loss_value)
        history["val_loss"].append(val_loss_value)

        trial.report(val_loss_value, step=epoch)
        if trial.should_prune():
            raise optuna.TrialPruned()

        if val_loss_value < best_val_loss - CONFIG["min_delta"]:
            best_val_loss = val_loss_value
            best_state = copy.deepcopy(model.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1

        if stale_epochs >= CONFIG["patience"]:
            break

    model.load_state_dict(best_state)

    trial.set_user_attr("best_val_loss", best_val_loss)
    trial.set_user_attr("epochs_ran", len(history["epoch"]))
    trial.set_user_attr("num_features", builder.in_features)
    trial.set_user_attr("num_nodes", builder.num_nodes)
    trial.set_user_attr("num_years", len(builder.years))

    if trial.number % 10 == 0:
        trial_dir = os.path.join(CONFIG["output_dir"], "optuna_trial_curves")
        os.makedirs(trial_dir, exist_ok=True)
        plt.figure(figsize=(8, 5))
        plt.plot(history["epoch"], history["train_loss"], label="Train Huber Loss", linewidth=2)
        plt.plot(history["epoch"], history["val_loss"], label="Validation Huber Loss", linewidth=2)
        plt.title(f"Macro Optuna Trial {trial.number}: Loss Convergence")
        plt.xlabel("Epoch")
        plt.ylabel("Huber Loss")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(trial_dir, f"trial_{trial.number:03d}_loss.png"), dpi=300)
        plt.close()

    return best_val_loss


def main() -> None:
    output_dir = CONFIG["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    print("Loading macro datasets...")
    if not os.path.exists(CONFIG["risk_csv"]):
        raise FileNotFoundError(
            f"Macro risk score file not found: {CONFIG['risk_csv']}. "
            "Set FYP_RISK_SCORES_MACRO_CSV or place the file under data/processed/."
        )
    if not os.path.exists(CONFIG["fin_csv"]):
        raise FileNotFoundError(
            f"Enhanced financial matrix not found: {CONFIG['fin_csv']}. "
            "Set FYP_FIN_MATRIX_ENHANCED_CSV or place the file under data/processed/."
        )
    risk_df = pd.read_csv(CONFIG["risk_csv"])
    fin_df = pd.read_csv(CONFIG["fin_csv"])

    precheck_builder = FinancialGraphBuilder(
        risk_df,
        fin_df,
        train_year_end=CONFIG["train_end_year"],
        standardize_features=True,
        impute_active_missing=True,
        edge_weight_mode=CONFIG["edge_weight_mode"],
        include_self_loops=CONFIG["include_self_loops"],
        self_loop_weight=CONFIG["self_loop_weight"],
    )
    precheck_diag = precheck_builder.compute_graph_diagnostics(tau=0.85)
    precheck_diag.to_csv(
        os.path.join(output_dir, "graph_diagnostics_macro_tau_085_precheck.csv"),
        index=False,
    )

    print("Starting Macro Optuna hyperparameter optimization...")
    sampler = optuna.samplers.TPESampler(seed=CONFIG["base_seed"])
    pruner = optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=25)
    study = optuna.create_study(
        direction="minimize",
        study_name="ST_GAT_Macro_Optimization",
        sampler=sampler,
        pruner=pruner,
    )

    study.optimize(lambda trial: objective(trial, risk_df, fin_df), n_trials=CONFIG["n_trials"])

    print("\nOptimization finished.")
    print("Best validation loss:", study.best_value)
    print("Best hyperparameters:", study.best_params)

    best_payload = {
        "best_value": study.best_value,
        "best_params": study.best_params,
        "config": CONFIG,
    }

    with open(os.path.join(output_dir, "optuna_best_params_macro.json"), "w") as f:
        json.dump(best_payload, f, indent=4)

    with open(os.path.join(output_dir, "optuna_best_params_macro.txt"), "w") as f:
        f.write("Best Hyperparameters from Macro Optuna Optimization\n")
        f.write("-" * 60 + "\n")
        f.write(f"Best validation Huber loss: {study.best_value}\n")
        for key, value in study.best_params.items():
            f.write(f"{key}: {value}\n")

    trials_df = study.trials_dataframe()
    trials_df.to_csv(os.path.join(output_dir, "optuna_trials_history_macro.csv"), index=False)

    try:
        ovm.plot_optimization_history(study)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "optuna_optimization_history_macro.png"), dpi=300)
        plt.close()

        ovm.plot_param_importances(study)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "optuna_param_importances_macro.png"), dpi=300)
        plt.close()
    except Exception as exc:
        print(f"Warning: Could not generate Optuna plots. Error: {exc}")

    print("\n" + "=" * 60)
    print(f"Macro Optuna phase complete. Outputs saved in '{output_dir}'.")
    print("=" * 60)


if __name__ == "__main__":
    main()