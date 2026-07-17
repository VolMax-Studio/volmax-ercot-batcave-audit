#!/usr/bin/env python3
"""Publish the ERCOT Bat Cave BESS audit to Zenodo.

Safe by default:
  * If zenodo_doi.txt exists, this publishes a NEW VERSION of the existing
    record, preserving the concept DOI. It will not create an orphan record.
  * If it does not exist, --force-new creates the first deposition.

Usage:
    python publish_zenodo.py --version 1.0.3 --dry-run
    python publish_zenodo.py --version 1.0.3
    python publish_zenodo.py --version 1.0.0 --force-new   # first publish only
"""
import argparse
import glob
import json
import os
import sys

import requests

ZENODO_API = "https://zenodo.org/api"
DOI_FILE = "zenodo_doi.txt"

# ---------------------------------------------------------------- file set

CORE_FILES = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    ".zenodo.json",
    ".gitignore",
    "audit_batcave.py",
    "pull_batcave.py",
    "pull_batcave_api.py",
    "pull_batcave_api_daily.py",
    "cross_validate_datasets.py",
    "get_ercot_stats.py",
    "publish_zenodo.py",
    "audits/US-TX-BATC-001/report.md",
    "audits/US-TX-BATC-001/findings.md",
    "audits/US-TX-BATC-001/failures.md",
    "audits/US-TX-BATC-001/metrics.json",
    "audits/US-TX-BATC-001/data_manifest.json",
    "results/panel1_peak_discharge_event.png",
    "results/panel2_f3_histogram.png",
]

# Raw telemetry. The manifest hashes are worthless if the files they describe
# live only on GitHub. The DOI is the permanence layer, so the data goes in it.
RAW_GLOB = "audits/US-TX-BATC-001/raw_data/*.csv"


def collect_files():
    present = [f for f in CORE_FILES if os.path.exists(f)]
    missing = [f for f in CORE_FILES if not os.path.exists(f)]

    raw = sorted(glob.glob(RAW_GLOB))
    if not raw:
        sys.exit(f"ABORT: no raw telemetry matched {RAW_GLOB}. Refusing to "
                 f"publish a manifest without the data it hashes.")
    files = present + raw

    # Zenodo keys are flat basenames; a collision would silently overwrite.
    seen = {}
    for path in files:
        name = os.path.basename(path)
        if name in seen:
            sys.exit(f"ABORT: basename collision on '{name}':\n"
                     f"  {seen[name]}\n  {path}")
        seen[name] = path
    return files, missing


# ---------------------------------------------------------------- api

def auth():
    path = os.path.expanduser("~/.zenodo_token")
    if not os.path.exists(path):
        sys.exit(f"ABORT: no token at {path}")
    return {"Authorization": f"Bearer {open(path).readline().strip()}"}


def read_prev_record_id():
    if not os.path.exists(DOI_FILE):
        return None
    for line in open(DOI_FILE):
        line = line.strip()
        if line.startswith("CONCEPT_DOI") or not line:
            continue
        if "zenodo.org/record" in line:
            return line.rstrip("/").split("/")[-1]
    first = open(DOI_FILE).readline().strip()
    if "zenodo." in first:
        return first.split("zenodo.")[-1]
    return None


def start_new_version(headers, prev_id):
    print(f"Creating new version of record {prev_id}...")
    r = requests.post(
        f"{ZENODO_API}/deposit/depositions/{prev_id}/actions/newversion",
        headers=headers)
    if r.status_code == 403:
        sys.exit("ABORT: 403 on newversion. Token lacks write scope, or "
                 f"record {prev_id} is not yours.")
    r.raise_for_status()
    draft_url = r.json()["links"]["latest_draft"]
    d = requests.get(draft_url, headers=headers)
    d.raise_for_status()
    return d.json()


def start_first(headers):
    print("Creating first deposition...")
    r = requests.post(f"{ZENODO_API}/deposit/depositions",
                      headers={**headers, "Content-Type": "application/json"},
                      json={})
    r.raise_for_status()
    return r.json()


