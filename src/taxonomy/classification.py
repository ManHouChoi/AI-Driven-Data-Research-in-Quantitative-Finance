"""
Semantic Classifier (Fast & Robust)
-----------------------------------
Logic:
 1. Loads the Taxonomy (JSON) with Centroids.
 2. Loads the Master CSV (All Risks).
 3. Embeds every risk factor.
 4. Assigns the 'Nearest Neighbor' Macro and Meso category mathematically.
 5. Saves individual files for the Risk Scoring Engine.
"""

import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ================= CONFIGURATION =================
PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
TAXONOMY_PATH = os.getenv(
    "FYP_TAXONOMY_JSON",
    os.path.join(PROJECT_ROOT, "data", "interim", "taxonomy", "taxonomy_base.json"),
)
MASTER_CSV = os.getenv(
    "FYP_MASTER_RISK_CSV",
    os.path.join(PROJECT_ROOT, "data", "interim", "model_input", "all_risk_factors_master.csv"),
)
OUTPUT_DIR = os.getenv(
    "FYP_CLASSIFICATION_OUTPUT_DIR",
    os.path.join(PROJECT_ROOT, "data", "interim", "processed", "classification_outputs"),
)
# =================================================

def load_taxonomy_vectors(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # 1. Macro Centroids
    macro_map = {} # ID -> Name
    macro_vecs = []
    macro_names = []
    
    for m in data['macro_categories']:
        macro_map[m['id']] = m['name']
        macro_vecs.append(m['centroid'])
        macro_names.append(m['name'])
        
    # 2. Meso Centroids (Grouped by Parent Name)
    meso_dict = {} # Parent_Name -> {names: [], vecs: []}
    
    for m in data['meso_categories']:
        parent = m['parent_macro']
        if parent not in meso_dict:
            meso_dict[parent] = {'names': [], 'vecs': []}
        
        meso_dict[parent]['names'].append(m['name'])
        meso_dict[parent]['vecs'].append(m['centroid'])
        
    return np.array(macro_vecs), macro_names, meso_dict

def main():
    print("🚀 Starting Semantic Classification...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(TAXONOMY_PATH):
        raise FileNotFoundError(
            f"Taxonomy JSON not found: {TAXONOMY_PATH}. "
            "Set FYP_TAXONOMY_JSON or run base_year_taxonomy.py first."
        )
    if not os.path.exists(MASTER_CSV):
        raise FileNotFoundError(
            f"Master risk CSV not found: {MASTER_CSV}. "
            "Set FYP_MASTER_RISK_CSV or run build_master_csv.py first."
        )
    
    # 1. Load Data
    print("   Loading Taxonomy...")
    macro_vecs, macro_names, meso_dict = load_taxonomy_vectors(TAXONOMY_PATH)

    if macro_vecs.size == 0 or not macro_names:
        raise ValueError("Taxonomy contains no macro centroids. Rebuild taxonomy_base.json.")
    
    print("   Loading Master CSV...")
    df = pd.read_csv(MASTER_CSV)
    
    # FIX 1: Drop NaNs AND reset the index to prevent NumPy array misalignment
    df = df.dropna(subset=['full_text']).reset_index(drop=True)
    print(f"   Total Risks to Classify: {len(df)}")

    if df.empty:
        print("⚠️  No risk rows with full_text found. Classification skipped.")
        return
    
    # 2. Embed Risks
    print("   Generating Embeddings (This may take a minute)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(df['full_text'].tolist(), show_progress_bar=True)
    
    # 3. Classify Macros (Vectorized)
    print("   Assigning Macro Categories...")
    sim_matrix = cosine_similarity(embeddings, macro_vecs)
    best_macro_idx = np.argmax(sim_matrix, axis=1)
    df['Macro_Category'] = [macro_names[i] for i in best_macro_idx]
    
    # 4. Classify Mesos (Vectorized Batch Processing)
    print("   Assigning Meso Categories...")
    df['Meso_Category'] = "General" # Fallback baseline
    
    # FIX 2: Group by Macro and calculate cosine similarity in matrices, not row-by-row
    for macro_name, group_indices in df.groupby('Macro_Category').groups.items():
        if macro_name in meso_dict:
            # Extract the embeddings specifically for this Macro cluster
            group_embeds = embeddings[group_indices]
            
            # Extract the Meso centroids associated with this Macro
            meso_centroids = meso_dict[macro_name]['vecs']
            meso_names = meso_dict[macro_name]['names']
            
            # Matrix multiplication for cosine similarity (Extremely Fast)
            sub_sims = cosine_similarity(group_embeds, meso_centroids)
            best_sub_idx = np.argmax(sub_sims, axis=1)
            
            # Assign names back to the dataframe using the exact group indices
            assigned_mesos = [meso_names[idx] for idx in best_sub_idx]
            df.loc[group_indices, 'Meso_Category'] = assigned_mesos

    # 5. Save Individual Files
    print("   Saving Output Files...")
    grouped = df.groupby(['Company', 'Year'])
    
    count = 0
    expected_cols = ['Company', 'Year', 'No.', 'Main Title', 'Sub-Title', 'Paragraph Text', 'Macro_Category', 'Meso_Category']
    
    for (ticker, year), group_df in grouped:
        safe_ticker = str(ticker).replace('/', '').upper()
        safe_year = str(year).replace('.0', '')
        
        filename = f"ITEM1A_RISK_FACTORS_{safe_ticker}_{safe_year}_classified.csv"
        path = os.path.join(OUTPUT_DIR, filename)
        
        # FIX 3: Safe column extraction (prevents KeyErrors if raw data is missing 'Sub-Title' etc.)
        out_cols = [c for c in expected_cols if c in group_df.columns]
        group_df[out_cols].to_csv(path, index=False)
        count += 1
        
    print(f"\n✅ Classification Complete.")
    print(f"   Generated {count} classified files in {OUTPUT_DIR}")
    print("   --> Now run risk_scoring.py")

if __name__ == "__main__":
    main()
