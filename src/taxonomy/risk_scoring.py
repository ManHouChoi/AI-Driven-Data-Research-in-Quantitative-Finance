# risk_scoring.py
"""
Risk Scoring Engine (Year-by-Year) - Robust Version
---------------------------------------------------
Input: Classified CSVs (e.g., ITEM1A_RISK_FACTORS_AAPL_2023_classified.csv).
Logic: Calculates NDI (Normalized Disclosure Intensity) for each company and year.
Output: Two master CSV matrices indexed by (Ticker, Year).
"""

import pandas as pd
import os
import glob
import numpy as np
import re
from pathlib import Path

# ----- CONFIG -----
PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
INPUT_DIR = os.getenv(
    "FYP_CLASSIFICATION_OUTPUT_DIR",
    os.path.join(PROJECT_ROOT, "data", "interim", "processed", "classification_outputs"),
)
OUTPUT_DIR = os.getenv(
    "FYP_SCORING_OUTPUT_DIR",
    os.path.join(PROJECT_ROOT, "data", "interim", "scoring_outputs"),
)
os.makedirs(OUTPUT_DIR, exist_ok=True)
# ------------------

def parse_filename(filepath):
    """
    Extracts Ticker and Year from filename.
    Matches: ITEM1A_RISK_FACTORS_{Ticker}_{Year}_classified.csv
    """
    filename = os.path.basename(filepath)
    match = re.search(r"ITEM1A_RISK_FACTORS_(.+)_(\d{4})_classified\.csv", filename)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

def load_and_score_file(filepath):
    try:
        df = pd.read_csv(filepath)
        
        # 1. Normalize Columns
        if 'Macro_Category' not in df.columns or 'Meso_Category' not in df.columns:
            print(f"    ⚠️  Missing columns in {os.path.basename(filepath)}")
            return None, None

        # 2. Clean Data (The Correct Way)
        # We perform strings checks, ensuring we don't crash on NaNs
        invalid_tags = ['Unknown', 'Skipped', 'NaN', 'nan', '']
        
        # Create mask on the ORIGINAL dataframe
        mask = (~df['Macro_Category'].astype(str).isin(invalid_tags)) & \
               (~df['Meso_Category'].astype(str).isin(invalid_tags))
        
        clean_df = df[mask].copy()
        
        total_risks = len(clean_df)
        if total_risks == 0:
            # Debug: Print why it's empty
            raw_len = len(df)
            if raw_len > 0:
                print(f"    ⚠️  All {raw_len} rows were 'Unknown' or 'Skipped' in {os.path.basename(filepath)}")
            return None, None

        # 3. Macro Scoring
        macro_counts = clean_df['Macro_Category'].value_counts()
        macro_scores = macro_counts / total_risks

        # 4. Meso Scoring (Combined Key)
        clean_df['Full_Meso_Name'] = clean_df['Macro_Category'] + " -> " + clean_df['Meso_Category']
        meso_counts = clean_df['Full_Meso_Name'].value_counts()
        meso_scores = meso_counts / total_risks
            
        return macro_scores, meso_scores

    except Exception as e:
        print(f"    ❌ Error reading {os.path.basename(filepath)}: {e}")
        return None, None

def main():
    print("🚀 Starting Risk Scoring Pipeline...")
    
    files = glob.glob(os.path.join(INPUT_DIR, "*_classified.csv"))
    print(f"   Found {len(files)} classified files in input directory.")
    
    if len(files) == 0:
        print(f"   ❌ No files found in {INPUT_DIR}.")
        print("      Set FYP_CLASSIFICATION_OUTPUT_DIR or run classification.py first.")
        return

    all_macro_rows = []
    all_meso_rows = []
    
    skipped_files = 0
    processed_files = 0

    for f in files:
        ticker, year = parse_filename(f)
        
        if not ticker: 
            print(f"    ⚠️  Skipped (Regex Mismatch): {os.path.basename(f)}")
            skipped_files += 1
            continue

        macro_s, meso_s = load_and_score_file(f)
        
        if macro_s is not None:
            # Macro Row
            m_row = macro_s.to_dict()
            m_row['Ticker'] = ticker
            m_row['Year'] = year
            all_macro_rows.append(m_row)

            # Meso Row
            ms_row = meso_s.to_dict()
            ms_row['Ticker'] = ticker
            ms_row['Year'] = year
            all_meso_rows.append(ms_row)
            
            processed_files += 1
        else:
            skipped_files += 1

    print(f"\n📊 Processing Summary:")
    print(f"   - Successfully Scored: {processed_files}")
    print(f"   - Skipped / Failed:    {skipped_files}")
    
    if processed_files == 0:
        print("   ❌ No valid data generated. Stopping.")
        return

    # 4. Create Multi-Index DataFrames
    print("   Compiling Master Matrices...")
    
    # Macro Matrix
    df_macro = pd.DataFrame(all_macro_rows)
    df_macro = df_macro.set_index(['Ticker', 'Year']).fillna(0)
    df_macro = df_macro.reindex(sorted(df_macro.columns), axis=1)
    
    # Meso Matrix
    df_meso = pd.DataFrame(all_meso_rows)
    df_meso = df_meso.set_index(['Ticker', 'Year']).fillna(0)
    df_meso = df_meso.reindex(sorted(df_meso.columns), axis=1)

    # 5. Save Outputs
    macro_path = os.path.join(OUTPUT_DIR, "risk_scores_macro_annual.csv")
    meso_path = os.path.join(OUTPUT_DIR, "risk_scores_meso_annual.csv")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_macro.to_csv(macro_path)
    df_meso.to_csv(meso_path)

    print("\n✅ Scoring Complete!")
    print(f"   - Macro Matrix: {macro_path}")
    print(f"   - Meso Matrix:  {meso_path}")
    
    # Quick Check of Dimensions
    print(f"   - Matrix Shape: {df_meso.shape} (Rows x Risk Categories)")

if __name__ == "__main__":
    main()
