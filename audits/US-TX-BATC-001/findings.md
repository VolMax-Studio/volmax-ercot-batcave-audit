# US-TX-BATC-001 — Findings

**Generated:** 2026-07-16T21:00:24.309133+00:00  
**Protocol:** P10 v1.2  
**Anchor class:** A (Primary source ERCOT MIS data; fully reproducible)  
**Rows analysed (post-dedup, ON only):** 16,925  

---

## Verdict Summary

| Rule | Claim | Verdict |
|------|-------|---------|
| F1 | 001a — 100 MW power | **Bounded** |
| F2 | 001b — 100 MWh energy | **Not Verified** |
| F3 | SoC internal consistency (separate finding class) | **Inconsistent** |
| F4 | SoC field interpretation | **Deferred** |

---

## F1 — Power Capacity (Claim F1: 100 MW)

- Max observed `telemetered_net_output`: **72.61 MW**
- Max observed `base_point`: **84.5 MW**
- Max observed `hsl`: **100.0 MW**
- ON intervals: 16,925
- Intervals with BP ≥ 83.33 MW (83.33% nameplate): 2
- Not Verified intervals (|TNO−BP| > 7.2 MW at BP ≥ 83.33 MW): **2**
- L2 Anomaly intervals (TNO > 100 MW): **0**

**Verdict:** **Bounded**
> **Note:** The maximum observed output is exactly equal to the High Sustainable Limit (HSL) of 100.0 MW. This indicates the capacity is demonstrated at the SCED model ceiling, meaning the physical asset output is likely model-saturated at this value.

---

## F2 — Energy Capacity (Claim F2: 100 MWh)

- Discharge blocks ≥ 30 min identified: **246**
- Largest block: **58.0 MWh**
- LSL-dispatch intervals (full-charge instruction): **6**
- SoC-enhanced bounded: **True**
- Not Verified events: **243**

**Verdict:** **Not Verified**

---

## F3 — SoC Internal Consistency *(separate finding class)*

> **Caveat:** soc is operator-reported BMS estimate, not independent physical measurement. This test verifies internal consistency of operator telemetry only. Systematic BMS reporting errors would not be detected.

- Evaluable discharge events: **245**
- Consistent events (ratio ∈ [0.85, 1.0]): **3** (1.2%)
- Required: ≥ 80%
- Ratio range: [0.0375, 1.4112], mean=0.6339

**Verdict:** **Inconsistent** *(F3 is a standalone finding — does not modify F1/F2)*

---

## F4 — SoC Field Interpretation

- `max_soc` field observed: **102.95 MWh**
- Max `soc` value observed: **99.18 MWh**
- Unit consistent with MWh scale: **True**

> Observed max_soc = 102.95 MWh. Interpretation of this field (buffer, SCED model limit, or other) requires ERCOT column definitions guide or equivalent DDL. No assumption made. Field used as-reported.

**Verdict:** **Deferred** — pending ERCOT column definitions.

---

## Methodological Notes

- All verdicts rendered from frozen F1–F4 grammar replicated from Anole audit.
- Anchor class A (Primary source ERCOT MIS data; fully reproducible).
- Access to the ERCOT MIS portal was geographically restricted during automated collection.
  To maintain reproducibility, raw filtered CSV files are committed directly to this repository,
  with a direct ZIP cross-check performed on a sample day to ensure ingestion parity.
  Due to Grid Status API Terms of Use, this repository must remain private until licensing clearance is completed.
- F3 is a standalone telemetry consistency evaluation and does not affect the primary verdicts.
- **Protocol Schema:** All verdicts are reported using the original Anole string categories to ensure direct comparability. No mapping to v1.1.1 ledger strings is performed to avoid misleading classifications (such as forcing a Bounded claim with 72.61% peak output into a 'Verified with Limitations' status, or a Not Verified claim into 'Hypothesis Rejected').

*End of findings — proceed to report.md for final audit narrative.*