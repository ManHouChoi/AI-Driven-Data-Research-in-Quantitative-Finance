import os
import warnings
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
import yfinance as yf
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Tuple, List

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))

# ==========================================
# 1. REAL MARKET DATA ENGINE
# ==========================================
class RealMarketDataEngine:
    """Fetches high-frequency pricing and ensures temporal continuity."""
    
    def __init__(self, tickers: List[str], start_date: str = "2023-01-01", end_date: str = "2024-01-01"):
        self.raw_tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.valid_tickers = []
        self.tensor_data = None

    def fetch_and_process(self) -> Tuple[np.ndarray, List[str]]:
        print(f"Fetching market data for {len(self.raw_tickers)} equities...")
        df = yf.download(self.raw_tickers, start=self.start_date, end=self.end_date, progress=False)
        
        px_col = 'Adj Close' if 'Adj Close' in df.columns.levels[0] else 'Close'
        px = df[px_col].copy()
        
        if hasattr(px.index, 'tz') and px.index.tz is not None:
            px.index = px.index.tz_localize(None)
            
        px = px.dropna(axis=1, thresh=int(len(px) * 0.95))
        px = px.ffill().bfill()
        
        self.valid_tickers = px.columns.tolist()
        
        returns = np.log(px / px.shift(1)).fillna(0)
        rolling_vol = returns.rolling(window=5).std().fillna(0)
        
        num_nodes = len(self.valid_tickers)
        num_days = len(returns)
        num_features = 2
        
        data_matrix = np.zeros((num_nodes, num_days, num_features), dtype=np.float32)
        
        for i, ticker in enumerate(self.valid_tickers):
            data_matrix[i, :, 0] = returns[ticker].values
            data_matrix[i, :, 1] = rolling_vol[ticker].values
            
        self.tensor_data = data_matrix
        print(f"Market data processed. Surviving universe: {num_nodes} equities over {num_days} trading days.")
        return data_matrix, self.valid_tickers

# ==========================================
# 2. ALIGNED GRAPH CONSTRUCTION
# ==========================================
class AlignedRiskGraphBuilder:
    """Constructs the spatial Adjacency Matrix strictly on valid pricing nodes."""
    
    def __init__(self, risk_df: pd.DataFrame, valid_tickers: List[str], target_year: int = 2022, top_k: int = 3):
        self.risk_df = risk_df
        self.valid_tickers = valid_tickers
        self.target_year = target_year
        self.top_k = top_k

    def build_graph(self) -> Tuple[torch.Tensor, torch.Tensor]:
        df_year = self.risk_df[self.risk_df['Year'] == self.target_year].copy()
        df_year = df_year.set_index('Ticker')
        
        intersected_df = df_year.loc[df_year.index.intersection(self.valid_tickers)]
        intersected_df = intersected_df.reindex(self.valid_tickers).fillna(0)
        risk_features = intersected_df.select_dtypes(include=[np.number]).drop(columns=['Year'], errors='ignore')
        
        X = np.log1p(risk_features.values)
        X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-8)
        
        similarity_matrix = cosine_similarity(X)
        
        edge_indices = []
        edge_weights = []
        num_nodes = similarity_matrix.shape[0]
        
        for i in range(num_nodes):
            top_k_idx = np.argsort(similarity_matrix[i])[-self.top_k:]
            for j in top_k_idx:
                if similarity_matrix[i, j] > 0:
                    edge_indices.append([i, j])
                    edge_weights.append(similarity_matrix[i, j])
                    
        edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        edge_weight = torch.tensor(edge_weights, dtype=torch.float32)
        
        print(f"Graph aligned: {num_nodes} nodes, {edge_index.shape[1]} structural risk edges.")
        return edge_index, edge_weight

