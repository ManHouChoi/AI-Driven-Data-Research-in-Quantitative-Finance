# update_taxonomy_dynamic.py
"""
Dynamic Taxonomy Evolution System
---------------------------------
Objective: Update the taxonomy with new year's data (e.g., 2025) by detecting
           structural shifts rather than just matching text.

Logic:
 1. Embed new risks.
 2. Identify 'Deviations' (Risks that don't fit existing categories well).
 3. Cluster the Deviations (Find emerging themes).
 4. Consult LLM: "Is this a NEW category, or a DRIFT of an existing one?"
 5. Update Taxonomy (Add new nodes or update existing centroids).

Author: Marco (FYP) - Adapted from Advanced Logic
"""

import pandas as pd
import numpy as np
import json
import time
import re
import os
from pathlib import Path
import umap
import hdbscan
import openai
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# 1. CONFIGURATION
# ==========================================

# Paths. Environment variables allow future-year reruns without editing code.
PROJECT_ROOT = Path(os.getenv("FYP_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
BASE_TAXONOMY_PATH = Path(
    os.getenv(
        "FYP_TAXONOMY_JSON",
        PROJECT_ROOT / "data" / "interim" / "taxonomy" / "taxonomy_base.json",
    )
)
NEW_DATA_PATH = Path(
    os.getenv(
        "FYP_NEW_RISKS_CSV",
        PROJECT_ROOT / "data" / "interim" / "model_input" / "new_risks_2025.csv",
    )
)
OUTPUT_DIR = Path(
    os.getenv(
        "FYP_TAXONOMY_UPDATE_DIR",
        PROJECT_ROOT / "outputs" / "taxonomy" / "updates_2025",
    )
)
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# Tuning
DEVIATION_THRESHOLD = 0.60  # If similarity is below this, it's a "Deviation"
MIN_NEW_THEME_SIZE = 5      # Need at least 5 examples to create a new category
ALPHA_DRIFT = 0.2           # How much a Merge updates the old centroid (20% new, 80% old)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. DATA ENGINE
# ==========================================

def load_and_prep_data(filepath):
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"❌ New data file not found: {filepath}")
        return None

    df = pd.read_csv(filepath)

    # Construct Full Context for Embedding (Matches Base Year Logic)
    # Using 'Main Title' + 'Sub-Title' + 'Paragraph Text' structure
    cols = ['Main Title', 'Sub-Title', 'Paragraph Text']
    for c in cols:
        if c not in df.columns: df[c] = ""

    df['full_text'] = (
        df['Main Title'].astype(str) + " | " +
        df['Sub-Title'].astype(str) + " | " +
        df['Paragraph Text'].astype(str)
    )
    return df

def get_base_centroids(taxonomy):
    """Extracts centroids and names from the JSON taxonomy."""
    ids = []
    names = []
    centroids = []
    definitions = []
    parents = []

    for meso in taxonomy["meso_categories"]:
        ids.append(meso["id"])
        names.append(meso["name"])
        centroids.append(meso["centroid"])
        definitions.append(meso["definition"])
        parents.append(meso.get("parent_macro", "General"))

    return {
        "ids": ids,
        "names": names,
        "centroids": np.array(centroids),
        "definitions": definitions,
        "parents": parents
    }

# ==========================================
# 3. LLM "CONSULTANT"
# ==========================================

def consult_llm_strategy(deviation_samples, closest_matches):
    """
    Shows the LLM the new risk cluster and the closest existing options.
    Asks for a strategic decision: ADD, MERGE, or IGNORE.
    """
    samples_text = "\n- ".join(deviation_samples[:5])
    closest_text = "\n".join([f"- {name} (Similarity: {score:.2f})" for name, score in closest_matches])

    prompt = f"""
    You are a Risk Taxonomy Architect. We detected a cluster of emerging risks in the 2025 financial reports that do not fit our 2022-2024 taxonomy well.

    NEW RISK CLUSTER SAMPLES:
    - {samples_text}

    CLOSEST EXISTING CATEGORIES (for reference):
    {closest_text}

    DECISION REQUIRED:
    Analyze the 'New Risk Cluster'. Does it represent a fundamentally NEW risk concept, or is it just a variation (drift) of an existing category?

    Respond in JSON format:
    {{
        "decision": "ADD" or "MERGE",
        "rationale": "One sentence explanation.",
        "category_name": "Proposed Name (if ADD) or Target Existing Name (if MERGE)",
        "parent_macro": "Proposed Macro Category (e.g. Technology, Market, Legal)"
    }}
    """

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("    ⚠️ DEEPSEEK_API_KEY is not set; using IGNORE fallback for this theme.")
        return {
            "decision": "IGNORE",
            "rationale": "LLM taxonomy consultation skipped because DEEPSEEK_API_KEY is not configured.",
            "category_name": "Unknown",
        }

    try:
        client = openai.OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            timeout=45
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"    ⚠️ LLM Error: {e}")
        # Fallback decision
        return {"decision": "IGNORE", "rationale": "Error", "category_name": "Unknown"}

# ==========================================
# 4. MAIN PIPELINE
# ==========================================

