# US-TX-BATC-001 — Pre-Registration and L0 Scoping Failures

This document registers a critical methodology failure detected during the execution of the **US-TX-BATC-001** telemetry audit. 

---

## 1. Description of the Failure

In the initial reconnaissance phase (documented in `US-TX-BATC-001_L0_recon.md`), the analyst recorded the following assertion:
> *"while official nameplate capacity is 100 MWh (according to Business Wire press release), maximum telemetered value of soc and max_soc in SCED sample for April 1, 2026, is 76.8 MWh (~23.2% less than nameplate)."*

This incorrect value (76.8 MWh) was subsequently frozen in the pre-registration document (`ZADATAK_prereg_US-TX-BATC-001_v1.md`) as the basis for the **F4 — SoC Field Interpretation** hypothesis framing (testing the "76.8 vs 100 MWh" mismatch).

Upon data acquisition and L1 data processing, the actual telemetry values for April 1, 2026, were found to be:
- Maximum `max_soc`: **102.57 MWh**
- Maximum `soc`: **73.77 MWh**

The number **76.8 MWh** is completely absent from both columns in the raw data for April 1st. It represents a scoping error that leaked through the pre-registration gate into the frozen audit protocol.

---

## 2. Impact on Falsification Findings

Because the framing "76.8 MWh vs 100 MWh" is based on a non-existent telemetry threshold, the pre-registered F4 hypothesis test is void:
- We cannot test the pre-registered hypothesis A (degradation/operational limit) or B (dynamic QSE limit) using the "76.8 MWh" ceiling.
- Any attempt to reformulate F4 around the observed `max_soc` peak of 102.95 MWh and actual `soc` peak of 99.18 MWh is a **post-hoc modification** of the frozen rules.
- Consequently, the F4 analysis comparing these telemetry limits and the systematic 0.63 ratio is classified as **exploratory, not pre-registered**.

---

## 3. Remediation & Protocol Compliance

1. **Protocol Disclosure**: The final audit report (`report.md`) and findings ledger (`findings.md`) must explicitly disclose this pre-scoping failure and state that the F4 hypothesis test was compromised by a scoping error.
2. **Exploratory Status**: The F4 telemetry ratio analysis and any interpretation of the 102.95 MWh max limit are officially relegated to the exploratory section of the report.
3. **Verdict**: The primary F4 verdict remains **Deferred** (pending official ERCOT documentation), ensuring no post-hoc assumptions are used to modify the final audit outcome.
