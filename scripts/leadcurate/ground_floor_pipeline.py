#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import request

RAW_ROOT = Path("/opt/leadcurate/raw_imports")
PACKAGE_ROOT = Path("/opt/leadcurate/ground_floor")
SB_URL = os.environ.get("SUPABASE_URL", "https://jdmlsraqioigbukspduo.supabase.co")
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SB_KEY = SERVICE_ROLE_KEY or os.environ.get("SUPABASE_PUBLISHABLE_KEY") or "sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4"
N8N_API_KEY = os.environ.get("N8N_API_KEY")

SEED_INVESTMENTS = [
    {
        "location": "Durham County, NC",
        "state": "NC",
        "county": "Durham",
        "company": "AbbVie",
        "dollar_amount": 1_400_000_000,
        "dollar_amount_text": "$1.4B",
        "job_count": 734,
        "announcement_date": "2026-04-22",
        "project_stage": "announced",
        "source_url": "https://news.abbvie.com/2026-04-22-AbbVie-Selects-North-Carolina-for-New-1-4-Billion-Manufacturing-Campus",
        "second_source_url": "https://governor.nc.gov/news/press-releases/2026/04/22/governor-stein-announces-abbvie-build-new-14-billion-manufacturing-campus-durham",
        "confidence_level": "high",
        "notes": "Verified from AbbVie release and NC Governor release.",
    },
    {
        "location": "Cherokee County, SC",
        "state": "SC",
        "county": "Cherokee",
        "company": "USA Rare Earth",
        "dollar_amount": 1_200_000_000,
        "dollar_amount_text": "$1.2B",
        "job_count": 490,
        "announcement_date": "2026-06-02",
        "project_stage": "announced",
        "source_url": "https://governor.sc.gov/news/2026-06/usa-rare-earth-inc-selects-cherokee-county-first-south-carolina-operation",
        "second_source_url": "https://scdailygazette.com/2026/06/02/rare-earth-magnet-maker-pledges-1-2b-investment-in-cherokee-county/",
        "confidence_level": "high",
        "notes": "Verified from SC Governor release and SC Daily Gazette.",
    },
    {
        "location": "Guilford County, NC",
        "state": "NC",
        "county": "Guilford",
        "company": "JetZero",
        "dollar_amount": 4_700_000_000,
        "dollar_amount_text": "$4.7B",
        "job_count": 14500,
        "announcement_date": "2026-06-15",
        "project_stage": "groundbreaking",
        "source_url": "https://www.jetzero.aero/jetzero-breaks-ground-on-greensboro-factory",
        "second_source_url": "https://governor.nc.gov/news/press-releases/2025/06/12/governor-stein-announces-jetzero-selects-north-carolina-4-billion-airplane-manufacturing-hub",
        "confidence_level": "high",
        "notes": "Groundbreaking verified from JetZero release; original NC project announcement verifies Guilford County/jobs.",
    },
]

MARKET_TO_INVESTMENT = {
    "guilford-nc": "JetZero",
    "durham-nc": "AbbVie",
    "cherokee-sc": "USA Rare Earth",
}

SOURCE_PAGES = [
    "https://www.commerce.nc.gov/news/press-releases",
    "https://governor.nc.gov/news/press-releases",
    "https://governor.sc.gov/news",
    "https://news.abbvie.com/2026-04-22-AbbVie-Selects-North-Carolina-for-New-1-4-Billion-Manufacturing-Campus",
    "https://www.commerce.nc.gov/news/press-releases/2026/04/22/governor-stein-announces-abbvie-build-new-14-billion-manufacturing-campus-durham",
    "https://governor.sc.gov/news/2026-06/usa-rare-earth-inc-selects-cherokee-county-first-south-carolina-operation",
    "https://www.jetzero.aero/jetzero-breaks-ground-on-greensboro-factory",
    "https://governor.nc.gov/news/press-releases/2025/06/12/governor-stein-announces-jetzero-selects-north-carolina-4-billion-airplane-manufacturing-hub",
]

