#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
page = root / "docs" / "workforce-os" / "index.html"
dashboard = root / "docs" / "command" / "index.html"
errors = []

if not page.exists():
    errors.append("standalone Workforce OS page missing")
else:
    text = page.read_text()
    required = [
        "Workforce OS",
        "wf-nav-overview",
        "wf-nav-relationships",
        "wf-nav-courses",
        "wf-nav-assets",
        "wf-nav-work",
        "wf-nav-conference",
        "0fba0555-5ef0-455d-8bed-5a518db639c0",
        "project_items",
        "project_assets",
        "activity_feed",
        "Dylan Lehr",
        "Michael S. Coone",
    ]
    for item in required:
        if item not in text:
            errors.append(f"missing: {item}")
    for forbidden in ["LeadCurate Projects", "Projects Workspace", "page-reggie"]:
        if forbidden in text:
            errors.append(f"standalone page contains forbidden project UI: {forbidden}")

if not dashboard.exists():
    errors.append("LeadCurate dashboard missing")
else:
    text = dashboard.read_text()
    if "/workforce-os/" not in text:
        errors.append("LeadCurate dashboard does not link to standalone Workforce OS")

if errors:
    print("FAILED")
    for error in errors:
        print("-", error)
    sys.exit(1)
print("PASS: standalone Workforce OS contract")
