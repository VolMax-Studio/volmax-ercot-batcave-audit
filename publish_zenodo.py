#!/usr/bin/env python3
"""Publish the ERCOT Bat Cave BESS audit to Zenodo and retrieve the DOI."""
import json
import os
import sys
import requests

ZENODO_API = "https://zenodo.org/api"
TOKEN = open(os.path.expanduser("~/.zenodo_token")).readline().strip()
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Files to upload (source code, reports, plots, metadata)
UPLOAD_FILES = [
    "README.md",
    "audit_batcave.py",
    "pull_batcave.py",
    "pull_batcave_api.py",
    "pull_batcave_api_daily.py",
    "cross_validate_datasets.py",
    "get_ercot_stats.py",
    "audits/US-TX-BATC-001/report.md",
    "audits/US-TX-BATC-001/findings.md",
    "audits/US-TX-BATC-001/metrics.json",
    "audits/US-TX-BATC-001/failures.md",
    "audits/US-TX-BATC-001/data_manifest.json",
    "results/panel1_peak_discharge_event.png",
    "results/panel2_f3_histogram.png",
    ".zenodo.json",
    "CITATION.cff",
    "LICENSE",
    ".gitignore",
]

def main():
    # Load metadata from .zenodo.json
    with open(".zenodo.json") as f:
        zmeta = json.load(f)

    # Step 1: Create empty deposit
    print("Creating Zenodo deposit...")
    r = requests.post(f"{ZENODO_API}/deposit/depositions",
                      headers={**HEADERS, "Content-Type": "application/json"},
                      json={})
    r.raise_for_status()
    deposition = r.json()
    dep_id = deposition["id"]
    bucket_url = deposition["links"]["bucket"]
    print(f"  Deposit created: ID={dep_id}")

    # Step 2: Upload files
    print(f"Uploading {len(UPLOAD_FILES)} files...")
    for filepath in UPLOAD_FILES:
        if not os.path.exists(filepath):
            print(f"  SKIP (not found): {filepath}")
            continue
        filename = os.path.basename(filepath)
        # Use bucket API for large file support
        with open(filepath, "rb") as fp:
            r = requests.put(
                f"{bucket_url}/{filename}",
                headers=HEADERS,
                data=fp,
            )
            r.raise_for_status()
        print(f"  Uploaded: {filepath} -> {filename}")

    # Step 3: Set metadata
    print("Setting metadata...")
    metadata = {
        "metadata": {
            "title": zmeta["title"],
            "upload_type": "dataset",
            "description": zmeta["description"],
            "creators": zmeta["creators"],
            "access_right": zmeta["access_right"],
            "license": zmeta["license"],
            "keywords": zmeta["keywords"],
        }
    }
    r = requests.put(f"{ZENODO_API}/deposit/depositions/{dep_id}",
                     headers={**HEADERS, "Content-Type": "application/json"},
                     json=metadata)
    r.raise_for_status()
    print("  Metadata set.")

    # Step 4: Publish
    print("Publishing deposition...")
    r = requests.post(f"{ZENODO_API}/deposit/depositions/{dep_id}/actions/publish",
                      headers=HEADERS)
    r.raise_for_status()
    published = r.json()
    doi = published["doi"]
    doi_url = published["doi_url"]
    record_url = published["links"]["record_html"]
    print(f"\n{'='*60}")
    print(f"PUBLISHED SUCCESSFULLY")
    print(f"  DOI:        {doi}")
    print(f"  DOI URL:    {doi_url}")
    print(f"  Record:     {record_url}")
    print(f"{'='*60}")

    # Write DOI to a local file for downstream use
    with open("zenodo_doi.txt", "w") as f:
        f.write(f"{doi}\n{doi_url}\n{record_url}\n")
    print(f"DOI saved to zenodo_doi.txt")

if __name__ == "__main__":
    main()
