We audited a second ERCOT battery under the same frozen rules. The replication didn't confirm or contradict our first audit — it exposed the limits of public telemetry.

Bat Cave BESS (100 MW/100 MWh, TX): 60 days of primary ERCOT SCED telemetry, 17,500 rows.

**First, our error.** Our pre-registration cited a non-existent number. The hypothesis built on it was voided, and the error is in our public failure registry. The rules stayed frozen; the mistake stays visible.

**Findings.** The 100 MW claim was never tested: peak dispatch was 72.6 MW, and ERCOT never called for >84.5 MW. Under our protocol, this is "Not Demonstrated" — a statement about dispatch, not physical limits. Max discharge: 58.0 MWh.

**The unresolved telemetry.** We compare reconstructed delivered energy against reported state-of-charge (SoC) drop.

On Bat Cave, the F3 reconciliation results are:
- Primary (frozen rule, all 245 events): 1.22% pass (mean ratio 0.6339).
- Exploratory (post-hoc stratification, ≥10 MWh, 117 events): 1.71% pass (mean ratio 0.7703).

On Anole, under the same frozen rule: 55.2% pass overall; the same exploratory stratification reached 81.8% (mean 0.98).

Same market, same data product, two different regimes. Yet their standard deviations are nearly identical (0.038 vs 0.043). The difference is a pure location shift of 0.21.

This exposes a limit of our pre-registered [0.85, 1.0] F3 rule. The pass rate measures where a distribution is centered, not data quality:
- Anole (mean 0.98) falls inside the band but has 17.3% of events exceeding 1.0 (a physical impossibility bounding our reconstruction noise).
- Bat Cave (mean 0.77) has 0% inside the band, yet is just as clean and never violates physics.

Both are ordinary; neither is a defect. A 0.77 ratio matches total stored energy denomination (reflecting efficiency and auxiliary losses). A 0.98 ratio matches delivered energy denomination.

With n=2 and no published schema, we cannot distinguish a reporting convention from a physical performance difference — which is the finding. We don't claim either asset underperforms; we claim we cannot tell.

Public ERCOT telemetry feeds benchmarks, indices, and pre-diligence screens. If the state-of-charge field cannot be reconstructed without undocumented, asset-specific semantics, what are these screens measuring?

Code, raw data, and hashes are open:
GitHub: https://github.com/VolMax-Studio/volmax-ercot-batcave-audit
DOI: https://doi.org/10.5281/zenodo.21401795

If we missed a public field definition, let us know — we will re-run and publish the fix.

#BESS #EnergyStorage #ERCOT
