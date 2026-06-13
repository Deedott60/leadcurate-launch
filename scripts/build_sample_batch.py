#!/usr/bin/env python3
"""
Build a LeadCurate sample batch from a public-record CSV.

This is a day-one, no-paid-provider workflow:
- reads a CSV downloaded from a lawful public county/source page
- maps common owner/property/source columns
- deduplicates by owner + property + parcel
- assigns a simple lead score and score reason
- writes a buyer-facing sample batch CSV
- writes a sales call tracker CSV for outreach follow-up

It does not skip trace, DNC scrub, bypass websites, or claim a record is safe to call.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


FIELD_ALIASES = {
    "owner_name": [
        "owner",
        "owner name",
        "owner_name",
        "taxpayer",
        "tax payer",
        "name",
        "grantor",
        "defendant",
    ],
    "property_address": [
        "property address",
        "property_address",
        "situs",
        "situs address",
        "site address",
        "location address",
        "parcel address",
        "address",
    ],
    "mailing_address": [
        "mailing address",
        "mailing_address",
        "mail address",
        "owner address",
        "taxpayer address",
    ],
    "parcel_id": [
        "parcel",
        "parcel id",
        "parcel_id",
        "pin",
        "apn",
        "account",
        "account number",
        "property id",
    ],
    "zip_code": ["zip", "zipcode", "zip code", "postal code"],
    "amount_due": [
        "amount due",
        "balance",
        "delinquent amount",
        "tax due",
        "total due",
        "judgment amount",
    ],
    "source_date": ["source date", "date", "file date", "record date", "sale date"],
}


@dataclass
class SampleRecord:
    assignment_preview_id: str
    owner_name: str
    property_address: str
    mailing_address: str
    parcel_id: str
    county: str
    state: str
    lead_lane: str
    source_type: str
    source_date: str
    lead_score: int
    score_reason: str
    contact_status: str
    dnc_status: str
    source_url: str
    notes: str


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.strip().lower()).strip()


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def pick(row: dict[str, str], canonical: str, headers: dict[str, str]) -> str:
    for alias in FIELD_ALIASES[canonical]:
        normalized = normalize_key(alias)
        if normalized in headers:
            return clean_text(row.get(headers[normalized], ""))
    return ""


def build_header_lookup(fieldnames: Iterable[str]) -> dict[str, str]:
    return {normalize_key(name): name for name in fieldnames}


def stable_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).lower().encode("utf-8")).hexdigest()
    return f"LC-SAMPLE-{digest[:10].upper()}"


def score_record(record: dict[str, str], lead_lane: str) -> tuple[int, str]:
    score = 55
    reasons: list[str] = []

    owner = record["owner_name"]
    prop = record["property_address"]
    mailing = record["mailing_address"]
    parcel = record["parcel_id"]
    amount_due = record["amount_due"]

    if owner:
        score += 8
        reasons.append("owner present")
    if prop:
        score += 12
        reasons.append("property address present")
    if parcel:
        score += 8
        reasons.append("parcel/account ID present")
    if mailing and prop and normalize_key(mailing) != normalize_key(prop):
        score += 8
        reasons.append("mailing differs from property")
    if amount_due:
        score += 5
        reasons.append("amount/balance field present")
    if lead_lane in {"tax_delinquent", "foreclosure", "probate_estate", "vacant_property"}:
        score += 4
        reasons.append(f"{lead_lane.replace('_', ' ')} signal")

    if not owner:
        score -= 12
        reasons.append("missing owner")
    if not prop:
        score -= 18
        reasons.append("missing property address")

    score = max(0, min(100, score))
    return score, "; ".join(reasons[:5]) or "public-record sample candidate"


def infer_lead_lane(source_type: str) -> str:
    key = normalize_key(source_type)
    if "tax" in key:
        return "tax_delinquent"
    if "probate" in key or "estate" in key:
        return "probate_estate"
    if "foreclosure" in key or "trustee" in key:
        return "foreclosure"
    if "vacant" in key or "code" in key:
        return "vacant_property"
    if "absentee" in key:
        return "absentee_owner"
    return "public_record_research"


def read_public_csv(
    input_path: Path,
    county: str,
    state: str,
    source_type: str,
    source_url: str,
    fallback_source_date: str,
    limit: int,
) -> list[SampleRecord]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row.")
        headers = build_header_lookup(reader.fieldnames)
        lead_lane = infer_lead_lane(source_type)
        seen: set[str] = set()
        records: list[SampleRecord] = []

        for row in reader:
            normalized = {
                "owner_name": pick(row, "owner_name", headers),
                "property_address": pick(row, "property_address", headers),
                "mailing_address": pick(row, "mailing_address", headers),
                "parcel_id": pick(row, "parcel_id", headers),
                "zip_code": pick(row, "zip_code", headers),
                "amount_due": pick(row, "amount_due", headers),
                "source_date": pick(row, "source_date", headers) or fallback_source_date,
            }
            dedupe_key = normalize_key(
                "|".join(
                    [
                        normalized["owner_name"],
                        normalized["property_address"],
                        normalized["parcel_id"],
                        source_type,
                    ]
                )
            )
            if not dedupe_key or dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            score, reason = score_record(normalized, lead_lane)
            if score < 50:
                continue

            records.append(
                SampleRecord(
                    assignment_preview_id=stable_id(
                        county,
                        state,
                        normalized["owner_name"],
                        normalized["property_address"],
                        normalized["parcel_id"],
                    ),
                    owner_name=normalized["owner_name"] or "Owner not shown in source",
                    property_address=normalized["property_address"],
                    mailing_address=normalized["mailing_address"],
                    parcel_id=normalized["parcel_id"],
                    county=county,
                    state=state.upper(),
                    lead_lane=lead_lane,
                    source_type=source_type,
                    source_date=normalized["source_date"],
                    lead_score=score,
                    score_reason=reason,
                    contact_status="not_enriched",
                    dnc_status="not_scrubbed",
                    source_url=source_url,
                    notes="Public-record sample. Contact data not included until enrichment and DNC/contact policy are configured.",
                )
            )
            if len(records) >= limit:
                break

    return sorted(records, key=lambda item: item.lead_score, reverse=True)


def write_sample_batch(records: list[SampleRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SampleRecord.__dataclass_fields__.keys()))
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)


def write_call_tracker(output_path: Path) -> None:
    tracker_path = output_path.with_name(output_path.stem + "_sales_call_tracker.csv")
    fields = [
        "prospect_company",
        "prospect_name",
        "phone",
        "email",
        "market",
        "source",
        "call_status",
        "last_touch_date",
        "next_follow_up",
        "interest_level",
        "notes",
    ]
    with tracker_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a LeadCurate public-record sample batch.")
    parser.add_argument("--input", required=True, type=Path, help="Public-record CSV source file.")
    parser.add_argument("--output", required=True, type=Path, help="Sample batch CSV output path.")
    parser.add_argument("--county", required=True, help="County name, e.g. Mecklenburg.")
    parser.add_argument("--state", required=True, help="State abbreviation, e.g. NC.")
    parser.add_argument("--source-type", required=True, help="Source label, e.g. tax delinquent.")
    parser.add_argument("--source-url", default="", help="Official source URL.")
    parser.add_argument("--source-date", default=str(date.today()), help="Source file date.")
    parser.add_argument("--limit", default=50, type=int, help="Maximum rows to export.")
    args = parser.parse_args()

    records = read_public_csv(
        input_path=args.input,
        county=args.county,
        state=args.state,
        source_type=args.source_type,
        source_url=args.source_url,
        fallback_source_date=args.source_date,
        limit=args.limit,
    )
    write_sample_batch(records, args.output)
    write_call_tracker(args.output)
    print(f"Wrote {len(records)} sample records to {args.output}")
    print(f"Wrote sales call tracker to {args.output.with_name(args.output.stem + '_sales_call_tracker.csv')}")


if __name__ == "__main__":
    main()
