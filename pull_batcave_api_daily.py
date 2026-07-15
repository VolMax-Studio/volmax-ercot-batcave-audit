"""
pull_batcave_api_daily.py — Pull 60 days of BATCAVE_ESR1 telemetry from Grid Status API day-by-day
=============================================================================================
"""

import os
import sys
import json
import hashlib
import time
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

    # Operating Window: 2026-03-18 to 2026-05-16 (60 days)
    window_start = datetime.date(2026, 3, 18)
    window_end = datetime.date(2026, 5, 16)
    print(f"Target Audit Operating Window: {window_start} to {window_end} (60 days)")

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

    url = "https://api.gridstatus.io/v1/datasets/ercot_sced_esr_60_day/query"
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

    total_rows = 0

    for i in range(60):
        op_date = window_start + datetime.timedelta(days=i)
        report_date = op_date + datetime.timedelta(days=60)
        
        # Grid Status API parameters: query from 05:00:00 UTC of op_date to 05:00:00 UTC of next day
        # which is exactly 00:00:00 to 24:00:00 America/Chicago time (since DST offsets vary, we can query a bit wider and filter in python)
        start_time_utc = (datetime.datetime.combine(op_date, datetime.time.min) - datetime.timedelta(hours=6)).isoformat() + "Z"
        end_time_utc = (datetime.datetime.combine(op_date, datetime.time.max) + datetime.timedelta(hours=6)).isoformat() + "Z"
        
        print(f"Operating Day {i+1}/60: {op_date} (querying UTC {start_time_utc} to {end_time_utc})...")
        
        params = {
            "api_key": api_key,
            "filter_column": "resource_name",
            "filter_value": RESOURCE_NAME,
            "start_time": start_time_utc,
            "end_time": end_time_utc,
            "limit": 10000,
            "return_format": "json"
        }
        
        # Retry logic for 429 rate limit
        retry_delay = 1.0
        success = False
        data = []
        for attempt in range(5):
            try:
                resp = requests.get(url, params=params, timeout=30)
                if resp.status_code == 429:
                    print(f"    Rate limit hit (429). Retrying in {retry_delay:.1f}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2.0
                    continue
                resp.raise_for_status()
                data = resp.json().get("data", [])
                success = True
                break
            except Exception as e:
                print(f"    Error on attempt {attempt+1}: {e}")
                time.sleep(2.0)
        
        if not success:
            print(f"    Failed to fetch data for operating date {op_date}")
            continue

        if not data:
            print(f"    Warning: No records found for operating date {op_date}")
            continue

        df_day = pd.DataFrame(data)
        
        # Normalize and sort
        df_day["sced_timestamp_utc"] = pd.to_datetime(df_day["sced_timestamp_utc"])
        
        # Filter for America/Chicago operating date
        df_day["operating_date"] = df_day["sced_timestamp_utc"].dt.tz_convert("America/Chicago").dt.date
        df_day_filtered = df_day[df_day["operating_date"] == op_date].copy()
        
        if df_day_filtered.empty:
            print(f"    Warning: No records matched operating date {op_date} after timezone conversion.")
            continue
            
        df_day_filtered["sced_timestamp_utc"] = df_day_filtered["sced_timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        df_day_filtered = df_day_filtered.sort_values("sced_timestamp_utc").drop_duplicates(subset=["sced_timestamp_utc"]).reset_index(drop=True)
        
        # Keep only target fields
        for field in target_fields:
            if field not in df_day_filtered.columns:
                df_day_filtered[field] = None
        df_day_filtered = df_day_filtered[target_fields]
        
        out_filename = f"BATC_ESR1_SCED_{op_date.isoformat()}.csv"
        out_path = RAW_DATA_DIR / out_filename
        df_day_filtered.to_csv(out_path, index=False)
        
        sha = sha256_file(out_path)
        manifest["files"].append({
            "operating_date": op_date.isoformat(),
            "report_date": report_date.isoformat(),
            "raw_zip_filename": f"ext.00013052.0000000000000000.{report_date.strftime('%Y%m%d')}.60_Day_SCED_Disclosure.zip",
            "filtered_csv_filename": out_filename,
            "sha256": sha,
            "row_count": len(df_day_filtered)
        })
        total_rows += len(df_day_filtered)
        print(f"    Saved {len(df_day_filtered)} rows to {out_filename}")
        
        # Pause to avoid rate limits
        time.sleep(0.5)

    manifest["total_rows"] = total_rows
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"\n✅ Ingestion completed. Total rows filtered: {total_rows}")
    print(f"Manifest written to {MANIFEST_PATH}")

if __name__ == "__main__":
    main()
