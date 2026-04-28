import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DRIFT_CSV = PROJECT_ROOT / "outputs" / "tables" / "Corporate_Structural_Drift.csv"
RISK_CSV = PROJECT_ROOT / "data" / "interim" / "scoring_outputs" / "risk_scores_macro_annual.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures"

def plot_drift_polarization(drift_df):
    """
    Creates a divergent bar chart showing the highest vs lowest drifting companies.
    """
    # Get Top 10 and Bottom 10
    top_10 = drift_df.head(10).copy()
    bottom_10 = drift_df.tail(10).copy()

    # Combine and assign a category for coloring
    top_10['Type'] = 'High Structural Drift (Restructuring)'
    bottom_10['Type'] = 'Low Structural Drift (Boilerplate)'

    plot_df = pd.concat([top_10, bottom_10])
    plot_df = plot_df.sort_values(by='Avg_YoY_Drift', ascending=True)

    plt.figure(figsize=(12, 8))
    sns.set_theme(style="whitegrid")

    # Create the horizontal bar plot
    bars = plt.barh(plot_df['Ticker'], plot_df['Avg_YoY_Drift'],
                    color=['royalblue' if t == 'Low Structural Drift (Boilerplate)' else 'crimson' for t in plot_df['Type']])

    plt.xlabel('Average Year-over-Year Cosine Drift', fontsize=12, fontweight='bold')
    plt.ylabel('Company Ticker', fontsize=12, fontweight='bold')
    plt.title('Corporate Risk Disclosure Polarization (2006-2024)', fontsize=16, fontweight='bold')

    # Add exact values to the end of the bars
    for bar in bars:
        plt.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                 f'{bar.get_width():.3f}',
                 va='center', ha='left', fontsize=10)

    # Custom Legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='crimson', label='High Drift (Dynamic Restructuring)'),
                       Patch(facecolor='royalblue', label='Zero/Low Drift (Static Boilerplate)')]
    plt.legend(handles=legend_elements, loc='lower right', fontsize=11)

    plt.tight_layout()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "Drift_Polarization_BarChart.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved -> {output_path}")

def plot_longitudinal_trajectory(risk_df):
    """
    Traces the actual Year-over-Year drift magnitude for specific case studies over time.
    """
    # Select 2 volatile companies and 2 stable companies based on your results
    target_tickers = ['ADM', 'AIG', 'DUK', 'GE']
    colors = {'ADM': 'darkred', 'AIG': 'crimson', 'DUK': 'cornflowerblue', 'GE': 'navy'}

    plt.figure(figsize=(12, 6))
    sns.set_theme(style="white")

    risk_cols = [c for c in risk_df.columns if c not in ['Ticker', 'Year']]

    for ticker in target_tickers:
        group = risk_df[risk_df['Ticker'] == ticker].sort_values('Year')
        if len(group) < 3:
            continue

        years = group['Year'].values[1:] # YoY starts from year 2
        vectors = group[risk_cols].values

        yoy_drifts = []
        for i in range(1, len(vectors)):
            v1, v2 = vectors[i-1], vectors[i]
            if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
                dist = 1.0
            else:
                sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                dist = 1.0 - sim
            yoy_drifts.append(dist)

        plt.plot(years, yoy_drifts, marker='o', linewidth=2.5, markersize=8,
                 label=f"{ticker}", color=colors[ticker], alpha=0.8)

    plt.axhline(y=0, color='black', linestyle='--', linewidth=1)
    plt.xlabel('Filing Year', fontsize=12, fontweight='bold')
    plt.ylabel('YoY Cosine Drift Magnitude', fontsize=12, fontweight='bold')
    plt.title('Longitudinal Risk Trajectory: Dynamic vs. Boilerplate Disclosures', fontsize=16, fontweight='bold')

    # Force integer ticks for years
    plt.xticks(np.arange(min(risk_df['Year']), max(risk_df['Year'])+1, 2))

    plt.legend(title='Company', fontsize=11, title_fontsize=12, loc='upper left')
    plt.grid(True, axis='y', linestyle='--', alpha=0.6)

    plt.tight_layout()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "Longitudinal_Drift_Trajectory.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved -> {output_path}")

def main():
    print("Loading datasets...")
    try:
        drift_df = pd.read_csv(DRIFT_CSV)
        risk_df = pd.read_csv(RISK_CSV)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return

    print("Generating Visualizations...")
    plot_drift_polarization(drift_df)
    plot_longitudinal_trajectory(risk_df)
    print("Done!")

if __name__ == "__main__":
    main()
