import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import os

def generate_attention_network(csv_path: str, top_k_edges: int = 50, output_filename: str = "st_gat_attention_network_cross.png"):
    """
    Ingests the ST-GAT attention weights CSV, removes self-loops, and renders
    a directed network graph mapping cross-asset risk spillovers.
    """
    print("Initializing NetworkX Attention Visualization (Cross-Asset Only)...")

    if not os.path.exists(csv_path):
        print(f"Error: Target file missing: {csv_path}")
        return

    # 1. Load Data
    df = pd.read_csv(csv_path)

    # FIXED: Strip out self-loops. We only care about how Company A affects Company B.
    df_cross = df[df['Source_Ticker'] != df['Target_Ticker']].copy()

    if df_cross.empty:
        print("Warning: No cross-company edges found. The threshold tau may be too high.")
        return

    # Filter for the strongest K cross-asset connections
    df_top = df_cross.nlargest(top_k_edges, 'Attention_Weight').copy()

    max_weight = df_top['Attention_Weight'].max()
    min_weight = df_top['Attention_Weight'].min()

    # 2. Construct Directed Graph
    G = nx.DiGraph()
    for _, row in df_top.iterrows():
        G.add_edge(
            row['Source_Ticker'],
            row['Target_Ticker'],
            weight=row['Attention_Weight']
        )

    # 3. Graph Layout Optimization (Spring layout naturally groups connected clusters)
    pos = nx.spring_layout(G, k=0.8, seed=42)

    # 4. Rendering Setup
    plt.figure(figsize=(14, 10))
    ax = plt.gca()
    ax.set_title(f"ST-GAT Cross-Asset Contagion: Top {top_k_edges} Risk Spillovers",
                 fontsize=18, fontweight='bold', pad=20)

    cmap = cm.get_cmap('magma_r')
    # Add a slight buffer to the normalization so the weakest edge isn't invisible
    norm = mcolors.Normalize(vmin=min_weight - 0.01, vmax=max_weight)

    edges = G.edges(data=True)
    edge_colors = [cmap(norm(d['weight'])) for u, v, d in edges]
    edge_widths = [max(1.0, (d['weight'] / min_weight) * 3.0) for u, v, d in edges]

    # 5. Draw Network
    nx.draw_networkx_nodes(
        G, pos,
        node_size=800,
        node_color='#E0EAF5',
        edgecolors='#2B475D',
        linewidths=1.5,
        ax=ax
    )

    nx.draw_networkx_edges(
        G, pos,
        arrowstyle='-|>',
        arrowsize=20,
        edge_color=edge_colors,
        width=edge_widths,
        connectionstyle="arc3,rad=0.15",
        ax=ax
    )

    nx.draw_networkx_labels(
        G, pos,
        font_size=10,
        font_weight='bold',
        ax=ax
    )

    # 6. Legend
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.7, aspect=20, pad=0.02)
    cbar.set_label('Cross-Asset Attention Weight Magnitude ($a_{ij}$)', rotation=270, labelpad=20, fontsize=12)

    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Visualization rendered and saved to: {output_filename}")

if __name__ == "__main__":
    ATTENTION_CSV = "ST_GAT_Attention_Weights.csv"
    generate_attention_network(ATTENTION_CSV, top_k_edges=50)