# ==========================================
# 3. SEQUENCE GENERATION & SPLITTING
# ==========================================
def create_sequences(data: np.ndarray, seq_len: int = 21, horizon: int = 5) -> Tuple[torch.Tensor, torch.Tensor]:
    num_nodes, num_days, num_features = data.shape
    X, Y = [], []
    
    for t in range(num_days - seq_len - horizon):
        x_seq = data[:, t : t + seq_len, :]
        y_target = np.std(data[:, t + seq_len : t + seq_len + horizon, 0], axis=1) * np.sqrt(252)
        X.append(x_seq)
        Y.append(y_target)
        
    return torch.tensor(np.array(X), dtype=torch.float32), torch.tensor(np.array(Y), dtype=torch.float32)

# ==========================================
# 4. NEURAL ARCHITECTURE (ST-GCN)
# ==========================================
class ST_GCN_VolatilityModel(nn.Module):
    def __init__(self, num_node_features: int, lstm_hidden_dim: int, gcn_hidden_dim: int):
        super(ST_GCN_VolatilityModel, self).__init__()
        self.lstm = nn.LSTM(input_size=num_node_features, hidden_size=lstm_hidden_dim, batch_first=True)
        self.dropout = nn.Dropout(p=0.2)
        self.gcn = GCNConv(in_channels=lstm_hidden_dim, out_channels=gcn_hidden_dim)
        self.linear = nn.Linear(gcn_hidden_dim, 1)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_weight: torch.Tensor) -> torch.Tensor:
        _, (h_n, _) = self.lstm(x)
        h_n = h_n.squeeze(0)
        h_n = self.dropout(h_n)
        
        z = self.gcn(h_n, edge_index, edge_weight)
        z = F.relu(z)
        
        out = self.linear(z).squeeze(-1)
        return F.softplus(out)

    def get_node_embeddings(self, x: torch.Tensor, edge_index: torch.Tensor, edge_weight: torch.Tensor) -> np.ndarray:
        """Executes a forward pass strictly to extract the hidden GCN node embeddings."""
        self.eval() 
        with torch.no_grad():
            _, (h_n, _) = self.lstm(x)
            h_n = h_n.squeeze(0)
            z = self.gcn(h_n, edge_index, edge_weight)
            z = F.relu(z)
        return z.numpy()

# ==========================================
# 5. EXECUTION & EVALUATION LOOP
# ==========================================
def train_and_evaluate(model: nn.Module, X: torch.Tensor, Y: torch.Tensor, edge_index: torch.Tensor, edge_weight: torch.Tensor, epochs: int = 40):
    num_samples = X.shape[0]
    train_size = int(num_samples * 0.8) 
    
    X_train, Y_train = X[:train_size], Y[:train_size]
    X_test, Y_test = X[train_size:], Y[train_size:]
    
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=1e-4)
    criterion = nn.MSELoss()
    
    print(f"\nTraining on {train_size} temporal sequences. Testing on {num_samples - train_size} out-of-sample sequences.")
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        
        for i in range(train_size):
            optimizer.zero_grad()
            pred_vol = model(X_train[i], edge_index, edge_weight)
            loss = criterion(pred_vol, Y_train[i])
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        if (epoch + 1) % 10 == 0:
            model.eval()
            test_loss = 0.0
            with torch.no_grad():
                for j in range(len(X_test)):
                    pred_vol = model(X_test[j], edge_index, edge_weight)
                    loss = criterion(pred_vol, Y_test[j])
                    test_loss += loss.item()
            print(f"Epoch {epoch+1:03d} | Train MSE: {train_loss/train_size:.6f} | Test MSE (Out-of-Sample): {test_loss/len(X_test):.6f}")

