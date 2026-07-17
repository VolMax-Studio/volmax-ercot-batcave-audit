We ran our ERCOT battery audit a second time — same frozen rules, different asset, different operator. The replication neither confirmed nor contradicted the first result. It found the edge of what public telemetry can tell you.

Bat Cave BESS (100 MW / 100 MWh, Mason County, TX): 60 days of primary ERCOT SCED disclosure telemetry, 17,500 records.

**First, our own error.** Our pre-registration cited a number that does not exist in the data. The hypothesis framing built on it was voided, and the error is documented in our public failure registry. The rules stayed frozen. The mistake stays visible.

**What we found.**

The 100 MW claim was never tested. ERCOT never dispatched the asset above 84.5 MW, and peak output was 72.6 MW. Under our protocol that is "Not Demonstrated" — a statement about dispatch, not about the battery. Largest continuous discharge: 58.0 MWh.

**Then the part we cannot resolve.**

Our method reconstructs delivered energy from metered output and compares it against the reported state-of-charge drop.

On our first ERCOT audit (esVolta Anole, 240 MW / 480 MWh), that reconciliation closed on 55.2% of discharge events overall, and 81.8% of major events — mean ratio 0.98.

On Bat Cave, under identical rules: 1.22% overall, 1.71% of major events — mean ratio 0.77.

Same market. Same public data product. Two reconciliation regimes. Yet their standard deviations are almost identical (0.038 vs 0.043). The difference is purely a location shift of 0.21.

This reveals a fundamental limit in our own pre-registered rules. Because the expectation band is fixed at [0.85, 1.0], the pass rate measures whether a ratio distribution is centered near 1.0, not telemetry quality.

- Anole's mean is 0.98, so its variance sweeps 81.8% of events into the band, while causing 17.3% to exceed 1.0 (a physical impossibility that bounds our reconstruction noise, not the battery).
- Bat Cave's mean is 0.77, so its variance places 0% of events in the band, even though its telemetry is just as clean and never violates physics.

Both positions are ordinary. Neither is a defect. A ratio near 0.77 is consistent with total stored energy denomination (reflecting round-trip losses and auxiliary load). A ratio near 0.98 is consistent with delivered energy denomination.

We could not find published documentation defining these fields. With n=2 and no schema, the public telemetry is insufficient to distinguish a reporting convention difference from a physical performance difference — which is itself the finding. We do not claim either asset underperforms; we claim we cannot tell.

Public ERCOT telemetry increasingly feeds performance benchmarking, third-party indices, and pre-diligence screening — the layer that runs before anyone gets a data room. If the state-of-charge field cannot be independently reconstructed without semantics nobody published, what is that layer measuring?

Everything is open — code, raw telemetry, hashes, and the failure registry:

Code and data: https://github.com/VolMax-Studio/volmax-ercot-batcave-audit
DOI (all versions): https://doi.org/10.5281/zenodo.21401795

If the field definitions exist somewhere public and we missed them, tell me — we will re-run and publish the correction under the same DOI.

#BESS #EnergyStorage #ERCOT
