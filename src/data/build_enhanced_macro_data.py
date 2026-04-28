import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
import datetime
import os
from pathlib import Path

def fetch_macro_data(start_year=2006, end_year=2024):
    print("Downloading Macroeconomic Data from FRED and Yahoo Finance...")
    
    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"
    
    # 1. Fetch FRED Data (Federal Reserve Economic Data)
    # GS10: 10-Year Treasury, GS2: 2-Year Treasury, BAA: Moody's Baa, AAA: Moody's Aaa, CPIAUCSL: CPI
    fred_series = ['GS10', 'GS2', 'BAA', 'AAA', 'CPIAUCSL']
    fred_data = web.DataReader(fred_series, 'fred', start_date, end_date)
    
    # Resample to Annual averages to match your 10-K data frequency
    annual_fred = fred_data.resample('YE').mean()
    annual_fred['Year'] = annual_fred.index.year
    
    # Calculate Spreads
    annual_fred['Term_Spread'] = annual_fred['GS10'] - annual_fred['GS2']
    annual_fred['Credit_Spread'] = annual_fred['BAA'] - annual_fred['AAA']
    
    # Calculate Inflation YoY
    annual_fred['Inflation_YoY'] = annual_fred['CPIAUCSL'].pct_change() * 100
    
    # 2. Fetch Yahoo Finance Data (VIX and SPY) using the robust Ticker().history() method
    vix_raw = yf.Ticker('^VIX').history(start=start_date, end=end_date)
    spy_raw = yf.Ticker('SPY').history(start=start_date, end=end_date)
    
    # Extract just the Close column
    vix = vix_raw[['Close']].copy()
    spy = spy_raw[['Close']].copy()
    
    # Resample to Annual
    annual_vix = vix.resample('YE').mean().reset_index()
    annual_vix['Year'] = annual_vix['Date'].dt.year
    annual_vix.rename(columns={'Close': 'VIX_Avg'}, inplace=True)
    
    annual_spy = spy.resample('YE').last().reset_index()
    annual_spy['SPY_Return'] = annual_spy['Close'].pct_change()
    annual_spy['Year'] = annual_spy['Date'].dt.year
    
    # 3. Merge Macro Features Together
    macro_df = annual_fred[['Year', 'GS10', 'Term_Spread', 'Credit_Spread', 'Inflation_YoY']].copy()
    macro_df = macro_df.merge(annual_vix[['Year', 'VIX_Avg']], on='Year', how='left')
    macro_df = macro_df.merge(annual_spy[['Year', 'SPY_Return']], on='Year', how='left')
    
    # Fill any missing early years with forward/back fills
    macro_df = macro_df.bfill().ffill()
    return macro_df

def merge_with_fin_data(original_fin_csv_path, output_csv_path):
    print(f"Loading original financial data from: {original_fin_csv_path}")
    fin_df = pd.read_csv(original_fin_csv_path)
    
    # Generate the macro feature panel
    macro_df = fetch_macro_data()
    
    print("Merging macroeconomic features into the cross-sectional panel...")
    # Merge on the 'Year' column so every stock in a given year gets the same macro context
    enhanced_fin_df = fin_df.merge(macro_df, on='Year', how='left')
    
    enhanced_fin_df.to_csv(output_csv_path, index=False)
    print(f"✅ Enhanced dataset saved to: {output_csv_path}")
    print("\nNew Macro Columns Added:")
    print(macro_df.columns.tolist())

if __name__ == "__main__":
    PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))

    INPUT_CSV = os.getenv(
        "FYP_FIN_MATRIX_CSV",
        os.path.join(PROJECT_ROOT, "data", "interim", "scoring_outputs", "fin_data_matrix.csv"),
    )

    OUTPUT_CSV = os.getenv(
        "FYP_FIN_MATRIX_ENHANCED_CSV",
        os.path.join(PROJECT_ROOT, "data", "interim", "scoring_outputs", "fin_data_matrix_enhanced.csv"),
    )

    merge_with_fin_data(INPUT_CSV, OUTPUT_CSV)