def run_evolution_pipeline():
    print("🚀 Starting Dynamic Taxonomy Evolution (2025)...")

    # 1. LOAD BASE TAXONOMY
    with open(BASE_TAXONOMY_PATH, "r") as f:
        base_taxonomy = json.load(f)

    base_data = get_base_centroids(base_taxonomy)
    print(f"   Loaded Base Taxonomy: {len(base_data['names'])} existing categories.")

    # 2. LOAD NEW DATA
    df_new = load_and_prep_data(NEW_DATA_PATH)
    if df_new is None: return

    print("   Generating Embeddings for new data...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    new_embeddings = model.encode(df_new['full_text'].tolist(), show_progress_bar=True)

    # 3. DETECT DEVIATIONS
    print("\n🔍 Detecting Deviations...")
    # Calculate similarity to ALL existing meso categories
    sim_matrix = cosine_similarity(new_embeddings, base_data["centroids"])

    # Get best match for each row
    best_sims = np.max(sim_matrix, axis=1)
    best_indices = np.argmax(sim_matrix, axis=1)

    # Identify Deviations
    deviation_mask = best_sims < DEVIATION_THRESHOLD
    deviations = df_new[deviation_mask]
    dev_embeddings = new_embeddings[deviation_mask]

    print(f"   Found {len(deviations)} risks ({len(deviations)/len(df_new):.1%}) that deviate from the 2024 baseline.")

    # Track changes
    change_log = []

    # 4. CLUSTER DEVIATIONS (Unsupervised Discovery)
    if len(deviations) >= MIN_NEW_THEME_SIZE:
        print("   🔮 Clustering deviations to find emerging themes...")

        # UMAP reduction for density-based clustering
        umap_reducer = umap.UMAP(n_neighbors=10, min_dist=0.1, n_components=5, random_state=42)
        dev_umap = umap_reducer.fit_transform(dev_embeddings)

        clusterer = hdbscan.HDBSCAN(min_cluster_size=MIN_NEW_THEME_SIZE, min_samples=3)
        dev_labels = clusterer.fit_predict(dev_umap)

        unique_labels = sorted(set(dev_labels))
        if -1 in unique_labels: unique_labels.remove(-1) # Remove noise

        print(f"   --> Discovered {len(unique_labels)} potential new risk themes.")

        # 5. PROCESS EACH EMERGING THEME
        for label in unique_labels:
            indices = np.where(dev_labels == label)[0]
            theme_embeddings = dev_embeddings[indices]
            theme_texts = deviations.iloc[indices]['full_text'].tolist()

            # A. Calculate "Theme Centroid"
            theme_centroid = np.mean(theme_embeddings, axis=0)

            # B. Find closest "Old World" neighbors for context
            # We compare the NEW Theme Centroid to OLD Categories
            sims = cosine_similarity([theme_centroid], base_data["centroids"])[0]
            top_3_idx = np.argsort(sims)[-3:][::-1]
            closest_matches = [(base_data["names"][i], sims[i]) for i in top_3_idx]

            print(f"\n   Analzying Emerging Theme #{label} (Size: {len(indices)})...")

            # C. Ask LLM Strategy
            decision = consult_llm_strategy(theme_texts, closest_matches)

            action = decision.get("decision", "IGNORE").upper()
            target_name = decision.get("category_name", "Unknown")

            print(f"      🤖 Strategy: {action} -> {target_name}")
            print(f"      📝 Rationale: {decision.get('rationale')}")

            # D. EXECUTE STRATEGY
            if action == "ADD":
                # Create new entry
                new_id = f"NEW_2025_{int(time.time())}_{label}"
                base_taxonomy["meso_categories"].append({
                    "id": new_id,
                    "parent_macro": decision.get("parent_macro", "Emerging Risks"),
                    "name": target_name,
                    "definition": decision.get("rationale", "Emerging risk detected in 2025."),
                    "size": len(indices),
                    "centroid": theme_centroid.tolist() # Save mathematical center
                })
                change_log.append({"Action": "ADD", "Category": target_name, "Size": len(indices)})

            elif action == "MERGE":
                # Find the existing category and shift its centroid
                found = False
                for meso in base_taxonomy["meso_categories"]:
                    if meso["name"] == target_name:
                        # MATHEMATICAL EVOLUTION:
                        # New Centroid = (1 - alpha) * Old + (alpha) * New
                        # This allows the category to "drift" towards the new definition
                        old_centroid = np.array(meso["centroid"])
                        new_centroid = ((1 - ALPHA_DRIFT) * old_centroid) + (ALPHA_DRIFT * theme_centroid)

                        meso["centroid"] = new_centroid.tolist()
                        meso["size"] += len(indices)
                        found = True
                        break

                if found:
                    change_log.append({"Action": "MERGE", "Category": target_name, "Size": len(indices)})
                else:
                    print(f"      ⚠️ Merge target '{target_name}' not found. Skipping.")

    # 6. SAVE RESULTS
    updated_json_path = OUTPUT_DIR / "taxonomy_2025_updated.json"
    with open(updated_json_path, "w", encoding="utf-8") as f:
        json.dump(base_taxonomy, f, indent=2, ensure_ascii=False)

    pd.DataFrame(change_log).to_csv(OUTPUT_DIR / "evolution_log.csv", index=False)

    print("\n✅ Evolution Complete.")
    print(f"   Updated Taxonomy: {updated_json_path}")
    print(f"   Changes Detected: {len(change_log)}")

if __name__ == "__main__":
    run_evolution_pipeline()
