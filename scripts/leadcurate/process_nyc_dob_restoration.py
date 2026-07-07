#!/usr/bin/env python3
"""NYC DOB violations -> restoration-contractor lane.

Filters 2.47M DOB violations to ACTIVE, restoration-relevant classes,
groups by building (BIN), scores by severity + volume + recency,
writes full snapshot + redacted-style preview + meta JSON.
"""
import csv
import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, date

SRC = "/opt/leadcurate/raw_imports/nyc/2026-06-19/dob-violations.csv"
OUT_DIR = "/opt/leadcurate/processed/nyc/2026-07-06"
TODAY = date(2026, 7, 6)

BORO = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}

# severity weights by violation category / type keywords
def classify(cat, vtype):
    cat = (cat or "").upper()
    vtype = (vtype or "").upper()
    if "DISMISSED" in cat or "RESOLVED" in cat.upper():
        return None, 0
    if "ACTIVE" not in cat and "FAILURE TO FILE" not in cat:
        return None, 0
    # restoration-relevant classes
    if "HAZARDOUS" in cat or "HAZARDOUS" in vtype:
        return "Hazardous", 50
    if "WORK WITHOUT PERMIT" in cat or "WORK W/O PERMIT" in vtype:
        return "Work Without Permit", 35
    if "FACADE" in vtype or "FISP" in vtype or "LL11" in vtype:
        return "Facade (FISP/LL11)", 45
    if "BOILER" in cat or "BOILER" in vtype:
        return "Boiler", 25
    if "STRUCTURAL" in vtype:
        return "Structural", 45
    if "CONSTRUCTION" in vtype:
        return "Construction", 30
    if "ELEVATOR" in vtype:
        return "Elevator", 20
    if "ACTIVE" in cat:
        return "Other Active", 10
    return None, 0

def parse_date(s):
    s = (s or "").strip()
    if not s:
        return None
    s = re.sub(r"[+-]\d{2}:?\d{0,2}$", "", s).strip()
    for fmt in ("%Y%m%d", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s[:19], fmt).date()
        except ValueError:
            continue
    return None

CLASS_ALIASES = {
    "facade": {"Facade (FISP/LL11)"},
    "hazardous": {"Hazardous"},
    "boiler": {"Boiler"},
    "structural": {"Structural"},
    "wwp": {"Work Without Permit"},
}

def parse_args():
    parser = argparse.ArgumentParser(description="Build NYC DOB restoration contractor cuts.")
    parser.add_argument("--borough", choices=sorted(BORO.values()), help="Limit output to one borough.")
    parser.add_argument("--class", dest="violation_class", choices=sorted(CLASS_ALIASES), help="Limit output to one violation class family.")
    parser.add_argument("--top", type=int, default=150, help="Number of ranked buildings to export.")
    parser.add_argument("--source", default=SRC)
    parser.add_argument("--output-dir", default=OUT_DIR)
    return parser.parse_args()