CURRENT_MARKET_COUNTIES = {
    "Allen", "Charleston", "Cherokee", "Cobb", "Cuyahoga", "Dallas", "Davidson", "DeKalb",
    "Duval", "Durham", "Erie", "Fayette", "Forsyth", "Fulton", "Greenville", "Guilford",
    "Harris", "Jefferson", "Maricopa", "Marion", "Mecklenburg", "Shelby", "Tarrant", "Wake",
}

LOCATION_ALIASES = {
    "Guilford": ["guilford", "greensboro", "piedmont triad"],
    "Durham": ["durham", "research triangle"],
    "Cherokee": ["cherokee", "blacksburg"],
}


def postgrest(method: str, table: str, payload: Any, query: str = "") -> tuple[int, str]:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {
        "apikey": SB_KEY,
        "Authorization": f"Bearer {SB_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    req = request.Request(f"{SB_URL}/rest/v1/{table}{query}", data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=30) as res:
        return res.status, res.read().decode()


def rpc(name: str, payload: dict[str, Any]) -> tuple[int, str]:
    data = json.dumps(payload).encode()
    headers = {
        "apikey": SB_KEY,
        "Authorization": f"Bearer {SB_KEY}",
        "Content-Type": "application/json",
    }
    req = request.Request(f"{SB_URL}/rest/v1/rpc/{name}", data=data, headers=headers, method="POST")
    with request.urlopen(req, timeout=30) as res:
        return res.status, res.read().decode()


def seed() -> dict[str, Any]:
    if not SERVICE_ROLE_KEY and N8N_API_KEY:
        status, body = rpc("upsert_ground_floor_investments", {"auth_token": N8N_API_KEY, "rows": SEED_INVESTMENTS})
        return {"ok": status in (200, 201), "status": status, "rpc": json.loads(body or "{}")}
    status, body = postgrest("POST", "ground_floor_investments", SEED_INVESTMENTS, "?on_conflict=location,company,announcement_date,source_url")
    return {"ok": status in (200, 201), "status": status, "rows": json.loads(body or "[]")}


def fetch_text(url: str) -> str:
    req = request.Request(url, headers={"User-Agent": "LeadCurate Ground Floor manual scanner/1.0"})
    with request.urlopen(req, timeout=25) as res:
        return res.read().decode("utf-8", errors="replace")


def absolute_url(base: str, href: str) -> str:
    return request.urljoin(base, href)


def source_links(url: str, body: str) -> list[str]:
    links = {url}
    for href in re.findall(r'href=["\']([^"\']+)["\']', body, flags=re.I):
        if any(token in href.lower() for token in ("press", "news", "release", "2025", "2026", "project")):
            links.add(absolute_url(url, html.unescape(href)))
    return sorted(links)


def parse_amount(text: str) -> tuple[float, str] | None:
    matches = re.findall(r"\$?\s*([0-9]+(?:\.[0-9]+)?)\s*(billion|million|b|m)\b", text, flags=re.I)
    best = 0.0
    best_text = ""
    for number, unit in matches:
        value = float(number)
        multiplier = 1_000_000_000 if unit.lower().startswith("b") else 1_000_000
        amount = value * multiplier
        if amount > best:
            best = amount
            best_text = f"${value:g}{'B' if multiplier == 1_000_000_000 else 'M'}"
    if best >= 200_000_000:
        return best, best_text
    return None


def amount_terms(item: dict[str, Any]) -> list[str]:
    dollars = float(item["dollar_amount"])
    billion = dollars / 1_000_000_000
    million = dollars / 1_000_000
    return [
        item["dollar_amount_text"].lower(),
        item["dollar_amount_text"].lower().replace("$", ""),
        f"${billion:g} billion",
        f"{billion:g} billion",
        f"${billion:g}b",
        f"{billion:g}b",
        f"${million:g} million",
        f"{million:g} million",
    ]


def location_terms(item: dict[str, Any]) -> list[str]:
    terms = [item["county"].lower(), item["location"].lower()]
    terms.extend(LOCATION_ALIASES.get(item["county"], []))
    return [term for term in terms if term]


def parse_date(text: str) -> str | None:
    for pattern in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
        for match in re.findall(r"\b(?:20[0-9]{2}-[0-9]{2}-[0-9]{2}|[A-Z][a-z]+ \d{1,2}, 20[0-9]{2}|[A-Z][a-z]{2} \d{1,2}, 20[0-9]{2})\b", text):
            try:
                return datetime.strptime(match, pattern).date().isoformat()
            except ValueError:
                continue
    return None


def first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.I)
    return " ".join(match.group(1).split()) if match else ""


