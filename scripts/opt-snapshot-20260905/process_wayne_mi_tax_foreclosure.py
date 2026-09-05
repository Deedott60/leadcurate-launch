#!/usr/bin/env python3
"""Match Wayne County's official 2026 tax-foreclosure PDF to parcels."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SOURCE_PAGE = (
    "https://www.waynecountymi.gov/Government/Elected-Officials/Treasurer/"
    "Property-Tax-Information/Forfeited-Property-List-with-Interested-Parties"
)
SOURCE_URL = (
    "https://www.waynecountymi.gov/files/assets/mainsite/v/1/treasurer/"
    "property-amp-taxes/documents/2026_wayne_county_delinquent_tax_liens.pdf"
)
TOKEN = re.compile(r"(?<![A-Za-z0-9])[0-9][0-9.\-]{6,30}(?![A-Za-z0-9])")


def parcel_key(value: str) -> str:
    return "".join(re.findall(r"\d", value or ""))


def pdf_parcel_keys(pdf: Path, known: set[str]) -> tuple[set[str], int]:
    command = [
        "gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=txtwrite",
        "-sOutputFile=-", str(pdf),
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None
    matched: set[str] = set()
    candidates = 0
    for raw_line in process.stdout:
        line = raw_line.decode("utf-8", errors="replace")
        for token in TOKEN.findall(line):
            key = parcel_key(token)
            if len(key) < 8:
                continue
            candidates += 1
            if key in known:
                matched.add(key)
    stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    return_code = process.wait()
    if return_code:
        raise RuntimeError(f"Ghostscript PDF extraction failed ({return_code}): {stderr[-1000:]}")
    return matched, candidates


def redact(row: dict[str, str]) -> dict[str, str]:
    result = dict(row)
    for field in result:
        lower = field.lower()
        if any(token in lower for token in ("parcel", "owner", "address", "street", "map_number")):
            result[field] = "REDACTED"
    return result


def process(canonical: Path, pdf: Path, output_dir: Path, preview_count: int) -> dict[str, object]:
    known: set[str] = set()
    with canonical.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            key = parcel_key(row.get("parcel_id", ""))
            if key:
                known.add(key)
    matched, candidate_tokens = pdf_parcel_keys(pdf, known)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_date = output_dir.name
    market = "wayne-mi"
    lane = "tax-delinquent"
    lane_dir = output_dir / lane
    lane_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{market}-{lane}-{run_date}"
    full = lane_dir / f"{stem}.csv"
    preview = lane_dir / f"{stem}-preview.csv"
    metadata = lane_dir / f"{stem}-meta.json"
    records = 0
    detroit = 0
    municipalities: dict[str, int] = {}
    preview_rows: list[dict[str, str]] = []
    with canonical.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        fields = [
            *reader.fieldnames,
            "lc_lane",
            "tax_foreclosure_year",
            "tax_years_covered",
            "source_publication_dates",
            "source_list_status",
        ]
        with full.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=fields)
            writer.writeheader()
            for row in reader:
                if parcel_key(row.get("parcel_id", "")) not in matched:
                    continue
                row.update(
                    {
                        "lc_lane": lane,
                        "tax_foreclosure_year": "2026",
                        "tax_years_covered": "2023 and prior",
                        "source_publication_dates": "2025-12-09; 2025-12-16",
                        "source_list_status": "Subject to foreclosure in 2026; source warns paid or resolved parcels may remain in the publication snapshot",
                    }
                )
                writer.writerow(row)
                records += 1
                municipality = row.get("municipality", "Unknown") or "Unknown"
                municipalities[municipality] = municipalities.get(municipality, 0) + 1
                detroit += municipality == "Detroit"
                if len(preview_rows) < preview_count:
                    preview_rows.append(redact(row))
    with preview.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(preview_rows)
    payload = {
        "market": market,
        "lane": lane,
        "status": "verified_publication_snapshot",
        "source_page": SOURCE_PAGE,
        "source_url": SOURCE_URL,
        "source_file": str(pdf),
        "source_data_as_of": "Publication snapshot created during week of 2025-11-16",
        "source_publication_dates": ["2025-12-09", "2025-12-16"],
        "source_status": "Official notice of property subject to foreclosure in 2026 for unpaid 2023-and-prior taxes",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "current_status_limitation": (
            "The official PDF states parcels paid after its November snapshot may still appear. "
            "Parcel-level current balances require a live Treasurer lookup at delivery."
        ),
        "canonical_source": str(canonical),
        "canonical_parcels": len(known),
        "candidate_numeric_tokens_checked": candidate_tokens,
        "records": records,
        "detroit_records": detroit,
        "non_detroit_records": records - detroit,
        "municipalities": dict(sorted(municipalities.items(), key=lambda item: item[1], reverse=True)),
        "outputs": {"full": str(full), "preview": str(preview), "meta": str(metadata)},
        "verification": {
            "matched_keys": len(matched),
            "full_csv_rows": records,
            "meta_count_matches_file": records == len(matched),
            "duplicate_parcels_in_full_csv": records - len(matched),
        },
    }
    metadata.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--preview", type=int, default=25)
    args = parser.parse_args()
    result = process(args.canonical, args.pdf, args.output_dir, args.preview)
    print(json.dumps(result, indent=2))
    return 0 if result["verification"]["meta_count_matches_file"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
