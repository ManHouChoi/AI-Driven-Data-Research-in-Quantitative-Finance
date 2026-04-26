# dav_volatility.py
"""
DAV Volatility Analysis: The "Horse Race"
-----------------------------------------
Models Compared:
 1. GARCH(1,1) [Baseline]
 2. EGARCH(1,1) [Control] - Captures asymmetry without text data.
 3. DAV (EGARCH-X) [Proposed] - Captures asymmetry + Textual Risk Level & Shock.

Outputs:
 - Leaderboard HTML with "Physical Meaning" interpretations.
 - Metrics CSV comparing all 3 models.
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from dataclasses import dataclass
from typing import Dict

warnings.filterwarnings("ignore")

# ================= CONFIGURATION =================
PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", os.getcwd())
START_DATE = os.getenv("FYP_DAV_START_DATE", "2020-01-01")
END_DATE = os.getenv("FYP_DAV_END_DATE", "2025-12-31")
RISK_SCORES_PATH = os.getenv(
    "FYP_RISK_SCORES_MESO_CSV",
    os.path.join(PROJECT_ROOT, "data", "processed", "risk_scores_meso_annual.csv"),
)
OUTDIR = os.getenv(
    "FYP_DAV_OUTPUT_DIR",
    os.path.join(PROJECT_ROOT, "outputs", "econometrics", "dav_benchmark_analysis"),
)
os.makedirs(OUTDIR, exist_ok=True)
# =================================================

# --- DATA LOADERS ---
def load_risk_matrix_annual(path):
    if not os.path.exists(path):
        print(f"❌ Risk matrix not found: {path}")
        print("   Set FYP_RISK_SCORES_MESO_CSV or place the file under data/processed/.")
        return pd.DataFrame()
    df = pd.read_csv(path, index_col=['Ticker', 'Year'])
    print(f"   Loaded Annual Risk Scores for {len(df.index.levels[0])} companies.")
    return df

def load_prices_yf(tickers, start, end):
    import yfinance as yf
    print(f"   Downloading prices for {len(tickers)} tickers...")
    try:
        df = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
        return df
    except Exception as e:
        print(f"   ⚠️ yfinance error: {e}")
        return pd.DataFrame()

def process_prices(px_raw):
    if isinstance(px_raw.columns, pd.MultiIndex):
        try:
            df = px_raw['Adj Close'].copy() if 'Adj Close' in px_raw.columns.levels[0] else px_raw['Close'].copy()
        except: df = px_raw.iloc[:, 0:].copy()
    else: df = px_raw.copy()
    
    df = df.reset_index().melt(id_vars="Date", var_name="Ticker", value_name="AdjClose")
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df = df.dropna().sort_values(['Ticker', 'Date'])
    
    df['Return'] = np.log(df['AdjClose'] / df.groupby('Ticker')['AdjClose'].shift(1))
    df['RealizedVol'] = df.groupby('Ticker')['Return'].transform(
        lambda x: x.rolling(30).std() * np.sqrt(252)
    )
    return df.dropna()

def construct_risk_time_series(ticker, risk_cat, dates, risk_df_annual):
    s_daily = pd.Series(index=dates, dtype=float).sort_index()
    try:
        ticker_data = risk_df_annual.loc[ticker]
        for year, row in ticker_data.iterrows():
            s_daily.loc[str(year)] = row[risk_cat]
    except KeyError: pass

    s_daily = s_daily.ffill().bfill().fillna(0)
    ds_daily = s_daily.diff().fillna(0)
    
    # Scale x10 for optimizer stability
    return s_daily.values * 10.0, ds_daily.values * 10.0

# --- MODELS ---
@dataclass
class ModelResult:
    name: str; bic: float; mse: float; params: Dict; variance: np.ndarray; success: bool

def _nll_gaussian(eps, h):
    h = np.maximum(h, 1e-12)
    return 0.5 * np.sum(np.log(2 * np.pi) + np.log(h) + (eps ** 2) / h)

# 1. GARCH(1,1) - Baseline
def fit_garch(r):
    theta0 = [np.mean(r), np.log(np.var(r)*0.01), 0.0, 2.0]
    def transform(t):
        alpha = 1/(1+np.exp(-t[2]))*0.99
        beta = 1/(1+np.exp(-t[3]))*(1-alpha)*0.99
        return {"mu": t[0], "omega": np.exp(t[1]), "alpha": alpha, "beta": beta}
    def filter_f(t):
        p=transform(t); n=len(r); h=np.zeros(n); eps=r-p["mu"]; h[:]=np.var(r)
        for i in range(1,n): h[i] = p["omega"] + p["alpha"]*eps[i-1]**2 + p["beta"]*h[i-1]
        return h, eps
    def obj(t): h,e=filter_f(t); return _nll_gaussian(e,h)
    
    res = minimize(obj, theta0, method="L-BFGS-B")
    h, _ = filter_f(res.x)
    bic = 4*np.log(len(r)) + 2*res.fun
    mse_score = np.mean(((r**2) - h)**2)
    return ModelResult("GARCH", bic, mse_score, transform(res.x), h, res.success)

# 2. EGARCH(1,1) - Control
def fit_egarch(r):
    theta0 = [np.mean(r), -1.0, 0.1, -0.05, 0.90]
    def transform(t):
        return {"mu":t[0], "omega":t[1], "alpha":t[2], "gamma":t[3], "beta":t[4]}
    def filter_f(t):
        p=transform(t); n=len(r); ln_h=np.zeros(n); eps=r-p["mu"]
        ln_h[:] = np.log(np.var(r)+1e-6); E_abs_z = np.sqrt(2/np.pi)
        for i in range(1,n):
            h_prev=np.exp(ln_h[i-1]); z=eps[i-1]/(np.sqrt(h_prev)+1e-12)
            ln_h[i] = p["omega"] + p["beta"]*ln_h[i-1] + p["alpha"]*(np.abs(z)-E_abs_z) + p["gamma"]*z
            if ln_h[i] < -20: ln_h[i]=-20
            elif ln_h[i] > 10: ln_h[i]=10
        return np.exp(ln_h), eps
    def obj(t): 
        if abs(t[4])>=0.999: return 1e9
        h,e=filter_f(t); return _nll_gaussian(e,h)
        
    res = minimize(obj, theta0, method="L-BFGS-B", bounds=[(None,None)]*2+[(None,None)]*2+[(0.001,0.999)])
    h, _ = filter_f(res.x)
    bic = 5*np.log(len(r)) + 2*res.fun
    mse_score = np.mean(((r**2) - h)**2)
    return ModelResult("EGARCH", bic, mse_score, transform(res.x), h, res.success)

# 3. DAV (EGARCH-X) - Proposed
def fit_dav(r, S, dS):
    theta0 = [np.mean(r), -1.0, 0.1, -0.05, 0.90, 0.0, 0.0]
    def transform(t):
        return {"mu":t[0], "omega":t[1], "alpha":t[2], "gamma":t[3], "beta":t[4], "delta1":t[5], "delta2":t[6]}
    def filter_f(t):
        p=transform(t); n=len(r); ln_h=np.zeros(n); eps=r-p["mu"]
        ln_h[:] = np.log(np.var(r)+1e-6); E_abs_z = np.sqrt(2/np.pi)
        for i in range(1,n):
            h_prev=np.exp(ln_h[i-1]); z=eps[i-1]/(np.sqrt(h_prev)+1e-12)
            # Full Equation
            ln_h[i] = (p["omega"] + p["beta"]*ln_h[i-1] + 
                       p["alpha"]*(np.abs(z)-E_abs_z) + p["gamma"]*z + 
                       p["delta1"]*S[i] + p["delta2"]*dS[i])
            if ln_h[i] < -20: ln_h[i]=-20
            elif ln_h[i] > 10: ln_h[i]=10
        return np.exp(ln_h), eps
    def obj(t): 
        if abs(t[4])>=0.999: return 1e9
        h,e=filter_f(t); return _nll_gaussian(e,h)
        
    bounds = [(None,None)]*2+[(None,None)]*2+[(0.001,0.999)]+[(-10,10)]*2
    res = minimize(obj, theta0, method="L-BFGS-B", bounds=bounds)
    h, _ = filter_f(res.x)
    bic = 7*np.log(len(r)) + 2*res.fun
    mse_score = np.mean(((r**2) - h)**2)
    return ModelResult("DAV", bic, mse_score, transform(res.x), h, res.success)

# --- INTERPRETATION ENGINE ---
def interpret_coefficients(d1, d2):
    """Generates physical meaning for Delta1 (Level) and Delta2 (Shock)."""
    meaning = []
    
    # Delta 1 (Level Effect)
    if abs(d1) < 0.01:
        meaning.append("Level: Neutral impact.")
    elif d1 > 0:
        meaning.append("<b>Level (+):</b> High disclosure correlates with <b>higher baseline risk</b> (Market nervousness).")
    else:
        meaning.append("<b>Level (-):</b> High disclosure correlates with <b>lower baseline risk</b> (Transparency premium).")
        
    # Delta 2 (Shock Effect)
    if abs(d2) < 0.01:
        meaning.append("Shock: No immediate reaction.")
    elif d2 > 0:
        meaning.append("<b>Shock (+):</b> New disclosure causes <b>volatility spikes</b> (Surprise factor).")
    else:
        meaning.append("<b>Shock (-):</b> New disclosure <b>calms the market</b> (Resolution of uncertainty).")
        
    return "<br>".join(meaning)

# --- REPORTING ---
def generate_report(results):
    html = """
    <html><head><style>
        body { font-family: 'Segoe UI', sans-serif; padding: 30px; background: #f9f9f9; color: #333; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .card { background: white; padding: 20px; margin-bottom: 30px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        table { border-collapse: collapse; width: 100%; font-size: 14px; margin-top: 15px; }
        th { background: #34495e; color: white; padding: 10px; text-align: left; }
        td { border-bottom: 1px solid #eee; padding: 8px; }
        .winner { background-color: #e8f8f5; color: #27ae60; font-weight: bold; border-left: 4px solid #27ae60; }
        .metric-good { color: green; }
        .metric-bad { color: red; }
        .interpretation { font-size: 13px; color: #555; font-style: italic; margin-top: 5px; line-height: 1.4; }
    </style></head><body>
    <h1>DAV Benchmark Analysis: GARCH vs EGARCH vs DAV</h1>
    <p>Comparing model fit (BIC) across the entire portfolio. Lower BIC indicates a better model.</p>
    """
    
    tickers = sorted(list(set(r['Ticker'] for r in results)))
    
    for t in tickers:
        t_res = [r for r in results if r['Ticker'] == t]
        if not t_res: continue
        
        # Sort by best DAV improvement to find the most relevant risk
        t_res.sort(key=lambda x: x['DAV_BIC_Imp'], reverse=True)
        best_risk = t_res[0]
        
        # Determine Overall Winner
        models = [
            ('GARCH', best_risk['GARCH_BIC']),
            ('EGARCH', best_risk['EGARCH_BIC']),
            ('DAV', best_risk['DAV_BIC'])
        ]
        winner_name, winner_score = min(models, key=lambda x: x[1])
        
        html += f"""
        <div class="card">
            <h2>{t} <span style="font-size:0.6em; color:#7f8c8d;">(Best Predictor: {best_risk['Risk']})</span></h2>
            <table>
                <tr>
                    <th>Model</th>
                    <th>BIC Score</th>
                    <th>MSE (Accuracy)</th>
                    <th>vs. Baseline</th>
                </tr>
                <tr class="{'winner' if winner_name=='GARCH' else ''}">
                    <td>GARCH(1,1)</td>
                    <td>{best_risk['GARCH_BIC']:.2f}</td>
                    <td>{best_risk['GARCH_MSE']:.6f}</td>
                    <td>-</td>
                </tr>
                <tr class="{'winner' if winner_name=='EGARCH' else ''}">
                    <td>EGARCH(1,1) [Control]</td>
                    <td>{best_risk['EGARCH_BIC']:.2f}</td>
                    <td>{best_risk['EGARCH_MSE']:.6f}</td>
                    <td>{best_risk['GARCH_BIC'] - best_risk['EGARCH_BIC']:.2f}</td>
                </tr>
                <tr class="{'winner' if winner_name=='DAV' else ''}">
                    <td><b>DAV (EGARCH-X)</b></td>
                    <td>{best_risk['DAV_BIC']:.2f}</td>
                    <td>{best_risk['DAV_MSE']:.6f}</td>
                    <td><span class="metric-good">+{best_risk['DAV_BIC_Imp']:.2f}</span></td>
                </tr>
            </table>
            
            <div style="margin-top: 15px; background: #fff8e1; padding: 15px; border-left: 4px solid #f1c40f;">
                <strong>💡 Physical Meaning of DAV Coefficients:</strong><br>
                {best_risk['Interpretation']}
            </div>
            
            <br>
            <img src="{t}_{best_risk['Safe_Name']}.png" style="width:100%; max-width:900px; border:1px solid #ddd;">
        </div>
        """
        
    html += "</body></html>"
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "benchmark_report.html"), "w", encoding='utf-8') as f:
        f.write(html)

# --- MAIN ---
def main():
    print("🚀 Starting 3-Way Benchmark Analysis...")
    risk_df = load_risk_matrix_annual(RISK_SCORES_PATH)
    tickers = risk_df.index.get_level_values(0).unique().tolist()
    if not tickers:
        print("No tickers found. Exiting DAV benchmark.")
        return
    
    px_raw = load_prices_yf(tickers, START_DATE, END_DATE)
    if px_raw.empty:
        print("No price data downloaded. Exiting DAV benchmark.")
        return
    df = process_prices(px_raw)
    all_results = []
    
    for t in tickers:
        print(f"\n Analyzing {t}...")
        sub = df[df['Ticker'] == t].copy()
        if len(sub) < 500: continue
        
        r = sub['Return'].values
        dates = sub['Date'].values
        
        # 1. Fit Benchmarks ONCE per ticker
        garch = fit_garch(r)
        egarch = fit_egarch(r)
        
        if not garch.success or not egarch.success: 
            print("   Benchmarks failed to converge.")
            continue
            
        # 2. Fit DAV for Top Risks
        try:
            t_annual = risk_df.loc[t]
            top_risks = t_annual.sum().sort_values(ascending=False).head(10).index.tolist()
        except: continue
        
        best_dav_res = None
        best_imp = -9999
        
        for cat in top_risks:
            S, dS = construct_risk_time_series(t, cat, dates, risk_df)
            dav = fit_dav(r, S, dS)
            if not dav.success: continue
            
            # Compare DAV vs EGARCH (The real test)
            improvement = egarch.bic - dav.bic
            
            interp = interpret_coefficients(dav.params['delta1'], dav.params['delta2'])
            safe_name = cat.replace(">", "").replace(" ", "").replace("/", "")[:30]
            
            res_entry = {
                "Ticker": t, "Risk": cat, "Safe_Name": safe_name,
                "GARCH_BIC": garch.bic, "GARCH_MSE": garch.mse,
                "EGARCH_BIC": egarch.bic, "EGARCH_MSE": egarch.mse,
                "DAV_BIC": dav.bic, "DAV_MSE": dav.mse,
                "DAV_BIC_Imp": improvement, # Improvement over Control
                "Interpretation": interp,
                "Params": dav.params
            }
            all_results.append(res_entry)
            
            if improvement > best_imp:
                best_imp = improvement
                best_dav_res = (dav, cat, safe_name)

        # Plot Winner
        if best_dav_res:
            dav_model, cat, safe_name = best_dav_res
            plt.figure(figsize=(12, 6))
            plt.plot(dates, np.sqrt(garch.variance)*np.sqrt(252), label="GARCH", color="gray", alpha=0.5, linestyle="--")
            plt.plot(dates, np.sqrt(egarch.variance)*np.sqrt(252), label="EGARCH (Control)", color="blue", alpha=0.6)
            plt.plot(dates, np.sqrt(dav_model.variance)*np.sqrt(252), label=f"DAV ({cat})", color="#d62728", linewidth=1.5)
            plt.title(f"{t}: Best Risk Factor = {cat}\nDAV vs EGARCH BIC Improvement: {best_imp:.2f}")
            plt.legend()
            plt.grid(True, alpha=0.3)
            os.makedirs(OUTDIR, exist_ok=True)
            plt.savefig(os.path.join(OUTDIR, f"{t}_{safe_name}.png"))
            plt.close()

    os.makedirs(OUTDIR, exist_ok=True)
    pd.DataFrame(all_results).to_csv(os.path.join(OUTDIR, "benchmark_metrics.csv"), index=False)
    generate_report(all_results)
    print(f"\n✅ Benchmark Complete. Report: {os.path.join(OUTDIR, 'benchmark_report.html')}")

if __name__ == "__main__":
    main()