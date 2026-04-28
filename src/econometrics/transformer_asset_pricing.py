import math
import warnings
from pathlib import Path
from typing import Tuple, List, Dict

import numpy as np
import pandas as pd
import yfinance as yf
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score
import optuna
import transformer_plot

warnings.filterwarnings("ignore")
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ==========================================
# 1. REAL MARKET DATA & TARGET GENERATION
# ==========================================
class MarketDataTargetEngine:
    """
    Fetches real pricing data, aligns temporal windows to prevent look-ahead bias,
    and calculates binary Crash Risk and Latent Factors (F_{t+1}).
    """
    def __init__(self, tickers: List[str], start_date: str = "2020-01-01", end_date: str = "2025-12-31"):
        # Append S&P 500 for market latent factor calculation
        self.tickers = list(set(tickers + ['^GSPC']))
        self.start_date = start_date
        self.end_date = end_date
        self.price_data = pd.DataFrame()

    def fetch_data(self):
        print(f"Fetching market data for {len(self.tickers)} equities + Market Index...")
        df = yf.download(self.tickers, start=self.start_date, end=self.end_date, progress=False)

        px_col = 'Adj Close' if 'Adj Close' in df.columns.levels[0] else 'Close'
        self.price_data = df[px_col].copy()

        if hasattr(self.price_data.index, 'tz') and self.price_data.index.tz is not None:
            self.price_data.index = self.price_data.index.tz_localize(None)

        self.price_data = self.price_data.ffill().bfill()

    def generate_targets_and_factors(self, risk_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merges NLP risk scores with forward Crash Risk (y_{t+1}) and Factors (F_{t+1}).
        Crash Risk is defined as a forward return <= -15%.
        """
        records = []
        cohort_years = sorted(risk_df['Year'].unique().tolist())

        for year in cohort_years:
            # Strict Fama-French Alignment
            mom_start = pd.Timestamp(year=year, month=7, day=1)
            formation_date = pd.Timestamp(year=year + 1, month=6, day=30)
            fwd_start = pd.Timestamp(year=year + 1, month=7, day=1)
            fwd_end = pd.Timestamp(year=year + 2, month=6, day=30)

            for ticker in risk_df[risk_df['Year'] == year]['Ticker']:
                if ticker not in self.price_data.columns or '^GSPC' not in self.price_data.columns:
                    continue

                series = self.price_data[ticker].dropna()
                mkt_series = self.price_data['^GSPC'].dropna()

                try:
                    # Target: Forward 1-Year Return
                    p_fwd_start = series.loc[fwd_start:fwd_end].iloc[0]
                    p_fwd_end = series.loc[fwd_start:fwd_end].iloc[-1]
                    fwd_return = (p_fwd_end - p_fwd_start) / p_fwd_start

                    # Latent Factor 1: Market Forward Return
                    mkt_start = mkt_series.loc[fwd_start:fwd_end].iloc[0]
                    mkt_end = mkt_series.loc[fwd_start:fwd_end].iloc[-1]
                    mkt_fwd_ret = (mkt_end - mkt_start) / mkt_start

                    # Latent Factor 2: Historical Momentum
                    p_mom_start = series.loc[mom_start:formation_date].iloc[0]
                    p_mom_end = series.loc[mom_start:formation_date].iloc[-1]
                    momentum = (p_mom_end - p_mom_start) / p_mom_start

                    # Latent Factor 3: Historical Volatility
                    hist_series = series.loc[mom_start:formation_date]
                    hist_vol = (np.log(hist_series / hist_series.shift(1)).dropna()).std() * np.sqrt(252)

                    # Define Binary Crash Risk (1 if forward return <= -15%)
                    crash_risk = 1 if fwd_return <= -0.15 else 0

                    records.append({
                        'Ticker': ticker,
                        'Year': year,
                        'Crash_Risk': crash_risk,
                        'Factor_Mkt_Ret': mkt_fwd_ret,
                        'Factor_Momentum': momentum,
                        'Factor_Hist_Vol': hist_vol
                    })
                except Exception:
                    continue # Skip if insufficient temporal overlap exists

        target_df = pd.DataFrame(records)
        master_df = pd.merge(risk_df, target_df, on=['Ticker', 'Year'], how='inner')
        return master_df

# ==========================================
# 2. DATA ENGINEERING & TENSOR GENERATION
# ==========================================
class SequentialRiskDataset(Dataset):
    """Transforms 2D panel data into 3D tensors (N, T, K) with strict pre-padding."""
    def __init__(self, df: pd.DataFrame, risk_cols: list[str], factor_cols: list[str], target_col: str, max_seq_len: int = 3):
        self.max_seq_len = max_seq_len
        self.k_dim = len(risk_cols)
        self.m_dim = len(factor_cols)

        self.x_data, self.padding_masks, self.y_data, self.f_data = [], [], [], []

        grouped = df.groupby('Ticker')
        for _, group in grouped:
            seq_len = len(group)
            if seq_len == 0:
                continue

            if seq_len > self.max_seq_len:
                group = group.iloc[-self.max_seq_len:]
                seq_len = self.max_seq_len

            risk_matrix = group[risk_cols].values
            target = group[target_col].values[-1]
            factors = group[factor_cols].values[-1]

            pad_len = self.max_seq_len - seq_len
            if pad_len > 0:
                pad_matrix = np.zeros((pad_len, self.k_dim), dtype=np.float32)
                risk_matrix = np.vstack((pad_matrix, risk_matrix))

            mask = np.array([True] * pad_len + [False] * seq_len, dtype=bool)

            self.x_data.append(risk_matrix)
            self.padding_masks.append(mask)
            self.y_data.append(target)
            self.f_data.append(factors)

        self.x_tensor = torch.tensor(np.stack(self.x_data), dtype=torch.float32)
        self.mask_tensor = torch.tensor(np.stack(self.padding_masks), dtype=torch.bool)
        self.y_tensor = torch.tensor(np.array(self.y_data), dtype=torch.float32)
        self.f_tensor = torch.tensor(np.stack(self.f_data), dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.y_data)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.x_tensor[idx], self.mask_tensor[idx], self.f_tensor[idx], self.y_tensor[idx]

# ==========================================
# 3. MATHEMATICAL ARCHITECTURE
# ==========================================
class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 50):
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, :x.size(1), :]
        return x

class TransformerAssetPricingModel(nn.Module):
    def __init__(self, k_dim: int, m_dim: int, d_model: int = 64, nhead: int = 4, num_layers: int = 1, dropout: float = 0.3):
        super(TransformerAssetPricingModel, self).__init__()
        self.d_model = d_model

        self.input_projection = nn.Linear(k_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=d_model * 4, dropout=dropout, batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.mlp_beta = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, m_dim)
        )

    def forward(self, x: torch.Tensor, padding_mask: torch.Tensor, f_t1: torch.Tensor) -> torch.Tensor:
        x_emb = self.input_projection(x) * math.sqrt(self.d_model)
        x_emb = self.pos_encoder(x_emb)

        context = self.transformer_encoder(x_emb, src_key_padding_mask=padding_mask)
        c_t = context[:, -1, :]

        beta = self.mlp_beta(c_t)
        logits = (beta * f_t1).sum(dim=1)
        return logits

# ==========================================
# 3.b ADVANCED LOSS FUNCTION (FOCAL LOSS)
# ==========================================
class FocalLossWithLogits(nn.Module):
    """
    Computes the Focal Loss directly from pre-sigmoid logits for numerical stability.
    Mathematically down-weights the majority class (non-crash) to force the
    attention mechanism to learn the minority class (crash).
    """
    def __init__(self, alpha: float = 0.25, gamma: float = 2.0, reduction: str = 'mean'):
        """
        Args:
            alpha: Weighting factor for the minority class.
            gamma: Focusing parameter to penalize hard-to-classify examples.
            reduction: Specifies the reduction to apply to the output ('none', 'mean', 'sum').
        """
        super(FocalLossWithLogits, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
        self.bce_with_logits = nn.BCEWithLogitsLoss(reduction='none')

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            logits: Unnormalized predictions of shape (N,)
            targets: Binary ground truth labels of shape (N,)
        Returns:
            Reduced focal loss scalar.
        """
        # Compute standard cross entropy loss
        bce_loss = self.bce_with_logits(logits, targets)

        # Calculate pt (the predicted probability of the true class)
        # Since bce_loss = -log(pt), then pt = exp(-bce_loss)
        pt = torch.exp(-bce_loss)

        # Apply the focal loss modulation
        focal_loss = self.alpha * (1 - pt) ** self.gamma * bce_loss

        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        return focal_loss

# ==========================================
# 4. UPDATED HYPERPARAMETER OPTIMIZATION
# ==========================================
def objective(trial: optuna.Trial, train_loader: DataLoader, val_loader: DataLoader, k_dim: int, m_dim: int) -> float:
    # Architectural Parameters
    d_model = trial.suggest_categorical("d_model", [64, 128])
    nhead = trial.suggest_categorical("nhead", [4, 8])
    num_layers = trial.suggest_int("num_layers", 1, 2)
    dropout = trial.suggest_float("dropout", 0.3, 0.5)

    # Optimizer Parameters
    lr = trial.suggest_float("lr", 1e-5, 1e-3, log=True)
    weight_decay = trial.suggest_float("weight_decay", 1e-4, 1e-2, log=True)

    # Focal Loss Parameters
    gamma = trial.suggest_float("gamma", 1.0, 3.0)
    alpha = trial.suggest_float("alpha", 0.1, 0.4)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TransformerAssetPricingModel(
        k_dim=k_dim, m_dim=m_dim, d_model=d_model, nhead=nhead, num_layers=num_layers, dropout=dropout
    ).to(device)

    # Instantiate Focal Loss instead of standard BCE
    criterion = FocalLossWithLogits(alpha=alpha, gamma=gamma, reduction='mean')
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    for epoch in range(25):
        model.train()
        for x_batch, mask_batch, f_batch, y_batch in train_loader:
            x_batch = x_batch.to(device)
            mask_batch = mask_batch.to(device)
            f_batch = f_batch.to(device)
            y_batch = y_batch.to(device)

            optimizer.zero_grad()
            logits = model(x_batch, mask_batch, f_batch)
            loss = criterion(logits, y_batch)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

    model.eval()
    all_preds, all_targets = [], []
    with torch.no_grad():
        for x_batch, mask_batch, f_batch, y_batch in val_loader:
            x_batch = x_batch.to(device)
            mask_batch = mask_batch.to(device)
            f_batch = f_batch.to(device)

            logits = model(x_batch, mask_batch, f_batch)
            probs = torch.sigmoid(logits)

            all_preds.extend(probs.cpu().numpy())
            all_targets.extend(y_batch.numpy())

    try:
        roc_auc = roc_auc_score(all_targets, all_preds)
    except ValueError:
        roc_auc = 0.5

    return roc_auc

def run_empirical_pipeline(macro_csv_path: str):
    print("Initializing Empirical Transformer Asset Pricing Pipeline...")

    # 1. Load NLP Risk Data
    risk_df = pd.read_csv(macro_csv_path)
    base_tickers = risk_df['Ticker'].unique().tolist()

    # Identify dynamic risk columns (exclude Ticker, Year, and non-feature columns)
    risk_cols = [c for c in risk_df.columns if c not in ['Ticker', 'Year', 'Unnamed: 0']]
    factor_cols = ['Factor_Mkt_Ret', 'Factor_Momentum', 'Factor_Hist_Vol']

    # 2. Fetch Pricing & Generate Targets
    engine = MarketDataTargetEngine(base_tickers)
    engine.fetch_data()
    master_df = engine.generate_targets_and_factors(risk_df)

    if master_df.empty:
        raise ValueError("Dimensionality Collapse: Failed to align NLP risk scores with valid forward pricing vectors.")

    # 3. Spatial Cross-Validation Split (80/20 by Ticker to preserve temporal sequences)
    unique_tickers = master_df['Ticker'].unique()
    np.random.shuffle(unique_tickers)
    split_idx = int(len(unique_tickers) * 0.8)

    train_df = master_df[master_df['Ticker'].isin(unique_tickers[:split_idx])].sort_values(['Ticker', 'Year'])
    val_df = master_df[master_df['Ticker'].isin(unique_tickers[split_idx:])].sort_values(['Ticker', 'Year'])

    print(f"Dataset aligned. Tickers -> Train: {split_idx} | Validation: {len(unique_tickers) - split_idx}")
    print(f"Crash Risk Target (Class 1): {master_df['Crash_Risk'].sum()} instances detected.")

    train_dataset = SequentialRiskDataset(train_df, risk_cols, factor_cols, 'Crash_Risk')
    val_dataset = SequentialRiskDataset(val_df, risk_cols, factor_cols, 'Crash_Risk')

    # Adjust batch size strictly for small N environments to guarantee backprop
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

    # 4. Bayesian Optimization
    study = optuna.create_study(direction="maximize")
    study.optimize(lambda trial: objective(trial, train_loader, val_loader, len(risk_cols), len(factor_cols)), n_trials=30)

    print(f"\nOptimization Complete. Best Out-of-Sample ROC-AUC: {study.best_value:.4f}")

    # 1. Instantiate the 'Best' Model
    best_params = study.best_params
    best_model = TransformerAssetPricingModel(
        k_dim=len(risk_cols),
        m_dim=len(factor_cols),
        d_model=best_params['d_model'],
        nhead=best_params['nhead'],
        num_layers=best_params['num_layers'],
        dropout=best_params['dropout']
    )

    # 2. Perform a final training pass to set the weights
    # We use the FocalLoss defined in your script
    criterion = FocalLossWithLogits(alpha=best_params['alpha'], gamma=best_params['gamma'])
    optimizer = torch.optim.AdamW(best_model.parameters(), lr=best_params['lr'], weight_decay=best_params['weight_decay'])

    print("Performing final training pass with optimal parameters for visualization...")
    best_model.train()
    for epoch in range(10): # Brief training pass
        for x_batch, mask_batch, f_batch, y_batch in train_loader:
            optimizer.zero_grad()
            logits = best_model(x_batch, mask_batch, f_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            optimizer.step()

    # 3. Call the visualization function
    # Ensure 'engine.price_data' and 'val_dataset' are in scope
    transformer_plot.plot_prediction_vs_price(
        model=best_model,
        val_dataset=val_dataset,
        valid_tickers=val_df['Ticker'].unique().tolist(),
        price_data=engine.price_data
    )

if __name__ == "__main__":
    MACRO_CSV = PROJECT_ROOT / "data" / "interim" / "scoring_outputs" / "risk_scores_macro_annual.csv"
    run_empirical_pipeline(MACRO_CSV)