# ==========================================
# 6. VISUALIZATION ENGINE
# ==========================================
# ==========================================
# 6. VISUALIZATION ENGINE
# ==========================================
def visualize_risk_clusters(model: nn.Module, X_tensor: torch.Tensor, edge_index: torch.Tensor, edge_weight: torch.Tensor, valid_tickers: list):
    """Extracts high-dimensional GCN embeddings and plots the market topology."""
    print("\nExtracting GCN Node Embeddings for final state visualization...")
    
    latest_sequence = X_tensor[-1] 
    embeddings = model.get_node_embeddings(latest_sequence, edge_index, edge_weight)
    
    print("Applying t-SNE Dimensionality Reduction...")
    # FIXED: Removed the 'n_iter' argument to resolve scikit-learn versioning conflicts
    tsne = TSNE(n_components=2, perplexity=min(15, len(valid_tickers)-1), random_state=42)
    embeddings_2d = tsne.fit_transform(embeddings)
    
    print("Applying K-Means to identify latent risk neighborhoods...")
    kmeans = KMeans(n_clusters=4, random_state=42)
    cluster_labels = kmeans.fit_predict(embeddings)
    
    plot_df = pd.DataFrame({
        'Ticker': valid_tickers,
        'Dim_1': embeddings_2d[:, 0],
        'Dim_2': embeddings_2d[:, 1],
        'Latent_Cluster': [f"Risk Neighborhood {c+1}" for c in cluster_labels]
    })
    
    plt.figure(figsize=(14, 10))
    sns.set_theme(style="whitegrid")
    
    sns.scatterplot(
        data=plot_df, 
        x='Dim_1', 
        y='Dim_2', 
        hue='Latent_Cluster', 
        palette='viridis', 
        s=100, 
        edgecolor='black', 
        alpha=0.8
    )
    
    for i in range(len(plot_df)):
        plt.annotate(
            plot_df['Ticker'].iloc[i], 
            (plot_df['Dim_1'].iloc[i], plot_df['Dim_2'].iloc[i]),
            xytext=(5, 5), 
            textcoords='offset points',
            fontsize=8,
            alpha=0.7
        )
        
    plt.title("ST-GCN Latent Space: Textual Risk Clusters & Volatility Topology", fontsize=16, fontweight='bold')
    plt.xlabel("t-SNE Dimension 1", fontsize=12)
    plt.ylabel("t-SNE Dimension 2", fontsize=12)
    plt.legend(title="Network Topology", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    output_dir = os.getenv(
        "FYP_ST_GCN_OUTPUT_DIR",
        os.path.join(PROJECT_ROOT, "outputs", "econometrics", "st_gcn_volatility"),
    )
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, "st_gcn_risk_clusters.png")
    plt.savefig(output_filename, dpi=300)
    print(f"Visualization saved to {output_filename}")
    
# ==========================================
# 7. MAIN ORCHESTRATOR
# ==========================================
def run_empirical_pipeline(risk_csv_path: str):
    print("Initializing Empirical Deep Learning Pipeline...")
    if not os.path.exists(risk_csv_path):
        print(f"Target file missing: {risk_csv_path}")
        return
        
    risk_df = pd.read_csv(risk_csv_path)
    base_tickers = risk_df['Ticker'].unique().tolist()
    
    data_engine = RealMarketDataEngine(base_tickers, start_date="2023-01-01", end_date="2024-01-01")
    raw_tensor, valid_tickers = data_engine.fetch_and_process()
    
    graph_builder = AlignedRiskGraphBuilder(risk_df, valid_tickers, target_year=2022, top_k=3)
    edge_index, edge_weight = graph_builder.build_graph()
    
    X_tensor, Y_tensor = create_sequences(raw_tensor, seq_len=21, horizon=5)
    
    model = ST_GCN_VolatilityModel(num_node_features=2, lstm_hidden_dim=32, gcn_hidden_dim=16)
    train_and_evaluate(model, X_tensor, Y_tensor, edge_index, edge_weight, epochs=50)
    
    # Execute visualization after training completes
    visualize_risk_clusters(model, X_tensor, edge_index, edge_weight, valid_tickers)

if __name__ == "__main__":
    MACRO_CSV = os.getenv(
        "FYP_RISK_SCORES_MACRO_CSV",
        os.path.join(PROJECT_ROOT, "data", "interim", "scoring_outputs", "risk_scores_macro_annual.csv"),
    )
    run_empirical_pipeline(MACRO_CSV)
