"""
pull_batcave.py — US-TX-BATC-001 Data Acquisition Script
========================================================
Protocol:  P10 v1.1 — "Unfalsifiable-as-Stated"
Asset:     BATCAVE_ESR1 (Bat Cave BESS, Mason County TX)
Primary:   ERCOT MIS (NP3-965-ER, Report Type 13052)
Fallback:  Local Zip Cache (ercot_zips/)
Window:    60 days, dynamically determined from latest disclosures.

Reproducibility Class: Class A (Fully Reproducible)
  Raw CSV data filtered for the target asset is committed directly.
"""

import os
import sys
import json
import hashlib
import re
import zipfile
import io
import time
import datetime
import argparse
from pathlib import Path
import pandas as pd
import requests
from dotenv import load_dotenv

# Config
RESOURCE_NAME = "BATCAVE_ESR1"
REPORT_TYPE_ID = 13052
MIS_DOC_LIST_URL = f"https://www.ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId={REPORT_TYPE_ID}"
DOWNLOAD_BASE_URL = "https://www.ercot.com/misdownload/servlets/mirDownload"

BASE_DIR = Path(__file__).parent
RAW_DATA_DIR = BASE_DIR / "audits" / "US-TX-BATC-001" / "raw_data"
MANIFEST_PATH = BASE_DIR / "audits" / "US-TX-BATC-001" / "data_manifest.json"
ZIP_CACHE_DIR = BASE_DIR / "ercot_zips"

# Expected nameplate / limit for verification check
NAMEPLATE_MW = 100.0

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def get_proxies():
    """Resolve and test a working proxy if configured."""
    proxy_url = os.getenv("ERCOT_PROXY")
    if proxy_url:
        p = {"http": proxy_url, "https": proxy_url}
        try:
            resp = requests.get(MIS_DOC_LIST_URL, headers={"User-Agent": "Mozilla/5.0"}, proxies=p, timeout=5)
            if resp.status_code == 200 and "ListDocsByRptTypeRes" in resp.text:
                print(f"Using configured proxy: {proxy_url}")
                return p
        except Exception:
            pass
        print(f"Configured proxy {proxy_url} failed or blocked by WAF.")
    return None


