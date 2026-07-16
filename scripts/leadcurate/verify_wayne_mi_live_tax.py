#!/usr/bin/env python3
"""Refresh Wayne tax-publication parcels against the live Treasurer system.

The Treasurer site is updated each business day. This manual, resumable verifier
POSTs one parcel at a controlled rate, preserves every source row, and emits a
current lane containing only parcels for which the live lookup returns a positive
delinquent balance. A publication match alone is never treated as current debt.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests


SOURCE_URL = "https://devpta.waynecountymi.gov/"
SEARCH_URL = f"{SOURCE_URL}Home/SearchResult"
SPACE = re.compile(r"\s+")
thread_local = threading.local()


def clean(value: object) -> str:
    return SPACE.sub(" ", str(value or "")).strip()


def parcel_lookup_id(value: object) -> str:
    raw = clean(value)
    digits = "".join(re.findall(r"\d", raw))
    if len(digits) >= 14:
        return digits
    return raw.replace(" ", "")


def parcel_key(value: object) -> str:
    return "".join(character for character in clean(value).upper() if character.isalnum())


def html_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value)
    return clean(html.unescape(re.sub(r"<[^>]+>", " ", value)))


def amount(value: str) -> float:
    try:
        return float(value.replace("$", "").replace(",", "").strip())
    except ValueError:
        return 0.0


def session() -> requests.Session:
    if not hasattr(thread_local, "session"):
        current = requests.Session()
        current.headers["User-Agent"] = "LeadCurate/1.0 public-record verification"
        current.get(SOURCE_URL, timeout=30).raise_for_status()
        thread_local.session = current
    return thread_local.session


def parse_result(parcel: str, body: str) -> dict[str, object]:
    text = html_text(body)
    year_pattern = re.compile(
        r"Tax Year:\s*(\d{4})\s+Tax:\s*\$([\d,]+(?:\.\d{2})?)\s+"
        r"Interest & Fees:\s*\$([\d,]+(?:\.\d{2})?)\s+"
        r"Amount Due:\s*\$([\d,]+(?:\.\d{2})?).{0,80}?Status:\s*([A-Z ]+?)(?=Tax Year:|Totals|$)",
        re.I,
    )
    years = [
        {
            "year": match.group(1), "tax": amount(match.group(2)),
            "interest_and_fees": amount(match.group(3)),
            "amount_due": amount(match.group(4)), "status": clean(match.group(5)).upper(),
        }
        for match in year_pattern.finditer(text)
    ]
    total_match = re.search(
        r"Totals\s*:\s*Total Tax:\s*\$([\d,]+(?:\.\d{2})?)\s+"
        r"Total Interest & Fees:\s*\$([\d,]+(?:\.\d{2})?)\s+"
        r"Total Amount Due:\s*\$([\d,]+(?:\.\d{2})?)",
        text,
        re.I,
    )
    fresh_match = re.search(
        r"PROPERTY TAX INFORMATION IS VALID AS OF BUSINESS DAY\s+(\d{2}/\d{2}/\d{4})",
        text,
        re.I,
    )
    taxpayer_match = re.search(r"Taxpayer\(s\)\s+(.*?)\s+Tax Year", text, re.I)
    address_match = re.search(r"Property Address\s+(.*?)\s+Taxpayer\(s\)", text, re.I)
    total_due = amount(total_match.group(3)) if total_match else sum(float(y["amount_due"]) for y in years)
    if years and total_due > 0:
        status = "current_delinquent_balance_returned"
    elif "The search produced no results" in text:
        status = "no_current_delinquent_record_returned"
    else:
        status = "no_positive_balance_returned"
    return {
        "parcel_key": parcel_key(parcel),
        "lookup_parcel_id": parcel,
        "live_tax_lookup_status": status,
        "live_tax_years": "; ".join(str(item["year"]) for item in years),
        "live_tax_statuses": "; ".join(f"{item['year']}:{item['status']}" for item in years),
        "live_tax_year_detail_json": json.dumps(years, separators=(",", ":")),
        "live_total_tax": amount(total_match.group(1)) if total_match else sum(float(y["tax"]) for y in years),
        "live_total_interest_and_fees": amount(total_match.group(2)) if total_match else sum(float(y["interest_and_fees"]) for y in years),
        "live_total_amount_due": total_due,
        "live_tax_data_as_of": fresh_match.group(1) if fresh_match else "",
        "live_taxpayer": clean(taxpayer_match.group(1)) if taxpayer_match else "",
        "live_property_address": clean(address_match.group(1)) if address_match else "",
        "live_checked_at": datetime.now(timezone.utc).isoformat(),
        "error": "",
    }


def check_parcel(parcel: str, delay: float, timeout: float, attempts: int) -> dict[str, object]:
    error = ""
    for attempt in range(1, attempts + 1):
        try:
            response = session().post(
                SEARCH_URL,
                data={
                    "PARCEL_ID": parcel,
                    "searchByAddressInd": "ParcelSearch",
                    "PARCEL_SEARCH_MSG": "",
                    "frequency": "on",
                },
                timeout=timeout,
            )
            response.raise_for_status()
            result = parse_result(parcel, response.text)
            time.sleep(delay)
            return result
        except requests.RequestException as exc:
            error = f"{type(exc).__name__}: {exc}"
            time.sleep(min(30.0, 2.0**attempt))
            if hasattr(thread_local, "session"):
                del thread_local.session
    return {
        "parcel_key": parcel_key(parcel), "lookup_parcel_id": parcel,
        "live_tax_lookup_status": "request_failed", "live_tax_years": "",
        "live_tax_statuses": "", "live_tax_year_detail_json": "[]",
        "live_total_tax": 0.0, "live_total_interest_and_fees": 0.0,
        "live_total_amount_due": 0.0, "live_tax_data_as_of": "",
        "live_taxpayer": "", "live_property_address": "",
        "live_checked_at": datetime.now(timezone.utc).isoformat(), "error": error,
    }


CHECK_FIELDS = [
    "parcel_key", "lookup_parcel_id", "live_tax_lookup_status", "live_tax_years",
    "live_tax_statuses", "live_tax_year_detail_json", "live_total_tax",
    "live_total_interest_and_fees", "live_total_amount_due", "live_tax_data_as_of",
    "live_taxpayer", "live_property_address", "live_checked_at", "error",
]


def load_checkpoint(path: Path) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    if not path.exists():
        return result
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("parcel_key"):
                result[str(row["parcel_key"])] = row
    return result


def redact(row: dict[str, object]) -> dict[str, object]:
    result = dict(row)
    for key in result:
        if any(
            token in key.lower()
            for token in (
                "owner", "address", "parcel", "taxpayer", "street", "zip", "map_number",
            )
        ):
            result[key] = "REDACTED"
    return result


def run(args: argparse.Namespace) -> dict[str, object]:
    with args.input.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        source_fields = reader.fieldnames or []
        source_rows = list(reader)
    unique_rows: dict[str, dict[str, str]] = {}
    for row in source_rows:
        key = parcel_key(row.get("parcel_id"))
        if key:
            unique_rows.setdefault(key, row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = args.checkpoint or args.output_dir / "wayne-mi-live-tax-checkpoint.jsonl"
    results = load_checkpoint(checkpoint)
    pending = [
        (key, parcel_lookup_id(row.get("parcel_id")))
        for key, row in unique_rows.items()
        if key not in results or results[key].get("live_tax_lookup_status") == "request_failed"
    ]
    if args.limit is not None:
        pending = pending[: args.limit]
    completed = 0
    lock = threading.Lock()
    with checkpoint.open("a", encoding="utf-8") as checkpoint_handle:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(check_parcel, lookup, args.delay, args.timeout, args.attempts): key
                for key, lookup in pending
            }
            for future in as_completed(futures):
                key = futures[future]
                result = future.result()
                with lock:
                    results[key] = result
                    checkpoint_handle.write(json.dumps(result, separators=(",", ":")) + "\n")
                    checkpoint_handle.flush()
                    completed += 1
                    if completed % args.progress_every == 0 or completed == len(pending):
                        print(f"checked={completed}/{len(pending)} cached={len(results)}", flush=True)

    run_date = args.output_dir.name
    lane_dir = args.output_dir / "tax-delinquent"
    lane_dir.mkdir(parents=True, exist_ok=True)
    stem = f"wayne-mi-tax-delinquent-{run_date}"
    full = lane_dir / f"{stem}.csv"
    preview = lane_dir / f"{stem}-preview.csv"
    checks = lane_dir / f"{stem}-live-checks.csv"
    meta = lane_dir / f"{stem}-meta.json"
    fields = [*source_fields, *[field for field in CHECK_FIELDS if field not in source_fields]]
    checked_rows: list[dict[str, object]] = []
    current_rows: list[dict[str, object]] = []
    for key, source in unique_rows.items():
        check = results.get(key)
        if not check:
            continue
        row: dict[str, object] = dict(source)
        row.update(check)
        checked_rows.append(row)
        if check["live_tax_lookup_status"] == "current_delinquent_balance_returned":
            current_rows.append(row)
    for path, rows in ((checks, checked_rows), (full, current_rows)):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    with preview.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(redact(row) for row in current_rows[: args.preview])

    errors = sum(row.get("live_tax_lookup_status") == "request_failed" for row in results.values())
    missing = len(unique_rows) - len(results)
    fresh_dates = sorted(
        {str(row.get("live_tax_data_as_of")) for row in results.values() if row.get("live_tax_data_as_of")}
    )
    verified = errors == 0 and missing == 0 and len(checked_rows) == len(unique_rows)
    payload = {
        "market": "wayne-mi", "lane": "tax-delinquent",
        "status": "verified_live_business_day" if verified else "partial_live_verification",
        "source_url": SOURCE_URL,
        "source_status": "Wayne County Treasurer live delinquent-property lookup",
        "source_data_as_of": fresh_dates,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(args.input),
        "publication_candidates": len(unique_rows),
        "live_checked": len(checked_rows),
        "records": len(current_rows),
        "no_current_positive_balance_returned": sum(
            row.get("live_tax_lookup_status") != "current_delinquent_balance_returned"
            and row.get("live_tax_lookup_status") != "request_failed"
            for row in results.values()
        ),
        "request_failures": errors,
        "unchecked": missing,
        "outputs": {
            "full": str(full), "preview": str(preview), "meta": str(meta),
            "live_checks": str(checks), "checkpoint": str(checkpoint),
        },
        "verification": {
            "full_csv_rows": len(current_rows),
            "unique_parcels_in_full_csv": len({parcel_key(row.get("parcel_id")) for row in current_rows}),
            "duplicate_parcels_in_full_csv": len(current_rows) - len({parcel_key(row.get("parcel_id")) for row in current_rows}),
            "all_publication_candidates_checked": missing == 0,
            "zero_request_failures": errors == 0,
            "only_positive_live_balances_shipped": all(
                float(row["live_total_amount_due"]) > 0 for row in current_rows
            ),
        },
    }
    meta.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--delay", type=float, default=0.75)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--preview", type=int, default=25)
    parser.add_argument("--progress-every", type=int, default=100)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 8:
        parser.error("--workers must be between 1 and 8")
    result = run(args)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "verified_live_business_day" else 1


if __name__ == "__main__":
    raise SystemExit(main())