def clear_inherited_files(headers, dep):
    """A new version inherits the previous version's files. Drop them so the
    record reflects this version exactly, not a merge of two."""
    inherited = dep.get("files", [])
    for f in inherited:
        r = requests.delete(
            f"{ZENODO_API}/deposit/depositions/{dep['id']}/files/{f['id']}",
            headers=headers)
        r.raise_for_status()
    if inherited:
        print(f"  Cleared {len(inherited)} inherited file(s).")


def upload(headers, bucket, files):
    print(f"Uploading {len(files)} files...")
    for path in files:
        with open(path, "rb") as fp:
            r = requests.put(f"{bucket}/{os.path.basename(path)}",
                             headers=headers, data=fp)
            r.raise_for_status()
    total = sum(os.path.getsize(p) for p in files) / 1e6
    print(f"  Done ({total:.2f} MB).")


def set_metadata(headers, dep_id, version):
    zmeta = json.load(open(".zenodo.json"))
    meta = {
        "title": zmeta["title"],
        "upload_type": "dataset",
        "description": zmeta["description"],
        "creators": zmeta["creators"],
        "access_right": zmeta["access_right"],
        "license": zmeta["license"],
        "keywords": zmeta["keywords"],
        "version": version,
    }
    r = requests.put(f"{ZENODO_API}/deposit/depositions/{dep_id}",
                     headers={**headers, "Content-Type": "application/json"},
                     json={"metadata": meta})
    r.raise_for_status()
    got = r.json()["metadata"].get("version")
    if got != version:
        sys.exit(f"ABORT: Zenodo stored version '{got}', expected '{version}'.")
    print(f"  Metadata set (version {got}).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="e.g. 1.0.3")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force-new", action="store_true",
                    help="create an unlinked record (first publish only)")
    args = ap.parse_args()

    files, missing = collect_files()
    for m in missing:
        print(f"  WARN missing: {m}")
    total = sum(os.path.getsize(f) for f in files) / 1e6
    print(f"{len(files)} files staged, {total:.2f} MB")

    prev_id = read_prev_record_id()
    if prev_id and args.force_new:
        sys.exit(f"ABORT: {DOI_FILE} points at record {prev_id}. --force-new "
                 f"would orphan it under a new concept DOI. Drop the flag.")
    if not prev_id and not args.force_new:
        sys.exit(f"ABORT: no {DOI_FILE} found. Pass --force-new only if this "
                 f"audit has never been published.")

    if args.dry_run:
        target = f"new version of record {prev_id}" if prev_id else "a new record"
        print(f"\nDRY RUN - would publish v{args.version} as {target}")
        for f in files[:6]:
            print(f"  {f}")
        if len(files) > 6:
            print(f"  ... and {len(files) - 6} more")
        return

    headers = auth()
    dep = start_new_version(headers, prev_id) if prev_id else start_first(headers)
    if prev_id:
        clear_inherited_files(headers, dep)

    upload(headers, dep["links"]["bucket"], files)
    set_metadata(headers, dep["id"], args.version)

    print("Publishing...")
    r = requests.post(
        f"{ZENODO_API}/deposit/depositions/{dep['id']}/actions/publish",
        headers=headers)
    r.raise_for_status()
    pub = r.json()

    doi = pub["doi"]
    concept = pub.get("conceptdoi")
    record = pub["links"]["record_html"]

    print("\n" + "=" * 62)
    print(f"  Version DOI (frozen) : {doi}")
    print(f"  Concept DOI (cite me): {concept}")
    print(f"  Record               : {record}")
    print("=" * 62)

    if not concept:
        print("\n  WARN: no conceptdoi returned. Do NOT update citations "
              "until you confirm it on the record page.")
        return

    with open(DOI_FILE, "w") as f:
        f.write(f"{doi}\n"
                f"https://doi.org/{doi}\n"
                f"{record}\n"
                f"CONCEPT_DOI={concept}\n"
                f"https://doi.org/{concept}\n")
    print(f"\n  {DOI_FILE} updated. Cite the CONCEPT DOI everywhere.")


if __name__ == "__main__":
    main()
