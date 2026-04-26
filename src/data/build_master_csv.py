import os
import glob
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import re
import gc # Added for memory management

# ================= CONFIGURATION =================
PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", os.getcwd())
INPUT_DIR = os.getenv(
    "FYP_RISK_HTML_DIR",
    os.path.join(PROJECT_ROOT, "data", "interim", "risk_factors_output"),
)
OUTPUT_FILE = os.getenv(
    "FYP_MASTER_RISK_CSV",
    os.path.join(PROJECT_ROOT, "data", "processed", "all_risk_factors_master.csv"),
)
# =================================================

def extract_metadata_robust(filename):
    match = re.search(r"ITEM1A_RISK_FACTORS_(.+)_(\d{4})\.html", filename)
    if match:
        return match.group(1), match.group(2)
    return None, None

def is_junk_line(text):
    t = text.lower().strip()
    if len(t) < 2: return True
    artifacts = ["table of contents", "index to financial", "form 10-k", "page", "item 1a", "part i"]
    for art in artifacts:
        if art in t and len(t) < 40: return True
    if t.isdigit(): return True
    return False

def get_style_signature(tag):
    sig = str(tag.name)
    if tag.has_attr('class'): sig += "." + ".".join(sorted(tag['class']))
    if tag.has_attr('style'): sig += "|" + tag['style'].replace(" ", "").lower()
    if tag.name in ['b', 'strong', 'h3', 'h4']: sig += "|bold"
    return sig

def parse_heuristic_two_pass(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    content_div = soup.find('div', class_='risk-content') or soup.body
    if not content_div: 
        soup.decompose() # MEMORY FIX: Destroy the soup object
        return []

    elements = content_div.find_all(['p', 'span', 'div', 'h1', 'h2', 'h3', 'b', 'strong', 'li'])
    
    # PASS 1: Stats
    style_stats = {} 
    valid_elements = []

    for el in elements:
        text = el.get_text(" ", strip=True)
        if not text or is_junk_line(text): continue
        
        valid_elements.append(el)
        sig = get_style_signature(el)
        word_count = len(text.split())
        
        if sig not in style_stats: style_stats[sig] = []
        style_stats[sig].append(word_count)

    style_roles = {}
    for sig, counts in style_stats.items():
        avg = np.mean(counts)
        if avg < 5: style_roles[sig] = "Main Title"
        elif 5 <= avg <= 35: style_roles[sig] = "Sub-Title"
        else: style_roles[sig] = "Text"

    # PASS 2: Extraction
    current_main = "General Risks"
    current_sub = "Overview"
    text_buffer = []
    raw_rows = [] 

    def flush_buffer():
        nonlocal text_buffer
        if text_buffer:
            full_text = " ".join(text_buffer).strip()
            full_text = re.sub(r'\s+', ' ', full_text)
            if len(full_text) > 30:
                raw_rows.append({
                    'Main Title': current_main,
                    'Sub-Title': current_sub,
                    'Paragraph Text': full_text
                })
            text_buffer = []

    for el in valid_elements:
        text = el.get_text(" ", strip=True)
        if is_junk_line(text): continue
        
        sig = get_style_signature(el)
        role = style_roles.get(sig, "Text")

        # Fallback: Explicit Bold is usually a Sub-Title
        if "bold" in sig and role == "Text" and len(text) < 100:
            role = "Sub-Title"

        if role == "Main Title":
            flush_buffer()
            current_main = text
            current_sub = "Overview" 
            
        elif role == "Sub-Title":
            flush_buffer()
            current_sub = text
            
        else:
            text_buffer.append(text)

    flush_buffer() 
    
    # CONTINUOUS NUMBERING
    final_rows = []
    risk_counter = 1  
    
    for row in raw_rows:
        if row['Sub-Title'] == "Overview":
            row['No.'] = 0 
        else:
            row['No.'] = risk_counter
            risk_counter += 1 
        final_rows.append(row)
        
    # MEMORY FIX: Forcibly destroy the massive DOM tree before returning
    soup.decompose()
    
    return final_rows

def main():
    print("🚀 Starting Memory-Optimized CSV Builder (Streaming to Disk)...")
    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    html_files = glob.glob(os.path.join(INPUT_DIR, "*.html"))
    
    print(f"   Found {len(html_files)} files.")

    # MEMORY FIX 1: Define columns and create an empty CSV with just the headers first
    cols = ['Company', 'Year', 'No.', 'Main Title', 'Sub-Title', 'Paragraph Text', 'full_text']
    pd.DataFrame(columns=cols).to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    total_rows = 0

    for i, file_path in enumerate(html_files):
        filename = os.path.basename(file_path)
        ticker, year = extract_metadata_robust(filename)
        
        if not year: continue
        if i % 10 == 0: print(f"   Processing {ticker} {year} ({i}/{len(html_files)})...")
        
        try:
            # 1. Parse just one file
            rows = parse_heuristic_two_pass(file_path)
            
            if not rows:
                continue
                
            # 2. Add metadata
            for row in rows:
                row['Company'] = ticker
                row['Year'] = year
                row['full_text'] = f"{row['Main Title']} | {row['Sub-Title']} | {row['Paragraph Text']}"
                
            # 3. Convert only this small chunk to a DataFrame
            df_chunk = pd.DataFrame(rows)
            for c in cols:
                if c not in df_chunk.columns: df_chunk[c] = ""
            df_chunk = df_chunk[cols]
            
            # Junk Filter applied to the chunk
            df_chunk = df_chunk[~df_chunk['Sub-Title'].str.contains("Table of Contents", case=False, na=False)]
            
            # 4. APPEND to the CSV (mode='a') without writing headers again
            df_chunk.to_csv(OUTPUT_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
            
            total_rows += len(df_chunk)
            
        except Exception as e:
            print(f"    ❌ Error on {filename}: {e}")
            
        # MEMORY FIX 2: Force Python to empty the trash
        del rows
        gc.collect()

    print(f"\n✅ Master CSV Build Complete! Saved to: {OUTPUT_FILE} (Approx {total_rows} rows)")

if __name__ == "__main__":
    main()