import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path
from scipy.spatial.distance import pdist, squareform

# ==========================================
# 1. CONFIGURATION
# ==========================================
PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
RISK_CSV_PATH = os.getenv(
    "FYP_RISK_SCORES_MACRO_CSV",
    os.path.join(PROJECT_ROOT, "data", "interim", "scoring_outputs", "risk_scores_macro_annual.csv"),
)
OUTPUT_DIR = os.getenv(
    "FYP_NETWORK_OUTPUT_DIR",
    os.path.join(PROJECT_ROOT, "outputs", "econometrics", "network_evolution"),
)
TAU = float(os.getenv("FYP_NETWORK_TAU", "0.9304"))  # The optimal threshold found by Optuna
LANDMARK_YEARS = [2008, 2020, 2024]  # Financial Crisis, COVID, Current

def build_adjacency_matrix(df_year, tau):
    """Computes the thresholded cosine similarity adjacency matrix for a given year."""
    tickers = df_year['Ticker'].values
    # Extract only numeric risk features
    risk_features = df_year.select_dtypes(include=[np.number]).drop(columns=['Year'], errors='ignore')
    
    # Compute Cosine Similarity
    dist_matrix = pdist(risk_features.values, metric='cosine')
    dist_matrix = np.nan_to_num(dist_matrix, nan=1.0)
    sim_matrix = 1.0 - squareform(dist_matrix)
    np.fill_diagonal(sim_matrix, 0.0)
    
    # Thresholding
    adj_matrix = np.where(sim_matrix >= tau, sim_matrix, 0.0)
    return adj_matrix, tickers

def plot_network_for_year(df, year, tau, output_filename):
    """Generates and saves a network graph visualization for a specific year."""
    df_year = df[df['Year'] == year].copy()
    if df_year.empty:
        print(f"No data available for {year}.")
        return

    adj_matrix, tickers = build_adjacency_matrix(df_year, tau)
    
    # Build NetworkX Graph
    G = nx.Graph()
    for i, ticker in enumerate(tickers):
        G.add_node(ticker)
        
    rows, cols = np.where(adj_matrix > 0)
    for r, c in zip(rows, cols):
        if r < c: # Undirected graph, avoid duplicate edges
            G.add_edge(tickers[r], tickers[c], weight=adj_matrix[r, c])
            
    # Remove isolated nodes for a cleaner plot
    G.remove_nodes_from(list(nx.isolates(G)))
    
    plt.figure(figsize=(14, 10))
    pos = nx.spring_layout(G, k=0.15, seed=42)
    
    # Draw Graph
    nx.draw_networkx_nodes(G, pos, node_size=50, node_color='royalblue', alpha=0.7)
    nx.draw_networkx_edges(G, pos, width=0.5, alpha=0.3, edge_color='gray')
    nx.draw_networkx_labels(G, pos, font_size=8, font_family="sans-serif")
    
    plt.title(f"S&P 500 Latent Risk Topology (Year: {year} | $\\tau={tau}$)", fontsize=16, fontweight='bold')
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    plt.close()
    print(f"Saved network visualization for {year} to {output_filename}")

def calculate_network_drift(df):
    """
    Calculates the year-over-year Cosine Distance of a company's risk vector.
    High drift indicates massive structural transformation in corporate disclosures.
    """
    df = df.sort_values(by=['Ticker', 'Year'])
    risk_cols = [c for c in df.columns if c not in ['Ticker', 'Year']]
    
    drift_records = []
    
    # Group by Ticker to analyze longitudinal shifts
    for ticker, group in df.groupby('Ticker'):
        if len(group) < 3: # Need sufficient history
            continue
            
        group = group.sort_values('Year')
        years = group['Year'].values
        vectors = group[risk_cols].values
        
        yoy_drifts = []
        for i in range(1, len(vectors)):
            # Cosine distance between Year T and Year T-1
            # Distance = 1 - Cosine Similarity. Higher distance = Higher Drift.
            v1 = vectors[i-1]
            v2 = vectors[i]
            
            # Handle zero vectors safely
            if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
                dist = 1.0
            else:
                sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                dist = 1.0 - sim
            yoy_drifts.append(dist)
            
        # Average annual drift
        avg_drift = np.mean(yoy_drifts)
        cumulative_shift = np.sum(yoy_drifts)
        
        drift_records.append({
            'Ticker': ticker,
            'Years_Active': len(years),
            'Avg_YoY_Drift': avg_drift,
            'Cumulative_Shift': cumulative_shift
        })
        
    drift_df = pd.DataFrame(drift_records)
    drift_df = drift_df.sort_values(by='Avg_YoY_Drift', ascending=False).reset_index(drop=True)
    return drift_df

def main():
    print("Loading Risk Scores...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(RISK_CSV_PATH):
        raise FileNotFoundError(
            f"Risk score file not found: {RISK_CSV_PATH}. "
            "Set FYP_RISK_SCORES_MACRO_CSV or place the file under data/interim/scoring_outputs/."
        )
    df = pd.read_csv(RISK_CSV_PATH)
    
    # 1. Generate Network Plots
    print("\nGenerating Landmark Network Topologies...")
    for year in LANDMARK_YEARS:
        output_path = os.path.join(OUTPUT_DIR, f"risk_network_{year}.png")
        plot_network_for_year(df, year, TAU, output_path)
        
    # 2. Calculate Structural Deviation (Drift)
    print("\nCalculating Structural Corporate Drift (2006-2024)...")
    drift_df = calculate_network_drift(df)
    
    drift_output_path = os.path.join(OUTPUT_DIR, "Corporate_Structural_Drift.csv")
    drift_df.to_csv(drift_output_path, index=False)
    print(f"Saved structural drift table to {drift_output_path}")
    
    print("\nTop 10 Most Structurally Deviating Companies (Highest YoY Risk Drift):")
    print(drift_df.head(10).to_string(index=False))
    
    print("\nTop 10 Most Structurally Stable Companies (Lowest YoY Risk Drift):")
    print(drift_df.tail(10).to_string(index=False))

if __name__ == "__main__":
    main()
