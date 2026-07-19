#!/usr/bin/env python3
"""Write the required 19-row Dollar Leads audit for every live market."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CATALOG = [
    "tax-debt", "recorded-tax-liens", "tax-sale", "pre-foreclosure", "probate",
    "code-violations", "property-liens", "absentee-owners", "out-of-state-owners",
    "tired-landlords", "high-equity", "individual-homeowner", "entity-owned",
    "verified-vacant-land", "active-permits", "office", "industrial", "multifamily",
    "blight-pressure",
]
MARKETS = {
    "fulton-ga": "Fulton County GA (Atlanta)",
    "shelby-tn": "Shelby County TN (Memphis)",
    "dallas-tx": "Dallas County TX",
    "wayne-mi": "Wayne County MI",
    "cook-il": "Cook County IL",
    "massachusetts-statewide": "Massachusetts (statewide)",
    "mecklenburg-nc": "Mecklenburg County NC (Charlotte)",
}

# These are evidence findings from the 2026-07-19 source audit. A lane with a
# verified file or live inventory always takes precedence over this mapping.
GAPS: dict[str, dict[str, tuple[str, str]]] = {
    "fulton-ga": {
        "pre-foreclosure": ("unavailable", "The current Sheriff levy-sale notice does not identify a verified row-level mortgage-foreclosure subset."),
        "probate": ("unavailable", "Fulton Probate Court offers case search, but no current property-address or parcel-key bulk export."),
        "code-violations": ("unavailable", "No current countywide official parcel-key bulk export of open code cases was identified; Atlanta's portal is city-only and its current export was not accessible."),
        "property-liens": ("unavailable", "No current countywide unrestricted parcel-key municipal, mechanic, or judgment-lien bulk source was identified."),
        "tired-landlords": ("unavailable", "The current certified parcel service has no last-sale or deed date, so 10-year tenure cannot be proven."),
        "active-permits": ("unavailable", "Atlanta publishes a city-only permit dashboard, but a current reusable parcel/address bulk export was not accessible for this cycle."),
        "blight-pressure": ("unavailable", "No current countywide official parcel-key blight feed was identified; the available Atlanta material is partial and not exportable as a verified current lane."),
    },
    "shelby-tn": {
        "recorded-tax-liens": ("unavailable", "The official property-transaction export stops at 2025-12-19, so it cannot prove a current 2026 recorded-tax-lien lane."),
        "pre-foreclosure": ("unavailable", "The official Shelby foreclosure map service ends in April 2018 and is too stale for a current product."),
        "probate": ("unavailable", "Shelby Probate Court does not publish a current parcel-address bulk export."),
        "property-liens": ("unavailable", "The official transaction export stops at 2025-12-19 and no current parcel-key mechanic/judgment-lien bulk feed was available."),
        "tired-landlords": ("unavailable", "The certified parcel service has no last-sale date, so 10-year ownership cannot be derived."),
        "high-equity": ("unavailable", "The certified parcel service exposes neither assessed/appraised value nor mortgage balances, so an equity proxy cannot be derived."),
    },
    "dallas-tx": {
        "recorded-tax-liens": ("unavailable", "Dallas County Clerk moved current post-2026-02-24 records to an interactive publicsearch.us portal with no unrestricted reusable bulk export."),
        "pre-foreclosure": ("unavailable", "Current foreclosure notices are in the County Clerk publicsearch.us interactive portal; no unrestricted current bulk export was available."),
        "probate": ("unavailable", "Dallas probate search does not publish a current property-address or parcel-key bulk export."),
        "code-violations": ("unavailable", "The official open code dataset contains 2018 records and is too stale to sell as current."),
        "property-liens": ("unavailable", "Current recorder lien records are searchable interactively but not available as an unrestricted parcel-key bulk export."),
        "active-permits": ("unavailable", "The official downloadable permit sample contains 2019-2020 records and is too stale to sell as current."),
        "blight-pressure": ("unavailable", "The available official code source is stale at 2018, so it cannot support a current blight lane."),
    },
    "wayne-mi": {
        "tax-sale": ("unavailable", "The current county sources prove positive tax debt but do not expose a distinct current scheduled-sale parcel file."),
        "probate": ("unavailable", "Wayne probate search does not publish a current property-address or parcel-key bulk export."),
        "property-liens": ("unavailable", "No current countywide unrestricted parcel-key municipal, mechanic, and judgment-lien bulk source was identified."),
        "active-permits": ("unavailable", "The Detroit permit dataset was last updated in September 2025 and no current countywide permit bulk source was available."),
    },
    "cook-il": {
        "tax-debt": ("unavailable", "The current Cook Treasurer delinquency list is restricted; the unrestricted public dataset is stale."),
        "recorded-tax-liens": ("unavailable", "Current Recorder lien search is interactive and no unrestricted parcel-key bulk export was available."),
        "tax-sale": ("unavailable", "The current Treasurer tax-sale list is restricted; the unrestricted public sale files are stale."),
        "pre-foreclosure": ("unavailable", "The current Clerk foreclosure search is interactive; the downloadable foreclosure dataset ends in 2015."),
        "probate": ("unavailable", "Cook probate search does not publish a current property-address or PIN bulk export."),
        "property-liens": ("unavailable", "No current unrestricted Recorder or countywide municipal parcel-key lien bulk export was available."),
    },
    "massachusetts-statewide": {
        "tax-sale": ("unavailable", "A Land Court tax-lien filing is not proof of a currently scheduled tax sale; no statewide scheduled-sale parcel source exists."),
        "probate": ("unavailable", "Massachusetts probate search does not publish a statewide property-address or parcel-key bulk export."),
        "code-violations": ("unavailable", "Code enforcement is published municipality by municipality; no current statewide official parcel-key bulk source exists."),
        "property-liens": ("unavailable", "Registry and municipal lien records are decentralized and no current statewide parcel-key bulk export exists."),
        "active-permits": ("unavailable", "Building permits are municipality-specific; no current statewide official parcel-key permit bulk source exists."),
        "blight-pressure": ("unavailable", "Blight and unsafe-building records are municipality-specific; no current statewide official parcel-key bulk source exists."),
    },
    "mecklenburg-nc": {
        "tax-debt": ("unavailable", "The current parcel roll does not prove an unpaid tax balance, and no current full parcel-key delinquency export was available."),
        "recorded-tax-liens": ("unavailable", "The live Charlotte municipal-lien source does not establish a distinct recorded tax-lien status."),
        "tax-sale": ("unavailable", "No current official scheduled tax-sale parcel bulk file was available for this cycle."),
        "pre-foreclosure": ("unavailable", "The parcel roll does not prove a foreclosure filing, and no current official parcel-key notice bulk export was available."),
        "probate": ("unavailable", "The court material available does not provide a current verified parcel-address bulk join; keyword inference is prohibited."),
        "active-permits": ("unavailable", "The open catalog exposes zoning review areas and special-use permits, not a current parcel-level active building-permit bulk lane."),
    },
}


def find_meta(processed: Path, market: str, lane: str, run_date: str) -> dict[str, Any] | None:
    lane_dir = processed / market / run_date / lane
    preferred = lane_dir / f"{market}-{lane}-{run_date}-meta.json"
    candidates = [preferred] if preferred.exists() else sorted(lane_dir.glob("*-meta.json"))
    if not candidates:
        return None
    return json.loads(candidates[-1].read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--processed-root", type=Path, default=Path("/opt/leadcurate/processed"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    live = {(item["market"], item["lane"]): item for item in inventory["lanes"]}
    args.output_dir.mkdir(parents=True, exist_ok=True)

    all_results: dict[str, Any] = {}
    for market, display in MARKETS.items():
        rows: list[dict[str, Any]] = []
        for lane in CATALOG:
            manifest = live.get((market, lane))
            meta = find_meta(args.processed_root, market, lane, args.date)
            if manifest:
                rows.append({
                    "lane": lane, "status": "live", "reason": "Verified source cut into live non-overlapping numbered batches.",
                    "source_name": manifest.get("source_name"), "source_url": manifest.get("source_url"),
                    "source_data_as_of": (meta or {}).get("source_data_as_of"),
                    "eligible_records": manifest.get("eligible_records"), "batched_records": manifest.get("batched_records"),
                    "batch_count": manifest.get("batch_count"), "remainder_records": manifest.get("remainder_records", 0),
                })
                continue
            meta_status = (meta or {}).get("status")
            records = int((meta or {}).get("records") or (meta or {}).get("record_count") or 0)
            if meta_status == "verified":
                reason = f"Verified {records} records, below the 50-record store minimum." if records < 50 else f"Verified {records} records; batch cut is still pending."
                rows.append({
                    "lane": lane, "status": "buildable-not-yet-built", "reason": reason,
                    "source_name": meta.get("source_name"), "source_url": meta.get("source_url"),
                    "source_data_as_of": meta.get("source_data_as_of"), "eligible_records": records,
                    "batched_records": 0, "batch_count": 0, "remainder_records": records,
                })
                continue
            gap = GAPS.get(market, {}).get(lane)
            if gap:
                status, reason = gap
            elif meta and meta.get("unavailable_reason"):
                status, reason = "unavailable", meta["unavailable_reason"]
            else:
                raise RuntimeError(f"no audited outcome for {market}/{lane}")
            rows.append({
                "lane": lane, "status": status, "reason": reason,
                "source_name": (meta or {}).get("source_name"), "source_url": (meta or {}).get("source_url"),
                "source_data_as_of": (meta or {}).get("source_data_as_of"),
                "eligible_records": records, "batched_records": 0, "batch_count": 0, "remainder_records": records,
            })
        if len(rows) != 19 or {row["lane"] for row in rows} != set(CATALOG):
            raise RuntimeError(f"{market}: audit is not exactly 19 unique catalog lanes")
        counts = Counter(row["status"] for row in rows)
        payload = {
            "market": market, "market_display": display, "audit_date": args.date,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "standard": "Dollar Leads Minimum Lane Standard", "catalog_lane_count": 19,
            "summary": dict(counts), "lanes": rows,
        }
        (args.output_dir / f"{market}-19-lane-audit.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        market_manifest = args.inventory.parent / market / "catalog-manifest.json"
        market_manifest.parent.mkdir(parents=True, exist_ok=True)
        market_manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        md = [f"# {display}: 19-lane Dollar Leads audit", "", f"Audit date: {args.date}", "", "| Lane | Status | Records batched | Batches | Reason |", "|---|---:|---:|---:|---|"]
        for row in rows:
            reason = str(row["reason"]).replace("|", "/")
            md.append(f"| {row['lane']} | {row['status']} | {row['batched_records']} | {row['batch_count']} | {reason} |")
        (args.output_dir / f"{market}-19-lane-audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        all_results[market] = payload["summary"]
    inventory["catalog_standard"] = "Dollar Leads Minimum Lane Standard"
    inventory["catalog_lane_count_per_market"] = 19
    inventory["catalog_audited_at_utc"] = datetime.now(timezone.utc).isoformat()
    inventory["catalog_audits"] = {
        market: {
            "manifest": str(args.inventory.parent / market / "catalog-manifest.json"),
            "summary": summary,
        }
        for market, summary in all_results.items()
    }
    pending = args.inventory.with_name(f".{args.inventory.name}.audit-pending")
    pending.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    pending.replace(args.inventory)
    print(json.dumps(all_results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
