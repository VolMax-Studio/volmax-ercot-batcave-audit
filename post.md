We ran our ERCOT battery audit a second time — same frozen rules, different asset, different operator. The replication neither confirmed nor contradicted the first result. It found the edge of what public telemetry can tell you.

Bat Cave BESS (100 MW / 100 MWh, Mason County, TX): 60 days of primary ERCOT SCED disclosure telemetry, 17,500 records.

**First, our own error.** Our pre-registration cited a number that does not exist in the data. The hypothesis framing built on it was voided, and the error is documented in our public failure registry. The rules stayed frozen. The mistake stays visible.

**What we found.**

The 100 MW claim was never tested. ERCOT never dispatched the asset above 84.5 MW, and peak output was 72.6 MW. Under our protocol that is "Not Demonstrated" — a statement about dispatch, not about the battery. Largest continuous discharge: 58.0 MWh.

**Then the part we cannot resolve.**

Our method reconstructs delivered energy from metered output and compares it against the reported state-of-charge drop.

On our first ERCOT audit (esVolta Anole, 240 MW / 480 MWh), that reconciliation closed on 55.2% of discharge events overall, and 81.8% of major events — mean ratio 0.98. But that "pass rate" is misleading: because Anole's distribution centers at 0.98, its variance causes 38 major events (17.3%) to exceed 1.0, which is thermodynamically impossible (delivered energy cannot exceed reported SoC drop).

On Bat Cave, under identical rules: 1.22% overall, 1.71% of major events — mean ratio 0.77. Yet Bat Cave has exactly 0% of events exceeding 1.0 (maximum ratio 0.9055). Every single event is physically possible.

Same market. Same public data product. Two reconciliation regimes.

Here is the part that matters: a ratio near 0.77 is consistent with total stored energy denomination (reflecting round-trip efficiency and auxiliary load). A ratio near 0.98 is consistent with delivered energy denomination. Both are ordinary. Neither is a defect.

We could not find published documentation defining these fields. With n=2 and no schema, we cannot distinguish a fleet-level reporting convention from a physical one. We do not claim either asset underperforms. We claim we cannot tell — and that is the finding.

Public ERCOT telemetry increasingly feeds performance benchmarking, third-party indices, and pre-diligence screening — the layer that runs before anyone gets a data room. If the state-of-charge field cannot be independently reconstructed without semantics nobody published, what is that layer measuring?

Everything is open — code, raw telemetry, hashes, and the failure registry:

Code and data: https://github.com/VolMax-Studio/volmax-ercot-batcave-audit
DOI (all versions): https://doi.org/10.5281/zenodo.21401795

If the field definitions exist somewhere public and we missed them, tell me — we will re-run and publish the correction under the same DOI.

#BESS #EnergyStorage #ERCOT