def main():
    args = parse_args()
    allowed_classes = CLASS_ALIASES.get(args.violation_class or "", set())
    buildings = defaultdict(lambda: {
        "violations": 0, "score": 0, "classes": defaultdict(int),
        "latest_issue": None, "earliest_issue": None,
        "boro": "", "address": "", "bin": "", "block": "", "lot": "",
        "sample_desc": "",
    })
    total = 0
    kept = 0
    with open(args.source, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            cls, weight = classify(row.get("VIOLATION_CATEGORY"), row.get("VIOLATION_TYPE"))
            if not cls:
                continue
            if allowed_classes and cls not in allowed_classes:
                continue
            issued = parse_date(row.get("ISSUE_DATE"))
            # keep only violations issued in last 6 years (active + actionable)
            if issued is None or (TODAY - issued).days > 2190:
                continue
            bin_id = (row.get("BIN") or "").strip()
            house = (row.get("HOUSE_NUMBER") or "").strip()
            street = (row.get("STREET") or "").strip()
            if not bin_id or not street:
                continue
            boro_name = BORO.get((row.get("BORO") or "").strip(), row.get("BORO") or "")
            if args.borough and boro_name != args.borough:
                continue
            kept += 1
            b = buildings[bin_id]
            b["bin"] = bin_id
            b["boro"] = boro_name
            b["address"] = f"{house} {street}".strip()
            b["block"] = (row.get("BLOCK") or "").strip()
            b["lot"] = (row.get("LOT") or "").strip()
            b["violations"] += 1
            b["classes"][cls] += 1
            recency_bonus = max(0, 20 - (TODAY - issued).days // 90)  # newer = hotter
            b["score"] += weight + recency_bonus
            if b["latest_issue"] is None or issued > b["latest_issue"]:
                b["latest_issue"] = issued
                desc = (row.get("DESCRIPTION") or "").strip()
                if desc:
                    b["sample_desc"] = desc[:160]
            if b["earliest_issue"] is None or issued < b["earliest_issue"]:
                b["earliest_issue"] = issued

    ranked = sorted(buildings.values(), key=lambda b: b["score"], reverse=True)
    top = ranked[: max(1, args.top)]

    import os
    os.makedirs(args.output_dir, exist_ok=True)
    suffix = ""
    if args.borough:
        suffix += "-" + args.borough.lower().replace(" ", "-")
    if args.violation_class:
        suffix += "-" + args.violation_class
    if args.top != 150:
        suffix += f"-top{args.top}"
    full_path = f"{args.output_dir}/nyc-dob-active-restoration-2026-07-06{suffix}.csv"
    prev_path = f"{args.output_dir}/nyc-dob-active-restoration-2026-07-06{suffix}-preview.csv"
    meta_path = f"{args.output_dir}/nyc-dob-active-restoration-2026-07-06{suffix}-meta.json"

    cols = ["rank", "score", "borough", "property_address", "bin", "block", "lot",
            "active_violations", "violation_classes", "latest_issue_date",
            "earliest_issue_date", "latest_description", "lane", "county", "state"]
    with open(full_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i, b in enumerate(top, 1):
            classes_str = "; ".join(f"{k} x{v}" for k, v in sorted(b["classes"].items(), key=lambda kv: -kv[1]))
            w.writerow([i, b["score"], b["boro"], b["address"], b["bin"], b["block"], b["lot"],
                        b["violations"], classes_str,
                        b["latest_issue"].isoformat() if b["latest_issue"] else "",
                        b["earliest_issue"].isoformat() if b["earliest_issue"] else "",
                        b["sample_desc"], "code_violation_restoration", "NYC (5 boroughs)", "NY"])

    # preview: top 25, address partially redacted (keep street, blur house number)
    with open(prev_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i, b in enumerate(top[:25], 1):
            addr = b["address"]
            parts = addr.split(" ", 1)
            red = (parts[0][0] + "**" if parts[0] else "**") + (" " + parts[1] if len(parts) > 1 else "")
            classes_str = "; ".join(f"{k} x{v}" for k, v in sorted(b["classes"].items(), key=lambda kv: -kv[1]))
            w.writerow([i, b["score"], b["boro"], red, "REDACTED", "", "",
                        b["violations"], classes_str,
                        b["latest_issue"].isoformat() if b["latest_issue"] else "",
                        b["earliest_issue"].isoformat() if b["earliest_issue"] else "",
                        b["sample_desc"], "code_violation_restoration", "NYC (5 boroughs)", "NY"])

    # class distribution for the sample page
    class_totals = defaultdict(int)
    for b in ranked:
        for k, v in b["classes"].items():
            class_totals[k] += v
    boro_totals = defaultdict(int)
    for b in ranked:
        boro_totals[b["boro"]] += 1

    meta = {
        "lane": "code_violation_restoration",
        "source": "NYC Open Data — DOB Violations (full citywide extract)",
        "source_pull_date": "2026-06-19",
        "processed_date": "2026-07-06",
        "filters": {
            "borough": args.borough,
            "class": args.violation_class,
            "top": args.top,
        },
        "total_source_rows": total,
        "active_relevant_violations_last6y": kept,
        "buildings_with_active_relevant": len(buildings),
        "top_n_exported": len(top),
        "class_distribution": dict(sorted(class_totals.items(), key=lambda kv: -kv[1])),
        "borough_building_counts": dict(sorted(boro_totals.items(), key=lambda kv: -kv[1])),
        "top10_preview": [
            {"rank": i, "borough": b["boro"], "violations": b["violations"],
             "score": b["score"],
             "classes": dict(b["classes"]),
             "latest": b["latest_issue"].isoformat() if b["latest_issue"] else ""}
            for i, b in enumerate(top[:10], 1)
        ],
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(json.dumps({"total": total, "kept": kept,
                      "buildings": len(buildings), "exported": len(top),
                      "class_distribution": meta["class_distribution"],
                      "borough_counts": meta["borough_building_counts"]}, indent=2))

if __name__ == "__main__":
    sys.exit(main())
