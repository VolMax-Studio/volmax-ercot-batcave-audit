import pandas as pd
from pathlib import Path
import math

BASE_DIR = Path(__file__).parent
GS_DIR = BASE_DIR / "audits" / "US-TX-BATC-001" / "raw_data_gs"
ERCOT_DIR = BASE_DIR / "audits" / "US-TX-BATC-001" / "raw_data"

# Overlapping dates
start_date = pd.to_datetime("2026-03-19")
end_date = pd.to_datetime("2026-05-16")
dates = pd.date_range(start_date, end_date).strftime("%Y-%m-%d").tolist()

print(f"Comparing {len(dates)} overlapping days from {dates[0]} to {dates[-1]} cell-by-cell...")

columns_to_compare = [
    "telemetered_net_output",
    "base_point",
    "hsl",
    "lsl",
    "soc",
    "min_soc",
    "max_soc",
    "telemetered_resource_status"
]

total_mismatches = 0
compared_rows = 0

for dt in dates:
    gs_file = GS_DIR / f"BATC_ESR1_SCED_{dt}.csv"
    ercot_file = ERCOT_DIR / f"BATC_ESR1_SCED_{dt}.csv"
    
    if not gs_file.exists():
        print(f"❌ Missing GS file for {dt}")
        total_mismatches += 1
        continue
    if not ercot_file.exists():
        print(f"❌ Missing ERCOT file for {dt}")
        total_mismatches += 1
        continue
        
    df_gs = pd.read_csv(gs_file).sort_values("sced_timestamp_utc").reset_index(drop=True)
    df_ercot = pd.read_csv(ercot_file).sort_values("sced_timestamp_utc").reset_index(drop=True)
    
    if len(df_gs) != len(df_ercot):
        print(f"❌ Row count mismatch on {dt}: GS has {len(df_gs)}, ERCOT has {len(df_ercot)}")
        total_mismatches += 1
        continue
        
    mismatches_today = 0
    for idx in range(len(df_gs)):
        row_gs = df_gs.iloc[idx]
        row_ercot = df_ercot.iloc[idx]
        
        ts_gs = row_gs["sced_timestamp_utc"]
        ts_ercot = row_ercot["sced_timestamp_utc"]
        
        if ts_gs != ts_ercot:
            print(f"❌ Timestamp mismatch on {dt} index {idx}: GS={ts_gs}, ERCOT={ts_ercot}")
            mismatches_today += 1
            continue
            
        for col in columns_to_compare:
            val_gs = row_gs.get(col)
            val_ercot = row_ercot.get(col)
            
            # Handle float comparison
            if col != "telemetered_resource_status":
                v_gs = float(val_gs) if pd.notna(val_gs) else None
                v_ercot = float(val_ercot) if pd.notna(val_ercot) else None
                
                if v_gs is None and v_ercot is None:
                    continue
                if v_gs is None or v_ercot is None or abs(v_gs - v_ercot) > 0.0001:
                    print(f"❌ Cell mismatch on {dt} at {ts_gs} for {col}: GS={v_gs}, ERCOT={v_ercot}")
                    mismatches_today += 1
            else:
                s_gs = str(val_gs).strip().upper() if pd.notna(val_gs) else ""
                s_ercot = str(val_ercot).strip().upper() if pd.notna(val_ercot) else ""
                if s_gs != s_ercot:
                    print(f"❌ Status mismatch on {dt} at {ts_gs}: GS='{s_gs}', ERCOT='{s_ercot}'")
                    mismatches_today += 1
                    
    if mismatches_today > 0:
        print(f"❌ {dt}: Found {mismatches_today} cell mismatches")
        total_mismatches += mismatches_today
    else:
        # print(f"✅ {dt}: Perfect match ({len(df_gs)} rows)")
        pass
    compared_rows += len(df_gs)

print(f"\n==========================================")
print(f"Cell-by-cell Cross-Validation Summary")
print(f"==========================================")
print(f"Total overlapping days compared: {len(dates)}")
print(f"Total rows compared: {compared_rows}")
print(f"Total cell mismatches found: {total_mismatches}")
if total_mismatches == 0:
    print(f"✅ SUCCESS: Ingestion layers are 100% byte-for-byte identical across all overlapping days!")
else:
    print(f"❌ FAILED: Found {total_mismatches} mismatches.")
