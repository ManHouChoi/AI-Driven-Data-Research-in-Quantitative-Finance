# GAT_data_pipeline.py
import numpy as np
import pandas as pd
import torch
from scipy.spatial.distance import pdist, squareform
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict

@dataclass
class GraphSnapshot:
    """A single temporal snapshot of the market graph.

    x:          [N, F] node feature matrix.
    edge_index: [2, E] weighted, directed sparse edge list. For an undirected graph,
                both (i, j) and (j, i) are included.
    edge_attr:  [E] edge weights. By default these preserve cosine-similarity
                values for diagnostics and optional weighted-edge experiments.
                The main topology-only ST-GAT can ignore this field.
    y:          [N, 2] forward targets: [Target_Ret, Target_Vol].
    """
    x: torch.Tensor
    edge_index: torch.Tensor
    edge_attr: torch.Tensor
    y: torch.Tensor

class FinancialGraphBuilder:
    """Build annual ST-GAT graph snapshots from risk exposures and financial features.

    The risk-score columns are assumed to be normalized exposure weights, i.e.
    category paragraphs / total risk paragraphs for each firm-year. These columns
    define the dynamic risk-similarity graph topology through cosine similarity.

    By default, cosine similarity is used to decide which off-diagonal edges exist.
    The ST-GAT model can either ignore edge_attr and use topology only, or consume
    edge_attr in a weighted-edge ablation.

    The financial columns define node features. Target_Ret and Target_Vol are
    assumed to be one-period-ahead labels already constructed upstream.
    """

    IDENTIFIER_COLS = {"Year", "Ticker"}
    TARGET_COLS = ["Target_Ret", "Target_Vol"]

    def __init__(
        self,
        risk_df: pd.DataFrame,
        fin_df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None,
        risk_cols: Optional[List[str]] = None,
        train_year_end: Optional[int] = 2016,
        standardize_features: bool = True,
        impute_active_missing: bool = True,
        edge_weight_mode: str = "cosine",
        include_self_loops: bool = True,
        self_loop_weight: float = 1.0,
    ):
        self.risk_df = risk_df.copy()
        self.fin_df = fin_df.copy()
        self.train_year_end = train_year_end
        self.standardize_features = standardize_features
        self.impute_active_missing = impute_active_missing
        self.edge_weight_mode = edge_weight_mode
        self.include_self_loops = include_self_loops
        self.self_loop_weight = float(self_loop_weight)

        if self.edge_weight_mode not in {"cosine", "binary"}:
            raise ValueError("edge_weight_mode must be either 'cosine' or 'binary'.")
        if self.self_loop_weight <= 0:
            raise ValueError("self_loop_weight must be positive.")

        self._validate_required_columns()

        self.tickers = sorted(list(set(self.risk_df["Ticker"]).union(set(self.fin_df["Ticker"]))))
        self.num_nodes = len(self.tickers)
        self.years = sorted(list(set(self.risk_df["Year"]).intersection(set(self.fin_df["Year"]))))

        if not self.years:
            raise ValueError("No overlapping years between risk_df and fin_df.")

        self.feature_cols = feature_cols or [
            c for c in self.fin_df.columns
            if c not in self.IDENTIFIER_COLS and c not in self.TARGET_COLS
        ]
        self.risk_cols = risk_cols or [
            c for c in self.risk_df.select_dtypes(include=[np.number]).columns
            if c not in self.IDENTIFIER_COLS
        ]

        if not self.feature_cols:
            raise ValueError("No financial feature columns detected. Pass feature_cols explicitly.")
        if not self.risk_cols:
            raise ValueError("No numeric risk-score columns detected. Pass risk_cols explicitly.")

        missing_features = [c for c in self.feature_cols if c not in self.fin_df.columns]
        missing_risks = [c for c in self.risk_cols if c not in self.risk_df.columns]
        if missing_features:
            raise ValueError(f"feature_cols not found in fin_df: {missing_features}")
        if missing_risks:
            raise ValueError(f"risk_cols not found in risk_df: {missing_risks}")

        self.in_features = len(self.feature_cols)
        self.feature_means_: Optional[pd.Series] = None
        self.feature_stds_: Optional[pd.Series] = None
        self.feature_medians_: Optional[pd.Series] = None

        self._fit_feature_preprocessor()

    def _validate_required_columns(self) -> None:
        for name, df in {"risk_df": self.risk_df, "fin_df": self.fin_df}.items():
            missing = [c for c in ["Year", "Ticker"] if c not in df.columns]
            if missing:
                raise ValueError(f"{name} is missing required columns: {missing}")

        missing_targets = [c for c in self.TARGET_COLS if c not in self.fin_df.columns]
        if missing_targets:
            raise ValueError(f"fin_df is missing required target columns: {missing_targets}")

    def _fit_feature_preprocessor(self) -> None:
        train_df = self.fin_df[self.fin_df["Year"] <= self.train_year_end] if self.train_year_end is not None else self.fin_df
        if train_df.empty:
            raise ValueError("Training dataframe for preprocessing is empty. Check train_year_end and Year values.")

        train_features = (
            train_df[self.feature_cols]
            .apply(pd.to_numeric, errors="coerce")
            .replace([np.inf, -np.inf], np.nan)
        )
        self.feature_medians_ = train_features.median(axis=0).fillna(0.0)

        if self.standardize_features:
            self.feature_means_ = train_features.mean(axis=0).fillna(0.0)
            std = train_features.std(axis=0, ddof=0).replace(0.0, 1.0).fillna(1.0)
            self.feature_stds_ = std

    def _prepare_features(self, f_idx: pd.DataFrame, active_mask: np.ndarray) -> np.ndarray:
        features_df = (
            f_idx[self.feature_cols]
            .apply(pd.to_numeric, errors="coerce")
            .replace([np.inf, -np.inf], np.nan)
        )

        if self.impute_active_missing:
            features_df = features_df.fillna(self.feature_medians_)
        else:
            complete_feature_rows = features_df.notna().all(axis=1).values
            active_mask &= complete_feature_rows
            features_df = features_df.fillna(0.0)

        if self.standardize_features:
            features_df = (features_df - self.feature_means_) / self.feature_stds_

        return features_df.fillna(0.0).values.astype(np.float32)

    def _prepare_risk_matrix(self, r_idx: pd.DataFrame) -> pd.DataFrame:
        """Return numeric, finite risk exposures aligned to the global ticker universe."""
        return (
            r_idx.reindex(self.tickers)[self.risk_cols]
            .apply(pd.to_numeric, errors="coerce")
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0.0)
        )

    def _risk_active_mask(self, r_idx: pd.DataFrame, risk_matrix: pd.DataFrame) -> np.ndarray:
        """Identify firm-years with an observed, non-empty risk exposure vector."""
        has_risk_row = r_idx.index.to_series().reindex(self.tickers).notna().values
        has_positive_exposure = risk_matrix.sum(axis=1).values > 0.0
        return has_risk_row & has_positive_exposure

    def _target_active_mask(self, f_idx: pd.DataFrame) -> np.ndarray:
        """Identify firm-years with finite forward return and volatility targets."""
        targets_df = (
            f_idx[self.TARGET_COLS]
            .apply(pd.to_numeric, errors="coerce")
            .replace([np.inf, -np.inf], np.nan)
        )
        return targets_df.notna().all(axis=1).values

    def _build_weighted_edges(self, risk_matrix: pd.DataFrame, tau: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Build sparse graph edges from risk-vector cosine similarity.

        The off-diagonal topology is always thresholded by cosine similarity.
        edge_weight_mode controls only the edge_attr values:
            - "cosine": preserve cosine similarities as edge_attr.
            - "binary": use 1.0 for every retained edge.

        The main topology-only ST-GAT sets use_edge_attr=False in GAT_models.py,
        so edge_attr is ignored by the model but remains useful for diagnostics.
        """
        dist_matrix = pdist(risk_matrix.values, metric="cosine")
        dist_matrix = np.nan_to_num(dist_matrix, nan=1.0, posinf=1.0, neginf=1.0)
        sim_matrix = 1.0 - squareform(dist_matrix)
        sim_matrix = np.clip(sim_matrix, 0.0, 1.0)
        np.fill_diagonal(sim_matrix, 0.0)

        adj_matrix = np.where(sim_matrix >= tau, sim_matrix, 0.0)
        row, col = np.where(adj_matrix > 0.0)

        if self.edge_weight_mode == "cosine":
            edge_weight = adj_matrix[row, col].astype(np.float32)
        else:
            edge_weight = np.ones(len(row), dtype=np.float32)

        if self.include_self_loops:
            # Explicit self-loops make the full graph A = I + A_risk. The model uses
            # add_self_loops=False, so this pipeline fully controls the ablation.
            self_row = np.arange(self.num_nodes, dtype=np.int64)
            self_col = np.arange(self.num_nodes, dtype=np.int64)
            self_weight = np.full(self.num_nodes, self.self_loop_weight, dtype=np.float32)

            row = np.concatenate([self_row, row.astype(np.int64)])
            col = np.concatenate([self_col, col.astype(np.int64)])
            edge_weight = np.concatenate([self_weight, edge_weight])
        else:
            row = row.astype(np.int64)
            col = col.astype(np.int64)

        return row, col, edge_weight

    def compute_graph_diagnostics(self, tau: float) -> pd.DataFrame:
        """Return annual graph-density diagnostics for a given similarity threshold.

        This is useful before expensive Optuna runs because a too-dense graph can
        force the GAT to aggregate noise, while a too-sparse graph may remove the
        intended risk-spillover signal.
        """
        if not 0.0 <= tau <= 1.0:
            raise ValueError(f"tau must be in [0, 1], got {tau}.")

        records = []
        for y in self.years:
            r_y = self.risk_df[self.risk_df["Year"] == y].copy()
            r_idx = r_y.set_index("Ticker")
            risk_matrix = self._prepare_risk_matrix(r_idx)

            dist_matrix = pdist(risk_matrix.values, metric="cosine")
            dist_matrix = np.nan_to_num(dist_matrix, nan=1.0, posinf=1.0, neginf=1.0)
            sim_matrix = 1.0 - squareform(dist_matrix)
            sim_matrix = np.clip(sim_matrix, 0.0, 1.0)
            np.fill_diagonal(sim_matrix, 0.0)

            off_diag_edges = sim_matrix >= tau
            edge_weights = sim_matrix[off_diag_edges]
            num_off_diag_edges = int(off_diag_edges.sum())
            active_risk_nodes = int((risk_matrix.sum(axis=1).values > 0.0).sum())
            possible_directed_edges = max(active_risk_nodes * (active_risk_nodes - 1), 1)
            avg_out_degree = num_off_diag_edges / max(self.num_nodes, 1)
            density_active = num_off_diag_edges / possible_directed_edges

            records.append({
                "Year": y,
                "Num_Nodes_Global": self.num_nodes,
                "Num_Active_Risk_Nodes": active_risk_nodes,
                "Num_OffDiagonal_Edges": num_off_diag_edges,
                "Avg_Out_Degree_Global": avg_out_degree,
                "Density_Among_Active_Risk_Nodes": density_active,
                "Mean_Edge_Weight": float(np.mean(edge_weights)) if len(edge_weights) else np.nan,
                "Median_Edge_Weight": float(np.median(edge_weights)) if len(edge_weights) else np.nan,
                "Min_Edge_Weight": float(np.min(edge_weights)) if len(edge_weights) else np.nan,
                "Max_Edge_Weight": float(np.max(edge_weights)) if len(edge_weights) else np.nan,
            })

        return pd.DataFrame(records)

    def build_signal(self, tau: float) -> Tuple[List[GraphSnapshot], torch.Tensor]:
        if not 0.0 <= tau <= 1.0:
            raise ValueError(f"tau must be in [0, 1], got {tau}.")

        snapshots: List[GraphSnapshot] = []
        masks_list: List[np.ndarray] = []

        for y in self.years:
            r_y = self.risk_df[self.risk_df["Year"] == y].copy()
            f_y = self.fin_df[self.fin_df["Year"] == y].copy()

            r_idx = r_y.set_index("Ticker")
            f_idx_raw = f_y.set_index("Ticker")

            # Target-aware active universe: a node is trainable/evaluable only if it has
            # non-empty current risk exposure, current financial features, and finite
            # forward return/volatility labels.
            f_idx = f_idx_raw.reindex(self.tickers)
            risk_matrix = self._prepare_risk_matrix(r_idx)

            has_risk = self._risk_active_mask(r_idx, risk_matrix)
            has_fin = f_idx_raw.index.to_series().reindex(self.tickers).notna().values
            has_target = self._target_active_mask(f_idx)
            active_mask = has_risk & has_fin & has_target

            features = self._prepare_features(f_idx, active_mask)

            targets_df = (
                f_idx[self.TARGET_COLS]
                .apply(pd.to_numeric, errors="coerce")
                .replace([np.inf, -np.inf], np.nan)
                .fillna(0.0)
            )
            targets = targets_df.values.astype(np.float32)

            row, col, edge_weight = self._build_weighted_edges(risk_matrix, tau)

            snapshot = GraphSnapshot(
                x=torch.tensor(features, dtype=torch.float),
                edge_index=torch.tensor(np.vstack((row, col)), dtype=torch.long),
                edge_attr=torch.tensor(edge_weight, dtype=torch.float),
                y=torch.tensor(targets, dtype=torch.float),
            )

            snapshots.append(snapshot)
            masks_list.append(active_mask.copy())

        active_masks_tensor = torch.tensor(np.stack(masks_list), dtype=torch.bool)
        return snapshots, active_masks_tensor

    def build_identity_signal(self) -> Tuple[List[GraphSnapshot], torch.Tensor]:
        """Build a diagonal/self-loop baseline using the same features and targets.

        This baseline tests whether each equity's own financial features alone can
        predict future return/volatility, without textual peer spillover.
        """
        snapshots: List[GraphSnapshot] = []
        masks_list: List[np.ndarray] = []
        row = np.arange(self.num_nodes, dtype=np.int64)
        col = np.arange(self.num_nodes, dtype=np.int64)
        edge_weight = np.ones(self.num_nodes, dtype=np.float32)

        for y in self.years:
            r_y = self.risk_df[self.risk_df["Year"] == y].copy()
            f_y = self.fin_df[self.fin_df["Year"] == y].copy()

            r_idx = r_y.set_index("Ticker")
            f_idx_raw = f_y.set_index("Ticker")
            f_idx = f_idx_raw.reindex(self.tickers)

            risk_matrix = self._prepare_risk_matrix(r_idx)
            has_risk = self._risk_active_mask(r_idx, risk_matrix)
            has_fin = f_idx_raw.index.to_series().reindex(self.tickers).notna().values
            has_target = self._target_active_mask(f_idx)
            active_mask = has_risk & has_fin & has_target

            features = self._prepare_features(f_idx, active_mask)
            targets_df = (
                f_idx[self.TARGET_COLS]
                .apply(pd.to_numeric, errors="coerce")
                .replace([np.inf, -np.inf], np.nan)
                .fillna(0.0)
            )
            targets = targets_df.values.astype(np.float32)

            snapshot = GraphSnapshot(
                x=torch.tensor(features, dtype=torch.float),
                edge_index=torch.tensor(np.vstack((row, col)), dtype=torch.long),
                edge_attr=torch.tensor(edge_weight, dtype=torch.float),
                y=torch.tensor(targets, dtype=torch.float),
            )

            snapshots.append(snapshot)
            masks_list.append(active_mask.copy())

        active_masks_tensor = torch.tensor(np.stack(masks_list), dtype=torch.bool)
        return snapshots, active_masks_tensor

    def describe(self) -> Dict[str, object]:
        return {
            "num_nodes": self.num_nodes,
            "num_years": len(self.years),
            "years": self.years,
            "num_features": self.in_features,
            "feature_cols": self.feature_cols,
            "num_risk_cols": len(self.risk_cols),
            "standardize_features": self.standardize_features,
            "train_year_end": self.train_year_end,
            "edge_weight_mode": self.edge_weight_mode,
            "include_self_loops": self.include_self_loops,
            "self_loop_weight": self.self_loop_weight,
            "active_mask_requires_positive_risk_exposure": True,
            "finite_target_required": True,
        }