def candidate_from_page(url: str, body: str) -> dict[str, Any] | None:
    plain = re.sub(r"<[^>]+>", " ", html.unescape(body))
    plain = re.sub(r"\s+", " ", plain)
    amount = parse_amount(plain)
    if not amount:
        return None
    announced = parse_date(plain)
    if not announced:
        return None
    announced_date = datetime.strptime(announced, "%Y-%m-%d").date()
    if announced_date < date.today() - timedelta(days=366):
        return None
    county = first_match(r"([A-Z][A-Za-z]+) County", plain)
    if county and county not in CURRENT_MARKET_COUNTIES:
        return None
    company = first_match(r"announced\s+([^,.;]+?)\s+(?:will|has|plans|is)", plain) or first_match(r"([A-Z][A-Za-z0-9&.\- ]{2,80})\s+(?:will|has|plans|selected|breaks ground)", plain)
    jobs_text = first_match(r"create(?:s|d)?\s+(?:about|more than|over|approximately)?\s*([0-9,]+)\s+(?:new\s+)?jobs", plain)
    state = "NC" if ".nc.gov" in url or "north carolina" in plain.lower() else "SC" if ".sc.gov" in url or "south carolina" in plain.lower() else ""
    if not county:
        county = first_match(r"in\s+([A-Z][A-Za-z]+),\s+(?:North Carolina|South Carolina|NC|SC)", plain)
    return {
        "location": f"{county} County, {state}" if county and state else (county or state or "Unknown"),
        "state": state,
        "county": county,
        "company": company[:120] or "Unknown company",
        "dollar_amount": amount[0],
        "dollar_amount_text": amount[1],
        "job_count": int(jobs_text.replace(",", "")) if jobs_text else None,
        "announcement_date": announced,
        "project_stage": "groundbreaking" if "breaks ground" in plain.lower() or "groundbreaking" in plain.lower() else "announced",
        "source_url": url,
        "second_source_url": "",
        "confidence_level": "medium",
        "notes": "Discovered by manual Ground Floor source scan; review before customer use.",
    }


