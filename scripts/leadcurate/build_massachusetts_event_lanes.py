#!/usr/bin/env python3
"""Match the nightly Massachusetts Land Court reports to MassGIS parcels.

Only an unambiguous exact normalized city + street match is emitted.  The
Servicemembers report is explicitly described as a pre-foreclosure filing
signal, not as proof that a foreclosure sale will occur.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pdfplumber


SUFFIXES = {
    "STREET": "ST", "ROAD": "RD", "AVENUE": "AVE", "DRIVE": "DR",
    "LANE": "LN", "COURT": "CT", "PLACE": "PL", "TERRACE": "TER",
    "PARKWAY": "PKWY", "HIGHWAY": "HWY", "BOULEVARD": "BLVD",
    "CIRCLE": "CIR", "TRAIL": "TRL", "TURNPIKE": "TPKE",
}
SOURCES = {
    "tax": "https://www.mass.gov/doc/tax-lien-cases/download",
    "service": "https://www.mass.gov/doc/servicemember-cases/download",
}


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def normalized(value: Any) -> str:
    words = re.sub(r"[^A-Z0-9 ]", " ", clean(value).upper()).split()
    return " ".join(SUFFIXES.get(word, word) for word in words)


def parse_report(path: Path, case_type: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            words = page.extract_words() or []
            starts = [
                float(word["top"])
                for word in words
                if float(word["x0"]) < 25 and re.fullmatch(r"\d{2}", word["text"])
            ]
            for index, top in enumerate(starts):
                next_top = starts[index + 1] if index + 1 < len(starts) else 735.0
                block = [word for word in words if top - 1.2 <= float(word["top"]) < next_top - 1.2]
                columns: list[list[str]] = [[] for _ in range(6)]
                for word in sorted(block, key=lambda item: (round(float(item["top"]), 1), float(item["x0"]))):
                    x = float(word["x0"])
                    column = 0 if x < 120 else 1 if x < 190 else 2 if x < 270 else 3 if x < 430 else 4 if x < 600 else 5
                    columns[column].append(word["text"])
                case_number = clean(" ".join(columns[0]))
                if not re.fullmatch(rf"\d{{2}} {case_type} \d{{6}}", case_number):
                    continue
                filed = clean(" ".join(columns[1]))
                city = clean(" ".join(columns[2]))
                street = clean(" ".join(columns[3]))
                if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", filed) or not city or not street:
                    continue
                results.append({
                    "case_number": case_number,
                    "filed_date": filed,
                    "city": city,
                    "street": street,
                    "plaintiff": clean(" ".join(columns[4])),
                    "defendant": clean(" ".join(columns[5])),
                })
    unique = {row["case_number"]: row for row in results}
    return [unique[key] for key in sorted(unique)]


def load_parcels(path: Path, wanted: set[tuple[str, str]]) -> tuple[list[str], dict[tuple[str, str], list[dict[str, str]]]]:
    index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        for row in reader:
            city = normalized(row.get("CITY"))
            addresses = {normalized(row.get("SITE_ADDR")), normalized(row.get("FULL_STR"))}
            for address in addresses - {""}:
                key = (city, address)
                if key in wanted:
                    index[key].append(row)
    return fields, index


def write_lane(
    market_dir: Path,
    run_date: str,
    lane: str,
    report_kind: str,
    cases: list[dict[str, str]],
    parcel_fields: list[str],
    parcels: dict[tuple[str, str], list[dict[str, str]]],
) -> dict[str, Any]:
    matched: list[dict[str, str]] = []
    unmatched: list[dict[str, str]] = []
    seen: set[str] = set()
    event_fields = [
        "lc_parcel_id", "lc_lane", "lc_event_status", "lc_case_number",
        "lc_filed_date", "lc_report_city", "lc_report_street", "lc_plaintiff",
        "lc_defendant", "lc_match_method", "lc_source_url",
    ]
    for case in cases:
        candidates = parcels.get((normalized(case["city"]), normalized(case["street"])), [])
        if len(candidates) != 1:
            unmatched.append({**case, "candidate_parcels": str(len(candidates))})
            continue
        parcel = candidates[0]
        key = clean(parcel.get("LC_PARCEL_KEY"))
        if not key or key in seen:
            continue
        seen.add(key)
        status = "new Land Court tax-lien foreclosure filing" if report_kind == "tax" else "new Land Court Servicemembers filing; pre-foreclosure signal, not a foreclosure judgment"
        matched.append({
            **parcel,
            "lc_parcel_id": key,
            "lc_lane": lane,
            "lc_event_status": status,
            "lc_case_number": case["case_number"],
            "lc_filed_date": case["filed_date"],
            "lc_report_city": case["city"],
            "lc_report_street": case["street"],
            "lc_plaintiff": case["plaintiff"],
            "lc_defendant": case["defendant"],
            "lc_match_method": "unique_exact_normalized_city_and_street",
            "lc_source_url": SOURCES[report_kind],
        })
    lane_dir = market_dir / lane
    lane_dir.mkdir(parents=True, exist_ok=True)
    stem = f"massachusetts-statewide-{lane}-{run_date}"
    full = lane_dir / f"{stem}.csv"
    preview = lane_dir / f"{stem}-preview.csv"
    unmatched_path = lane_dir / f"{stem}-unmatched.csv"
    fields = parcel_fields + event_fields
    for path, rows in ((full, matched), (preview, matched[:25])):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader(); writer.writerows(rows)
    with unmatched_path.open("w", newline="", encoding="utf-8") as handle:
        fields_unmatched = ["case_number", "filed_date", "city", "street", "plaintiff", "defendant", "candidate_parcels"]
        writer = csv.DictWriter(handle, fieldnames=fields_unmatched)
        writer.writeheader(); writer.writerows(unmatched)
    payload = {
        "market": "massachusetts-statewide",
        "lane": lane,
        "status": "verified",
        "source_name": "Massachusetts Land Court nightly three-month case report",
        "source_url": SOURCES[report_kind],
        "source_data_as_of": run_date,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_cases": len(cases),
        "records": len(matched),
        "unmatched_or_ambiguous_cases": len(unmatched),
        "duplicate_parcels_removed": len(cases) - len(unmatched) - len(matched),
        "classification_note": "Servicemembers filings are an advance-of-foreclosure signal, not proof of a foreclosure judgment or scheduled sale." if report_kind == "service" else "Tax Lien cases seek foreclosure of the right of redemption for a recorded municipal tax title.",
        "outputs": {"full": str(full), "preview": str(preview), "unmatched": str(unmatched_path)},
        "verification": {"full_csv_rows": len(matched), "unique_parcels_in_full_csv": len(seen), "duplicate_parcels_in_full_csv": 0},
    }
    (lane_dir / f"{stem}-meta.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--tax-report", type=Path, required=True)
    parser.add_argument("--servicemember-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    tax_cases = parse_report(args.tax_report, "TL")
    service_cases = parse_report(args.servicemember_report, "SM")
    wanted = {
        (normalized(case["city"]), normalized(case["street"]))
        for case in tax_cases + service_cases
    }
    fields, parcels = load_parcels(args.canonical, wanted)
    results = {
        "recorded-tax-liens": write_lane(args.output_dir, args.date, "recorded-tax-liens", "tax", tax_cases, fields, parcels),
        "tax-debt": write_lane(args.output_dir, args.date, "tax-debt", "tax", tax_cases, fields, parcels),
        "pre-foreclosure": write_lane(args.output_dir, args.date, "pre-foreclosure", "service", service_cases, fields, parcels),
    }
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
