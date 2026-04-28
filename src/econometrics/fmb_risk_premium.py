import os
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from pathlib import Path

warnings.filterwarnings("ignore")

# ================= CONFIGURATION =================
START_DATE = "2020-01-01"
END_DATE   = "2025-12-31"
PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
RISK_SCORES_PATH = os.getenv(
    "FYP_RISK_SCORES_MESO_CSV",
    os.path.join(PROJECT_ROOT, "data", "interim", "scoring_outputs", "risk_scores_meso_annual.csv"),
)
OUTDIR = os.getenv(
    "FYP_FMB_OUTPUT_DIR",
    os.path.join(PROJECT_ROOT, "outputs", "econometrics", "fmb_benchmark_analysis"),
)
os.makedirs(OUTDIR, exist_ok=True)
# =================================================

def load_and_prep_data():
    print("Loading data for Fama-MacBeth regression...")
    risk_df = pd.read_csv(RISK_SCORES_PATH)
    
    if 'Ticker' not in risk_df.columns:
        risk_df = risk_df.reset_index()
        
    risk_df['Year'] = risk_df['Year'].astype(int)
    risk_df['Ticker'] = risk_df['Ticker'].str.replace('.', '-', regex=False)
    tickers = risk_df['Ticker'].unique().tolist()
    
    print(f"Downloading prices for {len(tickers)} tickers. (Using safe loop mode)...")
    import yfinance as yf
    
    ret_records = []
    for t in tickers:
        try:
            # Download individual ticker history safely
            p = yf.Ticker(t).history(start=START_DATE, end=END_DATE, interval="1mo")
            if not p.empty:
                # Calculate 1-month forward log return
                p['Fwd_Return'] = np.log(p['Close'] / p['Close'].shift(1)).shift(-1)
                for date, row in p.iterrows():
                    if pd.notna(row['Fwd_Return']):
                        ret_records.append({
                            'Date': date.tz_localize(None), 
                            'Ticker': t, 
                            'Fwd_Return': row['Fwd_Return']
                        })
        except:
            pass # Ignore delisted/failed tickers
            
    ret_df = pd.DataFrame(ret_records)
    if ret_df.empty:
        print("❌ ERROR: yfinance could not download any valid prices.")
        return pd.DataFrame()
        
    ret_df['Year'] = ret_df['Date'].dt.year.astype(int)
    
    # The Safe Merge
    panel_df = pd.merge(ret_df, risk_df, on=['Ticker', 'Year'], how='inner')
    panel_df = panel_df.dropna(subset=['Fwd_Return'])
    
    print(f"--> Merge Complete: {len(panel_df)} valid month-ticker observations found.")
    return panel_df

def univariate_fama_macbeth(panel_df):
    if panel_df.empty:
        print("❌ ERROR: panel_df is empty. The merge failed, likely due to mismatched Tickers or Years.")
        return pd.DataFrame()
        
    print("Running Univariate Fama-MacBeth Regressions (Factor by Factor)...")
    dates = panel_df['Date'].unique()
    risk_cols = [c for c in panel_df.columns if c not in ['Date', 'Ticker', 'Year', 'Fwd_Return']]
    
    results = []
    
    for risk in risk_cols:
        coefs = []
        for d in dates:
            df_t = panel_df[panel_df['Date'] == d].dropna(subset=['Fwd_Return', risk])
            
            if len(df_t) > 2: 
                Y = df_t['Fwd_Return'].values
                X = df_t[risk].values
                
                if np.var(X) > 1e-8:
                    X = sm.add_constant(X, has_constant='add')
                    res = sm.OLS(Y, X).fit()
                    coefs.append(res.params[1])
        
        if not coefs:
            continue
            
        ts = pd.Series(coefs)
        mean_coef = ts.mean()
        
        try:
            nw_res = sm.OLS(ts.values, np.ones(len(ts))).fit(cov_type='HAC', cov_kwds={'maxlags': 3})
            se = nw_res.bse[0]
            t_stat = nw_res.tvalues[0]
            p_val = nw_res.pvalues[0]
        except:
            se = ts.std() / np.sqrt(len(ts)) if len(ts) > 1 else 1e-6
            t_stat = mean_coef / se if se > 0 else 0
            p_val = stats.t.sf(np.abs(t_stat), max(len(ts)-1, 1))*2
            
        results.append({
            'Risk Factor': risk,
            'Risk Premium': mean_coef,
            'Std Err': se,
            't-stat': t_stat,
            'p-value': p_val
        })
        
    if not results:
        print("❌ ERROR: No risk factors had enough variance to run regressions.")
        return pd.DataFrame()
        
    fmb_results = pd.DataFrame(results).sort_values('t-stat', key=abs, ascending=False)
    return fmb_results

def main():
    panel_df = load_and_prep_data()
    fmb_results = univariate_fama_macbeth(panel_df)
    
    if fmb_results.empty:
        empty_cols = ["Risk Factor", "Risk Premium", "Std Err", "t-stat", "p-value"]
        pd.DataFrame(columns=empty_cols).to_csv(
            os.path.join(OUTDIR, "fmb_results_summary.csv"),
            index=False,
        )
        return
        
    print("\n" + "="*90)
    print("UNIVARIATE FAMA-MACBETH REGRESSION RESULTS (Risk Premium Analysis)")
    print("="*90)
    print(fmb_results.head(20).to_string(index=False, float_format=lambda x: f"{x:.5f}"))
    print("="*90)
    
    fmb_results.to_csv(os.path.join(OUTDIR, "fmb_results_summary.csv"), index=False)
    print(f"\n✅ FMB run complete. Results saved to {OUTDIR}/fmb_results_summary.csv")

if __name__ == "__main__":
    main()
