import os
import time
import re
from bs4 import BeautifulSoup
import requests
import pandas as pd
from pathlib import Path

# ================= CONFIGURATION =================
PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
OUTPUT_DIR = os.getenv(
    "FYP_RISK_HTML_DIR",
    os.path.join(PROJECT_ROOT, "data", "raw", "risk_factors_output"),
)
# Ensure the directory exists immediately
os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_YEARS = [str(year) for year in range(2006, 2025)]  # 2006 to 2024
EMAIL_ADDRESS = os.getenv("SEC_CONTACT_EMAIL", "your_email@example.com")

# SEC mandates max 10 requests per second.
# We use 0.15 to be safe (approx 6.6 requests per second).
SEC_SLEEP_TIME = float(os.getenv("SEC_SLEEP_TIME", "0.15"))
# =================================================

def generate_live_sp500_cik_mapping() -> dict:
    """
    Dynamically fetches the live S&P 500 constituents and their SEC CIKs.
    Bypasses Wikipedia's 403 Forbidden block via browser spoofing.
    Returns a dictionary mapping {Ticker: '10-Digit CIK'}.
    """
    print("🌐 Fetching live S&P 500 roster from Wikipedia...")
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status() 
    
    sp500_table = pd.read_html(response.text)[0]
    
    mapping = {}
    for _, row in sp500_table.iterrows():
        ticker = row['Symbol']
        # The SEC EDGAR system requires CIKs to be exactly 10 digits, zero-padded
        cik = str(row['CIK']).zfill(10)
        mapping[ticker] = cik
        
    return mapping

def extract_item_1a_linear(raw_html):
    """
    Anchor-Based Extraction (The "Slice" Method).
    Slices the HTML elements between 'Item 1A' and 'Item 1B/2'.
    """
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    # 1. Flatten document into scanable blocks
    # ADDED 'ix:nonnumeric' to support modern iXBRL SEC filings
    all_elements = soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'span', 'b', 'strong', 'td', 'ix:nonnumeric'])
    
    # Regex for Headers
    start_pattern = re.compile(r'^item\s*1a\.?', re.IGNORECASE)
    end_pattern = re.compile(r'^item\s*(1b|2)\.?', re.IGNORECASE)
    
    # 2. Find ALL candidates for the START
    start_candidates = []
    for i, el in enumerate(all_elements):
        text = el.get_text(" ", strip=True).lower()
        if not text: continue
        
        if start_pattern.search(text):
            if len(text) > 60: continue
            if "..." in text: continue
            if re.search(r'\d+$', text): continue
            if "see item" in text: continue
            if "business" in text: continue

            start_candidates.append(i)

    if not start_candidates:
        return None

    # 3. Pick the BEST Start Candidate
    best_content = None
    
    for start_idx in reversed(start_candidates):
        end_idx = None
        
        # Scan forward from this start_idx
        for j in range(start_idx + 1, min(len(all_elements), start_idx + 5000)):
            el = all_elements[j]
            text = el.get_text(" ", strip=True).lower()
            
            if end_pattern.search(text) and len(text) < 60:
                end_idx = j
                break
        
        if end_idx:
            block_elements = all_elements[start_idx : end_idx]
            block_html = "".join([str(e) for e in block_elements])
            
            if len(block_html) > 3000:
                best_content = block_html
                break 
    
    if not best_content:
        # Fallback 1: File ended without a clear Item 1B/2
        last_start = start_candidates[-1]
        fallback_slice = all_elements[last_start:]
        block_html = "".join([str(e) for e in fallback_slice])
        
        if len(block_html) > 3000: 
            # Fallback 2: Truncate if it's the rest of a massive file
            if len(block_html) > 500_000:
                return f"<div class='risk-content'>{block_html[:100000]}... [Truncated for extreme length]</div>"
            return f"<div class='risk-content'>{block_html}</div>"
        
        return None

    return f"<div class='risk-content'>{best_content}</div>"

def main():
    # SEC EDGAR requires a specific User-Agent format: 'Company Name email@address.com'
    sec_headers = {'User-Agent': f'Academic Research {EMAIL_ADDRESS}'}

    if EMAIL_ADDRESS == "your_email@example.com":
        print(
            "⚠️  SEC_CONTACT_EMAIL is not set. Set it before large EDGAR runs, e.g. "
            "export SEC_CONTACT_EMAIL='your.name@example.com'"
        )
    
    # 1. Initialize the Target Universe dynamically
    try:
        companies_dict = generate_live_sp500_cik_mapping()
        print(f"✅ Successfully mapped {len(companies_dict)} S&P 500 companies.")
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Failed to fetch S&P 500 mapping. {e}")
        return # Halt execution safely

    print(f"\n🚀 Starting Extraction for Years: {TARGET_YEARS[0]} - {TARGET_YEARS[-1]}")
    
    # 2. Iterate through the generated dictionary
    for ticker, cik in companies_dict.items():
        print(f"\n--- Processing {ticker} (CIK: {cik}) ---")
        years_found = []
        
        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            
            # STRICT RATE LIMITING: Must pause before hitting the master JSON
            time.sleep(SEC_SLEEP_TIME) 
            
            meta_resp = requests.get(url, headers=sec_headers)
            
            # Handle potential SEC bans or dead CIKs gracefully
            if meta_resp.status_code != 200:
                print(f"    ⚠️ SEC API Error {meta_resp.status_code} for {ticker}. Skipping.")
                continue
                
            filings = meta_resp.json()['filings']['recent']
            
            for i, form in enumerate(filings['form']):
                if form in ['10-K', '10-K405', '10-KT']:
                    
                    report_date = filings.get('reportDate', [])[i]
                    if not report_date: 
                        report_date = filings['filingDate'][i]
                    fiscal_year = report_date.split('-')[0]
                    
                    if fiscal_year in TARGET_YEARS and fiscal_year not in years_found:
                        acc = filings['accessionNumber'][i].replace('-', '')
                        doc = filings['primaryDocument'][i]
                        dl_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
                        
                        filename = f"ITEM1A_RISK_FACTORS_{ticker}_{fiscal_year}.html"
                        save_path = os.path.join(OUTPUT_DIR, filename)
                        
                        if not os.path.exists(save_path):
                            print(f"    📥 Downloading {fiscal_year}...")
                            
                            # STRICT RATE LIMITING: Must pause before downloading the HTML
                            time.sleep(SEC_SLEEP_TIME)
                            
                            raw_resp = requests.get(dl_url, headers=sec_headers)
                            
                            if raw_resp.status_code == 200:
                                risk_html = extract_item_1a_linear(raw_resp.text)
                                
                                if risk_html:
                                    with open(save_path, 'w', encoding='utf-8') as f:
                                        f.write(risk_html)
                                    print(f"    ✅ Saved HTML ({len(risk_html):,} chars)")
                                else:
                                    print(f"    ⚠️  Extraction failed (Could not locate valid Item 1A boundaries).")
                            else:
                                print(f"    ⚠️  Download failed: HTTP {raw_resp.status_code}")
                                
                        else:
                            print(f"    ⏭️  Skipping {fiscal_year} (File already exists)")
                            
                        years_found.append(fiscal_year)
                        
        except Exception as e:
            print(f"    ❌ Error processing {ticker}: {e}")

if __name__ == "__main__":
    main()
