# P10 AUDIT REPORT: US-TX-BATC-001
**Asset:** Bat Cave Battery Energy Storage System (BATCAVE_ESR1)  
**Location:** Mason County, Texas, USA  
**Operator:** Developed by Broad Reach Power; acquired by ENGIE in August 2023 (closed Q4 2023); QSE during operating window: Engie Energy Marketing NA (QSUE74)  
**Registered Capacity:** 100.0 MW / 100.0 MWh  
**Audit Protocol:** P10 v1.2  
**Audit Operating Window:** 2026-03-19 to 2026-05-17 (60 days)  
**Anchor/Reproducibility Class:** Class A (Primary source ERCOT MIS data; fully reproducible)  
**Telemetry Records Analyzed:** 17,500 post-deduplication rows  
**Lead Auditor:** Ivan Nestorov (ORCID: [0009-0006-7940-9539](https://orcid.org/0009-0006-7940-9539)), VolMax Studio Lab  

---

## 1. Executive Summary & Verdicts

This audit evaluates the physical capacity claims of the **Bat Cave BESS** in the ERCOT market using primary telemetered disclosure data. The dataset was obtained directly from the ERCOT MIS portal under US network egress, and cross-validated cell-by-cell against the Grid Status API rendering. The audit is classified as **Anchor Class A**.

### Verdict Vocabulary (Version 1.2)
To ensure conceptual correctness and avoid misclassifications, this audit adopts the **P10 v1.2** controlled vocabulary standard, introducing the **`Not Demonstrated`** category. This designates claims that were not physically achieved during the operating window, but were also not disproven or rejected (e.g., because dispatch limits prevented a nameplate test in F1, or the asset's normal SoC telemetry reached 99.18 MWh while full-charge dispatches were followed by discharge blocks capped at 75.54 MWh in F2). This replaces misleading classifications (such as forcing F1 into 'Verified with Limitations' or F2 into 'Hypothesis Rejected').

| Rule | Metric/Claim | Pipeline Verdict | v1.2 Verdict | Finding Narrative |
| :--- | :--- | :--- | :--- | :--- |
| **F1** | 100.0 MW Power Capacity | Bounded | Not Demonstrated | HSL telemetry confirms model capacity at 100.0 MW. Actual physical net output peak reached 72.61 MW, and Base Points reached 84.5 MW. The asset was never dispatched to nameplate capacity. |
| **F2** | 100.0 MWh Energy Capacity | Not Verified | Not Demonstrated | The largest continuous net discharge block was 58.0 MWh. When instructed to fully charge (Base Point <= LSL < 0), the starting SoC of the subsequent discharge blocks never exceeded 75.54 MWh. |
| **F3** | SoC Telemetry Consistency | Inconsistent | Inconsistent | Consistency ratio deviates from naive thermodynamic expectations (mean: 0.6339); physical cause (RTE, parasitic loads) or column schema is undetermined. |
| **F4** | SoC Field Interpretation | Deferred | Deferred | Observed `max_soc` peaked at 102.95 MWh, which is consistent with an MWh scale. The pre-registered hypothesis framing is void due to a scoping error; the verdict is deferred pending official ERCOT column schemas. |

---

## 2. Ingestion, Reproducibility & L1 Integrity

The telemetry data for this audit was acquired directly from the **ERCOT MIS** portal (`pull_batcave.py`) utilizing US network egress. ERCOT MIS portal access requires US IP egress; raw filtered data is archived in this repository, so verification of this audit does not depend on geographic access.
- **Cross-Check Path:** A cell-by-cell cross-validation between the ERCOT direct dataset and the Grid Status API rendering was performed for all 59 overlapping days (2026-03-19 to 2026-05-16). Out of 17,210 compared rows, 0 cell mismatches were found, demonstrating 100% parity across all telemetered output, dispatch, limit, and SoC values.
- **Reproducibility:** Classified as **Class A**. To ensure reproducibility, raw filtered CSV files containing only the target resource telemetry are committed to this repository under `audits/US-TX-BATC-001/raw_data/` along with `data_manifest.json` containing SHA-256 hashes.
- **Terms of Use Constraint:** Because the primary data is obtained directly from ERCOT public disclosures and is fully reproducible, this repository serves as a Class A audit. Grid Status API was used solely for cross-validation.

### L1 Integrity: Column Independence Check
To verify that the SCED database columns `telemetered_net_output` and `base_point` represent independent telemetry streams rather than database copies:
- **Exact float matches (`tno == bp`):** **4 out of 17,500** records (0.02%).
- **Close matches (`abs(tno - bp) < 0.001 MW`):** **506 out of 17,500** records (2.89%).
- **Analysis:** This confirms that the two columns are independent physical and model telemetry streams. The few close matches occur naturally during periods where the BESS tracked its SCED Base Point dispatch instructions closely.

---

## 3. Detailed Findings

### F1 — Power Capacity (Claim: 100.0 MW)
Under P10, a power claim is **Bounded** if the model parameters (`HSL`) are registered at nameplate but physical dispatch limits the peak output:
- **Max Net Output (TNO):** 72.61 MW
- **Max Base Point (BP):** 84.50 MW
- **Max HSL:** 100.00 MW
- **Analysis of 2026-04-08 Intervals:** On **2026-04-08**, at **22:05:19 UTC** and **22:10:20 UTC**, the asset received dispatch instructions of **84.50 MW** and **84.10 MW** respectively under status ON, while telemetered net output during these intervals remained at **-0.39 MW** and **-0.287 MW**.
  - *Subsequent 30-Minute Telemetry:* At 22:15 UTC (BP = 10.78 MW), output was -0.429 MW. At 22:20 UTC (BP = 45.39 MW), output rose to 45.39 MW. At 22:25 UTC (BP = 0.00 MW), output remained at 45.39 MW. At 22:30 UTC (BP = 0.00 MW), output fell back to -0.396 MW. At 22:35 UTC (BP = 24.56 MW), output was -0.437 MW.
  - *Context:* These intervals coincide with a transition from status `ONTEST` (at 22:00 UTC) to status `ON`, and with a discontinuity in the telemetered SoC field (which dropped from 94.79 MWh to 8.91 MWh and then 0.0 MWh, before returning to 83.41 MWh at 22:30 UTC).
  - *Verdict Logic:* Under the verbatim Anole rule, the check `max_bp < NAMEPLATE_MW` is evaluated first. Since the maximum base point (84.50 MW) was less than the 100.0 MW nameplate, the verdict is mechanically set to **Bounded** (leading to the v1.2 verdict of **Not Demonstrated**).
- **Note on Threshold Scaling:** In the original Anole audit (240 MW nameplate), the underperformance threshold was defined as `max(7.2 MW, 3% of nameplate)`. For Bat Cave (100 MW nameplate), scaling the 7.2 MW absolute threshold linearly would yield 3.0 MW. Keeping the unscaled 7.2 MW absolute threshold represents a less sensitive threshold (7.2% of nameplate). For strict consistency with the pre-registered rules, we apply the unscaled 7.2 MW threshold in the main metrics, but note that the F1 verdict of Bounded is determined by the verbatim dispatch limit.

### F2 — Energy Capacity (Claim: 100.0 MWh)
Energy capacity requires a continuous discharge block of ≥ 30 minutes to verify the continuous energy delivered.
- **Total discharge events:** 246
- **Peak continuous discharge block:** **58.0 MWh** (delivered on 2026-05-12 between 01:15 UTC and 03:05 UTC, draining SoC from 75.81 MWh to 3.65 MWh over 1.83 hours).
- **Full-Charge Dispatch Performance:** The dataset contains 6 intervals where full-charge instructions (Base Point <= LSL < 0) were issued under status ON. In all 6 cases, the starting SoC of the subsequent discharge block was materially below the 90.0 MWh (90% of nameplate) threshold, peaking at **75.54 MWh** (on 2026-03-31). This mechanically satisfies the rule for a **Not Verified** verdict (leading to the v1.2 verdict of **Not Demonstrated**).
- **LSL Rule Amendment (Comparability Clause):** The original Anole audit code identified full-charge instructions using the check `Base Point <= LSL`. In the Anole dataset, this check and `Base Point <= LSL < 0` are mathematically equivalent and yield exactly **4,382 intervals** in both cases because the operator telemetered a negative LSL (`-240 MW`) during standby/idle periods. In Bat Cave, the operator telemetered `LSL = 0` during standby/idle periods. The naive check `Base Point <= LSL` was therefore met during idle intervals where `BP = 0, LSL = 0`, artificially inflating the count to 146 intervals. To protect the physical intent of the rule (identifying actual charging dispatches), we amended the check to `Base Point <= LSL < 0`, which yields exactly **6 intervals** on both the Grid Status and ERCOT direct datasets. This amendment is invariant on the Anole dataset and has no effect on the final F2 verdict (which remains Not Verified under both the 146 and 6 interval branches).
- **Normal Operations Context:** Outside of these full-charge instructions, telemetered SoC reached up to **99.18 MWh** on 12 operating days during normal operations, indicating that the BESS is capable of charging near nameplate capacity, but did not do so in response to the full-charge instructions followed by discharge events.

### F3 — SoC Telemetry Consistency
Evaluates the mathematical consistency between operator-reported BMS State of Charge (SoC) and actual physical net output (TNO).
- **Formula:** $\Delta \text{SoC} = \text{SoC}_{\text{start}} - \text{SoC}_{\text{end}}$ vs $\text{Discharge MWh} = \int \text{TNO} \, dt$
- **Expected Ratio:** $\frac{\text{Discharge MWh}}{\Delta \text{SoC}} \in [0.85, 1.0]$ 
- **Results:** Only **3 out of 245** evaluable events (1.22%) met this criterion. The mean consistency ratio is **0.6339**, indicating a systematic deviation where the reported SoC drops significantly faster than integrated energy output.
- **Verdict:** **Inconsistent** (defined strictly under the naive thermodynamic expectation rule).
  - *Context:* This deviation does not imply telemetry error or underperformance. Because the exact physical definition of the reported `soc` field (e.g., usable energy, round-trip efficiency losses, or auxiliary/parasitic consumption) is undocumented, the physical cause remains undetermined. Under standard battery characteristics, a ratio of 0.63–0.77 is consistent with physical losses and parasitic auxiliary loads, but cannot be verified without official ERCOT column schemas.


### F4 — SoC Field Interpretation & Pre-Registration Compromise
- **Pre-Registration Failure:** The pre-registered F4 hypothesis framing was based on an L0 scoping error asserting that the maximum telemetered SoC on April 1, 2026, was 76.8 MWh. Actual telemetry shows `max_soc` reached 102.57 MWh and `soc` reached 73.77 MWh on that day. The scoping error has been documented in `failures.md`.
- **Protocol Remediation:** Because the pre-registered framing is void, the F4 hypothesis test is compromised. The primary F4 verdict remains **Deferred** pending official ERCOT column schemas. No post-hoc assumptions (such as asserting the "scaling" explanation as proven fact) are used to determine this verdict.
- **Observed Limits:** The `max_soc` field peaked at 102.95 MWh, which is consistent with an MWh scale. 

---

## 4. Visual Evidence

### Panel 1: Peak Continuous Discharge Event (2026-05-12)
The plot below illustrates the peak discharge event, showing the battery draining from 75.81 MWh to 3.65 MWh, delivering a total of 58.0 MWh:

![Peak Discharge Event](../../results/panel1_peak_discharge_event.png)

### Panel 2: SoC Telemetry Consistency Ratio Histogram
The distribution of the consistency ratio shows a heavy concentration around 0.60–0.70, well below the naive expectation band of 0.85+:

![SoC Consistency Histogram](../../results/panel2_f3_histogram.png)

---

## 5. Post-Hoc Exploratory Analysis

*This section presents findings that were not pre-registered and do not affect the primary audit verdicts.*

### Telemetry Ratio Behavior (Event-Size Stratification)
The overall average consistency ratio of metered discharge to telemetered SoC drop is 0.6339 across the entire 60-day window. This overall average is not uniform, but exhibits a dependency on event sizes, as demonstrated when the 245 evaluable discharge events are stratified by integrated discharge size:

| Event Size Bin | Event Count | Mean Consistency Ratio | Ratio Range |
| :--- | :---: | :---: | :---: |
| **< 5 MWh** | 88 | **0.4178** | [0.0375, 1.4112] |
| **5 - 15 MWh** | 62 | **0.7195** | [0.4045, 0.9871] |
| **15 - 30 MWh** | 50 | **0.7710** | [0.6720, 0.9055] |
| **30 - 50 MWh** | 37 | **0.7838** | [0.7289, 0.8424] |
| **>= 50 MWh** | 8 | **0.7965** | [0.7683, 0.8221] |

#### Contrast with Anole and AEMO Dispatch Telemetry
To put these findings in context, we contrast Bat Cave's telemetry behavior with both the ERCOT Anole BESS audit (US-TX-ANOL-001) and the AEMO NEM fleet telemetry (AU).

##### Comparison with Anole Audit
For major discharge events ($\ge$ 10 MWh), the consistency ratios show a distinct baseline shift between the two ERCOT assets:
- **Anole BESS:** Reaches a mean consistency ratio of **0.9809** (Version 1.0.1, DOI: 10.5281/zenodo.21304135). Due to variance around this high center, 17.3% of its major events exceed 1.0.
- **Bat Cave BESS:** Reaches a mean consistency ratio of **0.7703** (117 major events), with 0% of events exceeding 1.0 (maximum ratio 0.9055).

However, the fact that Bat Cave has 0% of events exceeding 1.0 is a consequence of statistical distribution rather than a proof of physical compliance. Since the Bat Cave distribution is centered at 0.77 with a standard deviation of 0.043, a ratio of 1.0 lies more than $+5.30\sigma$ above the mean. Thus, it is mathematically expected that no observed events exceed 1.0, regardless of telemetry quality. Similarly, the higher pass rate of Anole is primarily a function of its distribution centering rather than superior telemetry quality.

Without official ERCOT documentation of the telemetry fields, it remains unresolved whether the difference between Anole's $\sim$0.98 mean and Bat Cave's $\sim$0.77 mean represents a difference in physical performance (e.g., round-trip efficiency and auxiliary loads) or merely a difference in reporting convention (e.g., total internal energy capacity vs. usable delivered energy capacity). With $n = 2$ assets, we cannot distinguish reporting conventions from physical performance.

##### Comparison with AEMO NEM Telemetry
This ambiguity in ERCOT contrasts. In AEMO's NEM dispatch telemetry (spanning 53 units over 12 months), the telemetry fields exhibit a precise mathematical identity. Under zero regulation services ($\text{LOWERREG} = 0$), the Victoria Big Battery (VBB1) telemetry satisfies the closed-form equation:
$$\text{ENERGY\_STORAGE}(t) - \text{INITIAL\_ENERGY\_STORAGE}(t) = - \text{trapez}(\text{INITIALMW} \to \text{TOTALCLEARED})$$
(where the negative sign arises because AEMO represents charging as negative MW power). This demonstrates that AEMO's telemetry is directly calculated via closed-form integration of dispatch instructions rather than being an independent physical measurement. In contrast, ERCOT's lack of documented semantics makes it impossible to verify if its fields represent raw physical sensor readings or integrated dispatch values.

A definitive resolution of these differences requires official ERCOT MIS column documentation.
