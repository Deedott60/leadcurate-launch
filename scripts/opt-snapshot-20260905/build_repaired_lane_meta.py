#!/usr/bin/env python3
"""Build file-matched metadata for a QA-repaired lane artifact."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--repair-report", required=True, type=Path)
    parser.add_argument("--qa-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    repair = json.loads(args.repair_report.read_text(encoding="utf-8"))
    qa = json.loads(args.qa_report.read_text(encoding="utf-8"))
    matches = [
        row for row in qa["results"]
        if row["market"] == repair["market"] and row["lane"] == repair["lane"]
    ]
    if len(matches) != 1 or not matches[0]["passed"]:
        raise ValueError("repaired lane does not have exactly one passing QA result")
    result = matches[0]
    warnings = result["warnings"]
    payload = {
        "market": repair["market"],
        "market_display": manifest["market_display"],
        "lane": repair["lane"],
        "lane_display": manifest["lane_display"],
        "status": "verified",
        "source_name": manifest["source_name"],
        "source_url": manifest["source_url"],
        "source_file": manifest["source_file"],
        "source_sha256": manifest["source_sha256"],
        "source_data_as_of": manifest["pull_cycle"],
        "source_retrieved_at": "2026-07-27",
        "records": repair["output_rows"],
        "repair": repair,
        "verification": {
            "qa_gate": "pass",
            "owner_occupied_pct": warnings.get("owner_occupied_pct"),
            "institutional_pct": warnings.get("institutional_pct"),
            "front50_outlier_pct": warnings.get("front50_outlier_pct"),
            "owner_populated_pct": warnings["owner_populated_pct"],
            "property_address_populated_pct": warnings["property_address_populated_pct"],
            "parcel_id_populated_pct": warnings["parcel_id_populated_pct"],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
