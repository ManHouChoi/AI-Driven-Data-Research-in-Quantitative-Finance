# GAT_models.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from typing import List
from GAT_data_pipeline import GraphSnapshot


class ST_GAT_Forecaster(nn.Module):
    """Spatio-Temporal Graph Attention forecaster.

    Expected input is a list of annual GraphSnapshot objects. For each year t:
        snapshot.x          has shape [N, F]
        snapshot.edge_index has shape [2, E]
        snapshot.edge_attr  has shape [E], containing cosine-similarity weights

    By default, the model uses risk similarity to define graph topology only.
    Set `use_edge_attr=True` to feed cosine-similarity weights into GATConv.

    Forward output shape:
        [N, T, out_dim]

    By construction, self-loops are expected to be supplied by the data pipeline.
    Therefore `add_self_loops=False` is used to make the adjacency matrix explicit:
        full model:     A = I + A_risk
        identity model: A = I
    """

    def __init__(
        self,
        in_features: int,
        spatial_dim: int = 32,
        out_dim: int = 2,
        heads: int = 4,
        dropout: float = 0.20,
        temporal_channels: int = 64,
        temporal_kernel_size: int = 2,
        positive_volatility: bool = False,
        use_edge_attr: bool = False,
    ):
        super().__init__()
        if temporal_kernel_size < 1:
            raise ValueError("temporal_kernel_size must be >= 1.")

        self.out_dim = out_dim
        self.positive_volatility = positive_volatility
        self.use_edge_attr = use_edge_attr
        self.temporal_kernel_size = temporal_kernel_size
        self.spatial_out_dim = spatial_dim * heads

        self.gat = GATConv(
            in_channels=in_features,
            out_channels=spatial_dim,
            heads=heads,
            dropout=dropout,
            concat=True,
            edge_dim=1 if use_edge_attr else None,
            add_self_loops=False,
        )
        self.spatial_norm = nn.LayerNorm(self.spatial_out_dim)
        self.activation = nn.ELU()
        self.dropout = nn.Dropout(dropout)

        self.tcn = nn.Conv1d(
            in_channels=self.spatial_out_dim,
            out_channels=temporal_channels,
            kernel_size=temporal_kernel_size,
            padding=temporal_kernel_size - 1,
        )
        self.temporal_norm = nn.LayerNorm(temporal_channels)
        self.regressor = nn.Linear(temporal_channels, out_dim)

    def forward(self, snapshots: List[GraphSnapshot]) -> torch.Tensor:
        if not snapshots:
            raise ValueError("ST_GAT_Forecaster.forward received an empty snapshot list.")

        spatial_embeddings = []
        for snapshot in snapshots:
            if self.use_edge_attr:
                edge_attr = snapshot.edge_attr
                if edge_attr is not None and edge_attr.dim() == 1:
                    edge_attr = edge_attr.view(-1, 1)
                h = self.gat(snapshot.x, snapshot.edge_index, edge_attr)
            else:
                h = self.gat(snapshot.x, snapshot.edge_index)
            h = self.spatial_norm(h)
            h = self.activation(h)
            h = self.dropout(h)
            spatial_embeddings.append(h)

        # H: [N, C_spatial, T]
        H = torch.stack(spatial_embeddings, dim=2)

        # Causal temporal convolution. Padding creates extra future positions at
        # the end; trimming back to T preserves the original sequence length.
        H_tcn = self.tcn(H)
        H_tcn = H_tcn[:, :, :H.size(2)]
        H_tcn = self.activation(H_tcn)

        # [N, T, C_temporal]
        H_tcn = H_tcn.permute(0, 2, 1)
        H_tcn = self.temporal_norm(H_tcn)
        H_tcn = self.dropout(H_tcn)

        out = self.regressor(H_tcn)

        if self.positive_volatility and self.out_dim >= 2:
            # Preserve unconstrained return prediction, force volatility prediction positive.
            ret = out[..., :1]
            vol = F.softplus(out[..., 1:2])
            if self.out_dim > 2:
                out = torch.cat([ret, vol, out[..., 2:]], dim=-1)
            else:
                out = torch.cat([ret, vol], dim=-1)

        return out