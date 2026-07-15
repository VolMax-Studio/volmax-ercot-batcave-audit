import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
METRICS_PATH = BASE_DIR / "audits" / "US-TX-BATC-001" / "metrics.json"

if not METRICS_PATH.exists():
    print(f"❌ Metrics file not found at {METRICS_PATH}")
    exit(1)

with open(METRICS_PATH) as fh:
    m = json.load(fh)

events = m["F3"]["events"]
print(f"Total evaluable events: {len(events)}")

# Stratification Bins
bins = [
    ("< 5 MWh", lambda x: x < 5),
    ("5 - 15 MWh", lambda x: 5 <= x < 15),
    ("15 - 30 MWh", lambda x: 15 <= x < 30),
    ("30 - 50 MWh", lambda x: 30 <= x < 50),
    (">= 50 MWh", lambda x: x >= 50),
]

print("\nTelemetry Ratio Mismatch (Event-Size Stratification):")
print("| Event Size Bin | Event Count | Mean Consistency Ratio | Ratio Range |")
print("| :--- | :---: | :---: | :---: |")

total_count = 0
for label, cond in bins:
    bin_events = [e for e in events if cond(e["mwh"])]
    if bin_events:
        ratios = [e["consistency_ratio"] for e in bin_events]
        mean_ratio = sum(ratios) / len(ratios)
        total_count += len(bin_events)
        print(f"| **{label}** | {len(bin_events)} | **{mean_ratio:.4f}** | [{min(ratios):.4f}, {max(ratios):.4f}] |")

print(f"\nSum of counts: {total_count} / {len(events)}")

# Major events (>= 10 MWh)
major_events = [e for e in events if e["mwh"] >= 10]
consistent_major = [e for e in major_events if 0.85 <= e["consistency_ratio"] <= 1.0]
ratios_major = [e["consistency_ratio"] for e in major_events]

print(f"\nMajor events (>= 10 MWh):")
print(f"- Count: {len(major_events)}")
print(f"- Consistent major: {len(consistent_major)}")
print(f"- Pass Rate: {len(consistent_major)/len(major_events)*100:.2f}% ({len(consistent_major)} out of {len(major_events)})")
print(f"- Mean Consistency Ratio: {sum(ratios_major)/len(major_events):.4f}")
print(f"- Max observed ratio: {max(ratios_major):.4f}")
