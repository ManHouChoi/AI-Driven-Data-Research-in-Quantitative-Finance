import os
import pandas as pd
import matplotlib.pyplot as plt

# ================= CONFIGURATION =================
PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", os.getcwd())
FMB_OUTPUT_DIR = os.getenv(
    "FYP_FMB_OUTPUT_DIR",
    os.path.join(PROJECT_ROOT, "outputs", "econometrics", "fmb_benchmark_analysis"),
)
CSV_PATH = os.getenv(
    "FYP_FMB_RESULTS_CSV",
    os.path.join(FMB_OUTPUT_DIR, "fmb_results_summary.csv"),
)
OUTPUT_IMAGE = os.getenv(
    "FYP_FMB_PLOT_PATH",
    os.path.join(FMB_OUTPUT_DIR, "fmb_risk_premiums.png"),
)
# =================================================

def main():
    if not os.path.exists(CSV_PATH):
        print(f"❌ Could not find {CSV_PATH}")
        return
        
    df = pd.read_csv(CSV_PATH)
    
    # Take the top 10 most significant factors (lowest p-value / highest absolute t-stat)
    top_10 = df.head(10).copy()
    
    # Clean up the names for the chart (Keep only the specific Meso-risk name)
    top_10['Short Name'] = top_10['Risk Factor'].apply(lambda x: x.split('->')[-1].strip())
    
    # Reverse the order so the most significant is at the top of the horizontal bar chart
    top_10 = top_10.iloc[::-1]
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Assign colors: Red for negative premium (drag on returns), Green for positive
    colors = ['#c0392b' if val < 0 else '#27ae60' for val in top_10['Risk Premium']]
    
    # Plot horizontal bars with standard error lines
    bars = ax.barh(
        top_10['Short Name'], 
        top_10['Risk Premium'], 
        xerr=top_10['Std Err'], 
        color=colors, 
        alpha=0.85,
        capsize=4,
        edgecolor='black',
        linewidth=0.8
    )
    
    ax.axvline(0, color='black', linewidth=1.5)
    ax.set_xlabel('Estimated Risk Premium ($\lambda$)', fontsize=12, fontweight='bold')
    ax.set_title('Top 10 Statistically Significant Meso-Risk Premiums (2020–2025)', fontsize=14, fontweight='bold', pad=15)
    ax.tick_params(axis='y', labelsize=11)
    
    # Add t-stat annotations next to the bars
    for bar, t_stat in zip(bars, top_10['t-stat']):
        xval = bar.get_width()
        # Offset the text slightly depending on if the bar is positive or negative
        offset = 0.02 if xval >= 0 else -0.06
        ax.text(xval + offset, bar.get_y() + bar.get_height()/2, 
                f't={t_stat:.2f}', 
                va='center', ha='left' if xval >= 0 else 'right', 
                fontsize=10, fontweight='bold', color='#333333')

    plt.tight_layout()
    os.makedirs(os.path.dirname(OUTPUT_IMAGE), exist_ok=True)
    plt.savefig(OUTPUT_IMAGE, dpi=300, bbox_inches='tight')
    print(f"✅ Plot saved as {OUTPUT_IMAGE}")

if __name__ == "__main__":
    main()