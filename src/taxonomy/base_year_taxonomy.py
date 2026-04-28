"""
Base Year Taxonomy Builder (Strict Structure)
---------------------------------------------
Objective: 
 1. 20 Strategic Macro Themes (Fixed).
 2. Max 6 Meso Sub-themes per Macro (Dynamic).
 3. Clean, high-level business taxonomy.

"""

import pandas as pd
import numpy as np
import json
import time
import re
import os
import openai
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans

# ==========================================
# 1. CONFIGURATION
# ==========================================

PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
INPUT_FILE = os.getenv(
    "FYP_MASTER_RISK_CSV",
    os.path.join(PROJECT_ROOT, "data", "interim", "model_input", "all_risk_factors_master.csv"),
)
OUTPUT_JSON = os.getenv(
    "FYP_TAXONOMY_JSON",
    os.path.join(PROJECT_ROOT, "data", "interim", "taxonomy", "taxonomy_base.json"),
)
OUTPUT_CSV = os.getenv(
    "FYP_TAXONOMY_CSV",
    os.path.join(PROJECT_ROOT, "data", "interim", "taxonomy", "hierarchical_risk_categories.csv"),
)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Structure Tuning
TARGET_MACRO_CLUSTERS = 20      # Exactly 20 Macro Themes
MAX_MESO_CLUSTERS = 6           # Max 6 Sub-themes per Macro
MIN_ITEMS_FOR_MESO = 15         # Don't split if Macro has < 15 items

os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def clean_taxonomy_text(text):
    if not isinstance(text, str): return text
    text = re.sub(r"\*\*|__", "", text)
    text = text.strip(" -:–\n\t")
    text = re.sub(r"\s{2,}", " ", text)
    if len(text) > 1: text = text[0].upper() + text[1:]
    return text

def parse_llm_output(response):
    name, definition = "Unknown", "N/A"
    if not response or not isinstance(response, str): return name, definition

    name_match = re.search(r"(Category\s*Name|Category|Subcategory)\s*:\s*(.+)", response, re.IGNORECASE)
    def_match = re.search(r"(Definition|Description)\s*:\s*(.+)", response, re.IGNORECASE)

    if name_match: name = name_match.group(2).strip()
    if def_match: definition = def_match.group(2).strip()
    
    # Fallback
    if name == "Unknown" and response:
        lines = response.split('\n')
        name = lines[0].replace("Category Name:", "").strip()[:80]

    return clean_taxonomy_text(name), clean_taxonomy_text(definition)

def llm_summarize_category(texts, level, parent_name=None, client=None, max_retries=4):
    """
    Added Exponential Backoff to handle API rate limits without skipping clusters.
    """
    sampled = "\n\n".join(np.random.choice(texts, min(8, len(texts)), replace=False))
    
    if level == "macro":
        prompt = f"""Analyze these risk factors and identify the single HIGH-LEVEL strategic theme (e.g. 'Cybersecurity', 'Market Risk', 'Supply Chain').
        
        Examples:
        {sampled}

        Return format:
        Category Name: [2-4 word Title]
        Definition: [1 sentence description]"""
    else:
        prompt = f"""Parent Category: "{parent_name}"
        These are specific risks within '{parent_name}'. Identify the specific sub-theme that binds them.
        
        Examples:
        {sampled}

        Return format:
        Subcategory: [Specific Name]
        Definition: [1 sentence description]"""

    # Retry Loop for API Limits
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                timeout=45
            )
            return completion.choices[0].message.content
        except Exception as e:
            wait_time = 5 * (2 ** attempt) # Waits 5s, 10s, 20s, 40s...
            print(f"    ⚠️ LLM Error (Attempt {attempt+1}/{max_retries}): {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            
    return "" # Returns empty only if all retries fail

# ==========================================
# 3. MAIN PIPELINE
# ==========================================

def main():
    print(f"🚀 Starting Strict Taxonomy Build ({TARGET_MACRO_CLUSTERS} Macros, Max {MAX_MESO_CLUSTERS} Mesos)...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    if not DEEPSEEK_API_KEY:
        print("❌ DEEPSEEK_API_KEY is not set. Export it before running taxonomy construction.")
        return

    # FIX: Load all data and reset the index to prevent alignment issues later
    df = pd.read_csv(INPUT_FILE)
    df = df.reset_index(drop=True) 
    
    if df.empty:
        print("❌ Dataset is empty. Check your CSV.")
        return

    print(f"   Loaded {len(df)} total risk factors across all years.")
    
    print("   Generating embeddings (This may take a moment for large datasets)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    texts = df['full_text'].fillna("").tolist()
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # --- LEVEL 1: MACRO CLUSTERING ---
    print(f"\n🌍 Clustering into {TARGET_MACRO_CLUSTERS} Macro Categories...")
    kmeans_macro = KMeans(n_clusters=TARGET_MACRO_CLUSTERS, random_state=42, n_init=10)
    macro_labels = kmeans_macro.fit_predict(embeddings)
    df['macro_cluster'] = macro_labels
    
    client = openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    
    taxonomy = {
        "macro_categories": [], 
        "meso_categories": [], 
        "metadata": {"base_year": "ALL", "model": "all-MiniLM-L6-v2"}
    }

    unique_macros = sorted(set(macro_labels))
    
    for m_id in unique_macros:
        indices = np.where(macro_labels == m_id)[0]
        cluster_texts = np.array(texts)[indices].tolist()
        
        # Name Macro
        summary = llm_summarize_category(cluster_texts, "macro", client=client)
        name, definition = parse_llm_output(summary)
        centroid = np.mean(embeddings[indices], axis=0).tolist()
        
        taxonomy["macro_categories"].append({
            "id": int(m_id),
            "name": name,
            "definition": definition,
            "size": len(cluster_texts),
            "centroid": centroid
        })
        
        # Assign back to dataframe using integer indexing safely
        df.loc[indices, "macro_category_name"] = name
        print(f"   🔹 Macro {m_id+1}: {name} ({len(cluster_texts)} items)")
        
        # --- LEVEL 2: MESO CLUSTERING (Strict K-Means) ---
        count = len(indices)
        
        if count < MIN_ITEMS_FOR_MESO:
            n_meso = 1
        else:
            n_meso = min(MAX_MESO_CLUSTERS, max(2, count // 25))
            
        sub_embeddings = embeddings[indices]
        
        kmeans_meso = KMeans(n_clusters=n_meso, random_state=42, n_init=10)
        meso_labels = kmeans_meso.fit_predict(sub_embeddings)
        
        for ms_id in range(n_meso):
            local_indices = np.where(meso_labels == ms_id)[0]
            global_indices = indices[local_indices]
            
            meso_texts = np.array(texts)[global_indices].tolist()
            if not meso_texts: continue

            summary_meso = llm_summarize_category(meso_texts, "meso", parent_name=name, client=client)
            ms_name, ms_def = parse_llm_output(summary_meso)
            ms_centroid = np.mean(embeddings[global_indices], axis=0).tolist()
            
            taxonomy["meso_categories"].append({
                "id": f"{m_id}_{ms_id}",
                "parent_macro": name,
                "name": ms_name,
                "definition": ms_def,
                "size": len(meso_texts),
                "centroid": ms_centroid
            })
            
            df.loc[global_indices, "meso_category_name"] = ms_name
            print(f"      └─ Meso ({len(meso_texts)}): {ms_name}")
            
            # Rate limit buffer
            time.sleep(0.5)

    # Save
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(taxonomy, f, indent=2, ensure_ascii=False)
        
    df.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n✅ Taxonomy Complete.")
    print(f"   Saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
