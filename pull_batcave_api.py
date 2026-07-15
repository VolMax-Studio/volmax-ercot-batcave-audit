"""
pull_batcave_api.py — Fetch 60-day SCED telemetry for BATCAVE_ESR1 from Grid Status API
===================================================================================
Uses GRIDSTATUS_API_KEY from .env.
Formats the outputs exactly like the raw ERCOT MIS extraction, enabling
offline audit verification.
"""

import os
import sys
import json
import hashlib
import datetime
from pathlib import Path
import pandas as pd
import requests
from dotenv import load_dotenv

RESOURCE_NAME = "BATCAVE_ESR1"
BASE_DIR = Path(__file__).parent
RAW_DATA_DIR = BASE_DIR / "audits" / "US-TX-BATC-001" / "raw_data"
MANIFEST_PATH = BASE_DIR / "audits" / "US-TX-BATC-001" / "data_manifest.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    load_dotenv(BASE_DIR / ".env")
    api_key = os.getenv("GRIDSTATUS_API_KEY")
    if not api_key:
        print("Error: GRIDSTATUS_API_KEY not found in .env")
        sys.exit(1)

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Determine the latest operating day from Grid Status API
    print("Fetching latest data from Grid Status API to determine operating window...")
    url = "https://api.gridstatus.io/v1/datasets/ercot_sced_esr_60_day/query"
    params = {
        "api_key": api_key,
        "filter_column": "resource_name",
        "filter_value": RESOURCE_NAME,
        "limit": 1,
        "sort_column": "sced_timestamp_utc",
        "sort_order": "desc",
        "return_format": "json"
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        latest_data = resp.json().get("data", [])
    except Exception as e:
        print(f"Error connecting to Grid Status API: {e}")
        sys.exit(1)

    if not latest_data:
        print("Error: No data returned from Grid Status API.")
        sys.exit(1)

    latest_ts = pd.to_datetime(latest_data[0]["sced_timestamp_utc"])
    latest_op_date = latest_ts.tz_convert("America/Chicago").date()
    
    # 60-day operating window ending at latest_op_date
    window_end = latest_op_date
    window_start = window_end - datetime.timedelta(days=59)
    print(f"Latest SCED timestamp: {latest_ts}")
    print(f"Audit Operating Window: {window_start} to {window_end} (60 days)")

    # Prepare manifest
    manifest = {
        "protocol": "P10 v1.1",
        "audit_id": "US-TX-BATC-001",
        "resource_name": RESOURCE_NAME,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "pulled_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "reproducibility_class": "Class A (Fully Reproducible)",
        "files": [],
        "total_rows": 0
    }

    # Fetch all days
    print(f"Fetching all 60 days from Grid Status API...")
    
    # Query in chunks of 15 days to avoid timeout and limit limits
    chunk_size = 15
    all_data = []
    
    for start_idx in range(0, 60, chunk_size):
        chunk_start = window_start + datetime.timedelta(days=start_idx)
        chunk_end = min(window_start + datetime.timedelta(days=start_idx + chunk_size - 1), window_end)
        
        # Grid Status API filter times in UTC (use wide bounds to cover central time day)
        start_time_utc = (datetime.datetime.combine(chunk_start, datetime.time.min) - datetime.timedelta(days=1)).isoformat() + "Z"
        end_time_utc = (datetime.datetime.combine(chunk_end, datetime.time.max) + datetime.timedelta(days=1)).isoformat() + "Z"
        
        print(f"  Querying chunk: {chunk_start} to {chunk_end}...")
        
        params = {
            "api_key": api_key,
            "filter_column": "resource_name",
            "filter_value": RESOURCE_NAME,
            "start_time": start_time_utc,
            "end_time": end_time_utc,
            "limit": 10000,
            "return_format": "json"
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            chunk_data = resp.json().get("data", [])
            all_data.extend(chunk_data)
            print(f"    Received {len(chunk_data)} records.")
        except Exception as e:
            print(f"Error fetching chunk: {e}")
            sys.exit(1)

    df_all = pd.DataFrame(all_data)
    
    # Normalize timestamp and sort
    df_all["sced_timestamp_utc"] = pd.to_datetime(df_all["sced_timestamp_utc"])
    df_all = df_all.sort_values("sced_timestamp_utc").drop_duplicates(subset=["sced_timestamp_utc"]).reset_index(drop=True)
    
    # Convert timestamps back to string ISO format
    df_all["sced_timestamp_utc_str"] = df_all["sced_timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Map columns to target schema
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
    
    # Group by operating date in America/Chicago timezone
    df_all["operating_date"] = df_all["sced_timestamp_utc"].dt.tz_convert("America/Chicago").dt.date
    
    # Save daily CSV files
    total_rows = 0
    for i in range(60):
        op_date = window_start + datetime.timedelta(days=i)
        report_date = op_date + datetime.timedelta(days=60)
        
        df_day = df_all[df_all["operating_date"] == op_date].copy()
        if df_day.empty:
            print(f"Warning: No data found for operating date {op_date}")
            continue
            
        # Format df_day to match target schema
        df_day["sced_timestamp_utc"] = df_day["sced_timestamp_utc_str"]
        df_day = df_day[target_fields].sort_values("sced_timestamp_utc").reset_index(drop=True)
        
        out_filename = f"BATC_ESR1_SCED_{op_date.isoformat()}.csv"
        out_path = RAW_DATA_DIR / out_filename
        df_day.to_csv(out_path, index=False)
        
        sha = sha256_file(out_path)
        manifest["files"].append({
            "operating_date": op_date.isoformat(),
            "report_date": report_date.isoformat(),
            "raw_zip_filename": f"ext.00013052.0000000000000000.{report_date.strftime('%Y%m%d')}.60_Day_SCED_Disclosure.zip",
            "filtered_csv_filename": out_filename,
            "sha256": sha,
            "row_count": len(df_day)
        })
        total_rows += len(df_day)
        
    manifest["total_rows"] = total_rows
    
    # Save manifest
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"\n✅ Ingestion completed. Total rows filtered: {total_rows}")
    print(f"Manifest written to {MANIFEST_PATH}")

if __name__ == "__main__":
    main()