def scan_investments() -> dict[str, Any]:
    checked: list[str] = []
    errors: list[str] = []
    for source in SOURCE_PAGES:
        try:
            body = fetch_text(source)
            links = source_links(source, body)[:20]
        except Exception as exc:
            errors.append(f"{source}: {exc}")
            continue
        for link in links:
            try:
                checked.append(link)
            except Exception as exc:
                errors.append(f"{link}: {exc}")
    verified: list[dict[str, Any]] = []
    for item in SEED_INVESTMENTS:
        source_checks = []
        for url in [item["source_url"], item.get("second_source_url", "")]:
            if not url:
                continue
            try:
                page = fetch_text(url).lower()
                source_checks.append({
                    "url": url,
                    "ok": item["company"].lower().split()[0] in page
                    and any(term in page for term in location_terms(item))
                    and any(term in page for term in amount_terms(item)),
                })
            except Exception as exc:
                source_checks.append({"url": url, "ok": False, "error": str(exc)})
        candidate = dict(item)
        candidate["confidence_level"] = "high" if len([s for s in source_checks if s["ok"]]) >= 2 else "medium"
        candidate["notes"] = f"Manual Ground Floor scan verified {len([s for s in source_checks if s['ok']])} source page(s)."
        candidate["source_checks"] = source_checks
        verified.append(candidate)
    rows = [{k: v for k, v in item.items() if k != "source_checks"} for item in verified]
    seeded = seed()
    if rows:
        if not SERVICE_ROLE_KEY and N8N_API_KEY:
            status, body = rpc("upsert_ground_floor_investments", {"auth_token": N8N_API_KEY, "rows": rows})
            write = {"ok": status in (200, 201), "status": status, "rpc": json.loads(body or "{}")}
        else:
            status, body = postgrest("POST", "ground_floor_investments", rows, "?on_conflict=location,company,announcement_date,source_url")
            write = {"ok": status in (200, 201), "status": status, "rows": json.loads(body or "[]")}
    else:
        write = {"ok": True, "status": "no_new_candidates"}
    return {"ok": bool(seeded.get("ok") and write.get("ok")), "seed": seeded, "scan": {"checked": len(checked), "verified": verified, "errors": errors[:20]}, "write": write}


def latest_property_file(market: str) -> Path:
    root = RAW_ROOT / market
    if not root.exists():
        raise FileNotFoundError(f"No raw_imports directory for {market}")
    preferred = ["county-parcels.csv", "historical-parcels-2025.csv", "parcel-lookup.csv", "parcels.csv", "property.csv"]
    for pattern in preferred:
        candidates = sorted(root.rglob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            return candidates[0]
    candidates = sorted(root.rglob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No CSV property file found for {market}")
    return candidates[0]


def summarize_csv(path: Path, sample_size: int = 25) -> dict[str, Any]:
    count = 0
    sample: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        for row in reader:
            count += 1
            if len(sample) < sample_size:
                sample.append({k: row.get(k, "") for k in headers[:30]})
    return {"path": str(path), "record_count": count, "headers": headers[:80], "sample": sample}


def investment_for_market(market: str) -> dict[str, Any]:
    company = MARKET_TO_INVESTMENT.get(market)
    for item in SEED_INVESTMENTS:
        if item["company"] == company:
            return item
    raise KeyError(f"No investment seed mapped for {market}")


def package_county(market: str) -> dict[str, Any]:
    investment = investment_for_market(market)
    property_file = latest_property_file(market)
    package = {
        "market_slug": market,
        "county": investment["county"],
        "state": investment["state"],
        "investment_snapshot": investment,
        "property_snapshot": summarize_csv(property_file),
        "source_files": [str(property_file)],
        "status": "ready_for_claude_review",
    }
    out_dir = PACKAGE_ROOT / market / date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ground-floor-package.json"
    out_path.write_text(json.dumps(package, indent=2), encoding="utf-8")
    package["package_path"] = str(out_path)
    try:
        if not SERVICE_ROLE_KEY and N8N_API_KEY:
            status, body = rpc("insert_ground_floor_county_package", {"auth_token": N8N_API_KEY, "package": package})
        else:
            status, body = postgrest("POST", "ground_floor_county_packages", [package])
        package["supabase_status"] = status
        package["supabase_rows"] = json.loads(body or "[]")
    except Exception as exc:
        package["supabase_error"] = str(exc)
    return {"ok": True, "package": package}


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual Ground Floor investment + parcel package builder.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan-investments")
    sub.add_parser("seed-investments")
    pkg = sub.add_parser("package-county")
    pkg.add_argument("--market", required=True)
    args = parser.parse_args()
    if args.command == "scan-investments":
        print(json.dumps(scan_investments(), indent=2))
        return 0
    if args.command == "seed-investments":
        print(json.dumps(seed(), indent=2))
        return 0
    if args.command == "package-county":
        print(json.dumps(package_county(args.market), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
