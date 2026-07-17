#!/usr/bin/env python3
"""Panel 3 — cross-audit SoC reconciliation comparison.

Two responsibilities:

  vendor_anole_reference()  copies the Anole F3 major-event ratios INTO this
                            repository, hash-pinned, so Panel 3 regenerates on
                            any clone. Run once, commit the result.

  generate_panel3()         renders the figure from vendored + local metrics.

Design constraints (P10 Publication Gate, PG3):
  * The only shaded region is the pre-registered [0.85, 1.00] rule band. It is
    the one boundary that exists. Interpretive bands are not drawn as if
    measured.
  * Distributions are normalised to percent-of-own-events. Raw counts would
    make the larger sample look like the stronger result.
  * Colours are the standard categorical pair. No pass/fail valence.
  * The title describes what is plotted. The subtitle states the limit. Neither
    asserts a conclusion the data cannot support.
"""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = Path(__file__).parent
BATC_METRICS = BASE_DIR / "audits" / "US-TX-BATC-001" / "metrics.json"
REFERENCE = BASE_DIR / "audits" / "US-TX-BATC-001" / "reference" / "anole_f3_major_events.json"
OUTPUT = BASE_DIR / "results" / "panel3_f3_comparison.png"

MAJOR_MWH = 10.0                 # threshold, frozen — identical to the Anole audit
RULE_BAND = (0.85, 1.00)         # pre-registered F3 expectation band

ANOLE_DOI = "10.5281/zenodo.21304134"
BATC_DOI = "10.5281/zenodo.21401795"

C_ANOLE = "#4C72B0"
C_BATC = "#DD8452"
C_RULE = "#6B7280"


# ── vendoring ────────────────────────────────────────────────────────────────

def vendor_anole_reference(anole_metrics: Path) -> None:
    """Extract the Anole major-event ratios into this repo, hash-pinned.

    Panel 3 is a cross-audit comparison, so the other audit's output is an
    INPUT to this one. Inputs get archived. A figure that renders only on the
    author's laptop is not reproducible, it is a screenshot.
    """
    raw = anole_metrics.read_bytes()
    src_sha = hashlib.sha256(raw).hexdigest()
    m = json.loads(raw)

    events = m["F3"]["events"]
    ratios = [e["consistency_ratio"] for e in events if e["mwh"] >= MAJOR_MWH]
    if not ratios:
        raise SystemExit(f"ABORT: no Anole events >= {MAJOR_MWH} MWh")

    payload = {
        "_comment": "Vendored input to US-TX-BATC-001 Panel 3. Derived from the "
                    "Anole audit's frozen metrics.json. Do not edit by hand.",
        "source_audit": "US-TX-ANOL-001",
        "source_doi": ANOLE_DOI,
        "source_file": "audits/US-TX-ANOL-001/metrics.json",
        "source_sha256": src_sha,
        "threshold_mwh": MAJOR_MWH,
        "n_events": len(ratios),
        "mean_ratio": round(sum(ratios) / len(ratios), 6),
        "consistency_ratios": [round(r, 6) for r in ratios],
    }
    REFERENCE.parent.mkdir(parents=True, exist_ok=True)
    REFERENCE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Vendored {len(ratios)} Anole ratios -> {REFERENCE}")
    print(f"  source sha256: {src_sha}")
    print("  Commit this file and add its hash to data_manifest.json.")


# ── figure ───────────────────────────────────────────────────────────────────

def _load():
    if not REFERENCE.exists():
        raise SystemExit(
            f"ABORT: {REFERENCE} is missing.\n"
            f"Panel 3 is a cross-audit comparison and cannot be regenerated "
            f"without the vendored reference. Run vendor_anole_reference() "
            f"against the Anole audit's metrics.json and commit the result.\n"
            f"Silently skipping would ship a figure no third party can "
            f"reproduce, which is not Class A."
        )
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))

    m = json.loads(BATC_METRICS.read_text(encoding="utf-8"))
    batc = [e["consistency_ratio"] for e in m["F3"]["events"]
            if e["mwh"] >= MAJOR_MWH]

    if ref["threshold_mwh"] != MAJOR_MWH:
        raise SystemExit(f"ABORT: vendored threshold {ref['threshold_mwh']} "
                         f"!= {MAJOR_MWH}. The comparison would not be like "
                         f"for like.")
    return ref["consistency_ratios"], batc, ref


def generate_panel3() -> None:
    anole, batc, ref = _load()

    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=140)
    bins = np.linspace(0.40, 1.30, 31)

    # Percent of each asset's own major events. Raw counts would encode sample
    # size as apparent magnitude.
    for data, colour, label in (
        (anole, C_ANOLE, f"esVolta Anole BESS (240 MW / 480 MWh) — "
                         f"n={len(anole)}, mean {np.mean(anole):.2f}"),
        (batc, C_BATC, f"Bat Cave BESS (100 MW / 100 MWh) — "
                       f"n={len(batc)}, mean {np.mean(batc):.2f}"),
    ):
        w = np.ones(len(data)) / len(data) * 100
        ax.hist(data, bins=bins, weights=w, color=colour, alpha=0.55,
                edgecolor=colour, linewidth=1.4, label=label)

    # The only region with a definition behind it.
    ax.axvspan(*RULE_BAND, color=C_RULE, alpha=0.13, zorder=0)
    ax.text(np.mean(RULE_BAND), ax.get_ylim()[1] * 0.97,
            "pre-registered\nexpectation band\n[0.85 – 1.00]",
            ha="center", va="top", fontsize=8.5, color="#374151",
            linespacing=1.35)

    for data, colour in ((anole, C_ANOLE), (batc, C_BATC)):
        ax.axvline(np.mean(data), color=colour, ls="--", lw=1.6, alpha=0.9)

    ax.set_xlabel("Reconciliation ratio  —  metered discharge (MWh) / reported SoC drop (MWh)",
                  fontsize=10.5, labelpad=9)
    ax.set_ylabel("% of that asset's major discharge events", fontsize=10.5)
    ax.set_xlim(0.40, 1.30)
    ax.tick_params(labelsize=9.5)
    ax.grid(axis="y", ls=":", alpha=0.45)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper left", fontsize=9.5, frameon=False)

    fig.suptitle(f"SoC reconciliation, major discharge events (\u2265 {MAJOR_MWH:.0f} MWh)",
                 fontsize=14, fontweight="bold", x=0.062, ha="left", y=0.975)
    ax.set_title("Two ERCOT assets, identical frozen rules. Neither position is "
                 "attributable to asset performance.",
                 fontsize=10, color="#4B5563", loc="left", pad=10)

    fig.text(
        0.062, 0.012,
        "A ratio near 0.94 is consistent with `soc` denominated in delivered energy; near 0.77 with `soc` denominated in total\n"
        "stored energy (round-trip efficiency plus auxiliary load). We found no published field definition, and with n=2 assets\n"
        f"the public data does not distinguish a reporting convention from a physical one.   Sources: {ANOLE_DOI} · {BATC_DOI}",
        fontsize=7.6, color="#6B7280", ha="left", linespacing=1.6)

    fig.tight_layout(rect=[0, 0.085, 1, 0.94])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=140, facecolor="white")
    plt.close(fig)
    print(f"Saved {OUTPUT}  (Anole n={len(anole)}, Bat Cave n={len(batc)})")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--vendor":
        vendor_anole_reference(Path(sys.argv[2]))
    else:
        generate_panel3()