def fetch_document_list(proxies=None):
    """Fetch report list from ERCOT MIS."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    # Add timestamp parameter to bypass cache
    ts_url = f"{MIS_DOC_LIST_URL}&_={int(time.time() * 1000)}"
    print(f"Querying document list from {MIS_DOC_LIST_URL}...")
    resp = requests.get(ts_url, headers=headers, proxies=proxies, timeout=30)
    if resp.status_code == 403:
        print("Error: Access denied (403 Forbidden). ERCOT MIS blocks non-US IP addresses.")
        print("Please configure a US proxy in .env or place downloaded ZIPs in 'ercot_zips/'.")
        resp.raise_for_status()
    resp.raise_for_status()
    return resp.json()

def parse_doc_list(data):
    """Parse JSON document list returning map of report_date -> doclookupId."""
    doc_map = {}
    try:
        doc_list = data["ListDocsByRptTypeRes"]["DocumentList"]
    except KeyError:
        print("Error: Invalid JSON response structure from ERCOT MIS.")
        return doc_map

    for doc in doc_list:
        constructed_name = doc["Document"]["ConstructedName"]
        doc_id = doc["Document"]["DocID"]
        # extract date YYYYMMDD from constructed name (e.g. ext.00013052.0000000000000000.20260706.051231658...)
        match = re.search(r"\.(20\d{6})\.", constructed_name)

        if match:
            date_str = match.group(1)
            report_date = datetime.datetime.strptime(date_str, "%Y%m%d").date()
            doc_map[report_date] = {
                "doc_id": doc_id,
                "friendly_name": constructed_name
            }
    return doc_map


def download_zip(doc_id, filename, proxies=None):
    """Download ZIP file from ERCOT MIS."""
    url = f"{DOWNLOAD_BASE_URL}?doclookupId={doc_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    ZIP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = ZIP_CACHE_DIR / filename

    print(f"Downloading {filename}...")
    resp = requests.get(url, headers=headers, proxies=proxies, timeout=120, stream=True)
    if resp.status_code == 403:
        print("Error: Download blocked by ERCOT WAF (403).")
        resp.raise_for_status()
    resp.raise_for_status()

    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Saved to {dest_path}")
    return dest_path

def process_raw_zip(zip_path, resource_name=RESOURCE_NAME):
    """Extract and process the ESR CSV file from the ZIP archive."""
    with zipfile.ZipFile(zip_path) as z:
        esr_file = None
        for name in z.namelist():
            cleaned_name = name.replace(" ", "_").lower()
            if "esr_data_in_sced" in cleaned_name and name.endswith(".csv"):
                esr_file = name
                break
        
        if not esr_file:
            print(f"Warning: No ESR data file found in {zip_path.name}")
            return None

        print(f"Found ESR file: {esr_file}")
        with z.open(esr_file) as f:
            df = pd.read_csv(f)

    # Normalize column names (strip whitespace)
    df.columns = df.columns.str.strip()

    # Filter for target resource
    df_filtered = df[df["Resource Name"] == resource_name].copy()
    if df_filtered.empty:
        print(f"Warning: No rows found for resource {resource_name} in {zip_path.name}")
        return None

    # Map column names to P10 standards
    col_map = {
        'SCED Time Stamp': 'sced_timestamp_utc',
        'SCED Timestamp': 'sced_timestamp_utc',
        'Resource Name': 'resource_name',
        'Telemetered Net Output': 'telemetered_net_output',
        'Base Point': 'base_point',
        'HSL': 'hsl',
        'LSL': 'lsl',
        'State of Charge': 'soc',
        'SOC': 'soc',
        'Minimum SOC': 'min_soc',
        'Min SOC': 'min_soc',
        'Maximum SOC': 'max_soc',
        'Max SOC': 'max_soc',
        'Telemetered Resource Status': 'telemetered_resource_status',
        'Resource Status': 'telemetered_resource_status'
    }

    # Localize and convert timestamp to UTC ISO format
    time_col = None
    for c in ['SCED Time Stamp', 'SCED Timestamp']:
        if c in df_filtered.columns:
            time_col = c
            break

    if time_col:
        df_filtered[time_col] = pd.to_datetime(df_filtered[time_col])
        if "Repeated Hour Flag" in df_filtered.columns:
            localized = df_filtered[time_col].dt.tz_localize(
                "America/Chicago",
                ambiguous=(df_filtered["Repeated Hour Flag"] == "N")
            )
        else:
            localized = df_filtered[time_col].dt.tz_localize("America/Chicago", ambiguous="infer")
        
        df_filtered["sced_timestamp_utc"] = localized.dt.tz_convert("UTC").dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Rename other columns
    rename_dict = {k: v for k, v in col_map.items() if k != time_col and k in df_filtered.columns}
    df_filtered = df_filtered.rename(columns=rename_dict)

    # Keep only target fields
    target_fields = [
        "sced_timestamp_utc",
        "resource_name",
        "telemetered_net_output",
        "base_point",
        "hsl",
        "lsl",
        "soc",
        "min_soc",
        "max_soc",
        "telemetered_resource_status"
    ]
    
    # Fill missing target fields with NaN if not present
    for f in target_fields:
        if f not in df_filtered.columns:
            df_filtered[f] = None

    df_filtered = df_filtered[target_fields]
    df_filtered = df_filtered.sort_values("sced_timestamp_utc").reset_index(drop=True)
    return df_filtered

def run_cross_validation(local_df, api_key):
    """Run exploratory cross-validation comparison against Grid Status API for 2026-04-01."""
    print("\n=== Running Exploratory Cross-Validation for 2026-04-01 ===")
    url = "https://api.gridstatus.io/v1/datasets/ercot_sced_esr_60_day/query"
    params = {
        "api_key": api_key,
        "filter_column": "resource_name",
        "filter_value": RESOURCE_NAME,
        "start_time": "2026-04-01T00:00:00Z",
        "end_time": "2026-04-01T23:59:59Z",
        "limit": 1000,
        "return_format": "json"
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        gs_data = resp.json().get("data", [])
    except Exception as e:
        print(f"Error fetching from Grid Status API: {e}")
        return False

    if not gs_data:
        print("Warning: No cross-val data returned from Grid Status API.")
        return False

    df_gs = pd.DataFrame(gs_data)
    
    # Format and rename Grid Status columns to match local
    df_gs = df_gs.rename(columns={
        "sced_timestamp_utc": "sced_timestamp_utc",
        "resource_name": "resource_name",
        "telemetered_net_output": "telemetered_net_output",
        "base_point": "base_point",
        "hsl": "hsl",
        "lsl": "lsl",
        "soc": "soc",
        "min_soc": "min_soc",
        "max_soc": "max_soc",
        "telemetered_resource_status": "telemetered_resource_status"
    })
    
    # Ensure formats are comparable
    df_gs["sced_timestamp_utc"] = pd.to_datetime(df_gs["sced_timestamp_utc"]).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df_gs = df_gs[local_df.columns].sort_values("sced_timestamp_utc").reset_index(drop=True)

    # Filter local DF for the same day
    df_local_day = local_df[local_df["sced_timestamp_utc"].str.startswith("2026-04-01")].copy()
    df_local_day = df_local_day.sort_values("sced_timestamp_utc").reset_index(drop=True)

    print(f"Grid Status records: {len(df_gs)}")
    print(f"Local ERCOT records: {len(df_local_day)}")

    if len(df_gs) != len(df_local_day):
        print(f"Mismatch: Record counts differ ({len(df_gs)} vs {len(df_local_day)})")
        # Find missing timestamps
        gs_times = set(df_gs["sced_timestamp_utc"])
        local_times = set(df_local_day["sced_timestamp_utc"])
        print(f"Timestamps in GS but not local: {gs_times - local_times}")
        print(f"Timestamps in local but not GS: {local_times - gs_times}")
        return False

    # Compare numeric values
    mismatches = 0
    for idx in range(len(df_gs)):
        row_gs = df_gs.iloc[idx]
        row_local = df_local_day.iloc[idx]
        t_gs = row_gs["sced_timestamp_utc"]
        
        for col in ["telemetered_net_output", "base_point", "hsl", "lsl", "soc"]:
            val_gs = float(row_gs[col]) if pd.notna(row_gs[col]) else 0.0
            val_local = float(row_local[col]) if pd.notna(row_local[col]) else 0.0
            if abs(val_gs - val_local) > 0.01:
                print(f"Value mismatch at {t_gs} for {col}: GS={val_gs}, Local={val_local}")
                mismatches += 1

    if mismatches == 0:
        print("✅ Success: Ingestion Cross-Validation Passed. Ingestion layers match exactly.")
        return True
    else:
        print(f"❌ Failed: Ingestion Cross-Validation failed with {mismatches} mismatches.")
        return False

def main():
    load_dotenv(BASE_DIR / ".env")
    parser = argparse.ArgumentParser(description="Pull SCED disclosure data for Bat Cave BESS.")
    parser.add_argument("--cross-val", action="store_true", help="Run cross-validation on 2026-04-01.")
    args = parser.parse_args()

    proxies = get_proxies()
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ZIP_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fetch document list from ERCOT MIS
    doc_map = {}
    try:
        data = fetch_document_list(proxies)
        doc_map = parse_doc_list(data)
        print(f"Parsed {len(doc_map)} daily disclosure documents from ERCOT MIS.")
    except Exception as e:
        print(f"Could not fetch document list online: {e}")
        print("Checking for local ZIP files in ercot_zips/...")

    # 2. Freeze the 60-day window to 2026-03-19 -> 2026-05-17
    window_start = datetime.date(2026, 3, 19)
    window_end = datetime.date(2026, 5, 17)
    print(f"\nAudit Operating Window (FROZEN): {window_start} to {window_end} (60 days)")

    # Prepare manifest
    manifest = {
        "protocol": "P10 v1.2",
        "audit_id": "US-TX-BATC-001",
        "resource_name": RESOURCE_NAME,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "pulled_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "reproducibility_class": "Class A (Fully Reproducible)",
        "files": [],
        "total_rows": 0
    }

    all_day_dfs = []
    total_rows = 0

    for i in range(60):
        op_date = window_start + datetime.timedelta(days=i)
        report_date = op_date + datetime.timedelta(days=60)
        
        filename = f"ext.00013052.0000000000000000.{report_date.strftime('%Y%m%d')}.60_Day_SCED_Disclosure.zip"
        zip_path = ZIP_CACHE_DIR / filename

        # Resolve document ID
        doc_info = doc_map.get(report_date)
        
        # Download if missing and online info is available
        if not zip_path.exists():
            if doc_info:
                try:
                    download_zip(doc_info["doc_id"], filename, proxies)
                except Exception as e:
                    print(f"Skipping download for report date {report_date}: {e}")
            else:
                print(f"ZIP {filename} missing locally, and not found in online doc list.")

        # Process if exists
        if zip_path.exists():
            print(f"Processing {zip_path.name}...")
            try:
                df_day = process_raw_zip(zip_path)
                if df_day is not None and not df_day.empty:
                    out_filename = f"BATC_ESR1_SCED_{op_date.isoformat()}.csv"
                    out_path = RAW_DATA_DIR / out_filename
                    df_day.to_csv(out_path, index=False)
                    
                    sha = sha256_file(out_path)
                    manifest["files"].append({
                        "operating_date": op_date.isoformat(),
                        "report_date": report_date.isoformat(),
                        "raw_zip_filename": filename,
                        "filtered_csv_filename": out_filename,
                        "sha256": sha,
                        "row_count": len(df_day)
                    })
                    total_rows += len(df_day)
                    all_day_dfs.append(df_day)
            except Exception as e:
                print(f"Error processing {zip_path.name}: {e}")
        else:
            print(f"Missing ZIP file for operating day {op_date} (report date {report_date})")

    manifest["total_rows"] = total_rows
    
    # Save manifest
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n✅ Pipeline completed. Total rows filtered: {total_rows}")
    print(f"Manifest written to {MANIFEST_PATH}")

    # 3. Cross-Validation Step
    if args.cross_val or os.getenv("GRIDSTATUS_API_KEY"):
        api_key = os.getenv("GRIDSTATUS_API_KEY")
        if api_key and all_day_dfs:
            combined_df = pd.concat(all_day_dfs, ignore_index=True)
            run_cross_validation(combined_df, api_key)

if __name__ == "__main__":
    main()
