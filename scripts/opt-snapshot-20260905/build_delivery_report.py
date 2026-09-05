#!/usr/bin/env python3
"""
Render a branded LeadCurate customer-delivery HTML report from a package folder.
Output: <package>/delivery-report.html — opens in any browser, print-friendly.
"""
import csv
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PACKAGES = Path("/opt/leadcurate/packages")

LANE_DESCRIPTIONS = {
    "pre_foreclosure": "Active court-filed foreclosure cases. Each record has the property address, case number, action-filed date, scheduled sale date, and a days-to-sale countdown. Closer to sale = more urgent.",
    "code_violations_open": "Open building / property maintenance violations from the city inspector. Records flagged Vacant Lot, Vacant Structure, or Abandoned are highest-priority — owner is distressed or absent.",
    "lien_holder_final_orders": "Lien-holder final orders issued by the city. Records include citation amount, hearing schedule, and the owner's mailing state. Out-of-state owners with active final orders are top targets.",
    "city_lien_active": "Active city liens on Charlotte property — filed and unpaid. Owner names include real institutional REI funds and individual absentee owners.",
    "vacant_land": "Vacant land parcels with absentee owners. Filtered to ≥0.10 acres and identifiable owner, ranked by acreage × land value × out-of-state bonus.",
    "absentee_high_value": "Single-family rentals owned by out-of-state entities, $200k+ assessed. Includes institutional SFR funds (BAF, SFR JV, HOME SFR) and individual investors.",
}

# Read which fields to feature per lane in the inline table
LANE_DISPLAY_COLS = {
    "pre_foreclosure": ["rank", "score", "property_address", "neighborhood", "sale_date", "days_to_sale", "case_number"],
    "code_violations_open": ["rank", "score", "property_address", "violation_code", "occupancy_status", "inspection_date", "citation_amount"],
    "lien_holder_final_orders": ["rank", "score", "owner_name", "owner_mail_city", "owner_mail_state", "final_citation_amount", "date_of_notification", "is_out_of_state"],
    "city_lien_active": ["rank", "score", "owner_name", "property_address", "lien_status", "invoice_date"],
    "vacant_land": ["rank", "score", "owner_name", "property_address", "mail_city", "mail_state", "total_acreage", "land_value"],
    "absentee_high_value": ["rank", "score", "owner_name", "mail_city", "mail_state", "property_location", "year_built", "total_value"],
}

COL_LABELS = {
    "rank": "#", "score": "Score",
    "property_address": "Property address",
    "property_partial": "Property",
    "owner_name": "Owner",
    "neighborhood": "Neighborhood",
    "sale_date": "Sale date",
    "days_to_sale": "Days to sale",
    "case_number": "Case #",
    "violation_code": "Violation",
    "occupancy_status": "Occupancy",
    "inspection_date": "Inspected",
    "citation_amount": "Citation",
    "final_citation_amount": "Citation",
    "owner_mail_city": "Mail city",
    "owner_mail_state": "State",
    "date_of_notification": "Notified",
    "is_out_of_state": "Out of state",
    "lien_status": "Status",
    "invoice_date": "Invoiced",
    "mail_city": "Mail city",
    "mail_state": "State",
    "total_acreage": "Acres",
    "land_value": "Land value",
    "year_built": "Built",
    "total_value": "Assessed",
    "property_location": "Property location",
}

PALETTE_CSS = """
:root {
  --ink: #1e293b; --muted: #64748b; --cream: #faf7f2; --stone: #f5f1eb;
  --dark: #0f172a; --emerald: #15803d; --emerald-2: #22c55e; --emerald-soft: #dff4e8;
  --gold: #d97706; --gold-soft: #fef3c7;
  --line: rgba(30,41,59,.12); --shadow: 0 24px 80px rgba(15,23,42,.12); --radius: 24px;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--cream); color: var(--ink); line-height: 1.55; }
.container { width: min(1100px, calc(100% - 40px)); margin: 0 auto; }
header.report-header { padding: 32px 0 24px; border-bottom: 1px solid var(--line);
  background: rgba(255,255,255,0.5); }
.header-row { display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 16px; }
.logo { font-family: "Playfair Display", serif; font-size: 28px; font-weight: 700;
  letter-spacing: -0.04em; color: var(--dark); }
.logo span { color: var(--emerald); }
.badge { display: inline-flex; align-items: center; gap: 8px;
  background: var(--emerald-soft); color: var(--emerald);
  padding: 8px 14px; border-radius: 999px;
  font-size: 12px; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase; }
.doc-meta { font-size: 13px; color: var(--muted); margin-top: 4px; }
section.cover { padding: 56px 0 40px; }
h1 { font-family: "Playfair Display", serif; font-size: clamp(40px, 6vw, 64px);
  line-height: 1; letter-spacing: -0.04em; margin: 16px 0 18px; max-width: 880px; }
.lead { font-size: 18px; color: var(--muted); max-width: 720px; line-height: 1.6; }
section { padding: 40px 0; border-top: 1px solid var(--line); }
section.no-divider { border-top: none; }
h2 { font-family: "Playfair Display", serif; font-size: clamp(28px, 3.4vw, 38px);
  line-height: 1.05; letter-spacing: -0.03em; margin: 0 0 8px; }
h3 { font-size: 18px; font-weight: 700; margin: 22px 0 10px; }
h4 { font-size: 14px; font-weight: 700; color: var(--emerald);
  text-transform: uppercase; letter-spacing: 0.1em; margin: 0 0 6px; }
p { margin: 8px 0 14px; color: #334155; }
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px; margin: 22px 0 8px; }
.metric { background: white; border: 1px solid var(--line); border-radius: 18px; padding: 18px; }
.metric .label { font-size: 12px; color: var(--muted); font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.08em; }
.metric .value { font-size: 30px; font-weight: 800; letter-spacing: -0.03em; margin-top: 4px; color: var(--dark); }
.metric .note { font-size: 12px; color: var(--muted); margin-top: 4px; }
.lane-card { background: white; border: 1px solid var(--line); border-radius: 24px;
  padding: 24px 28px; margin: 22px 0; border-left: 4px solid var(--emerald); }
.lane-card.tier-a { border-left-color: var(--gold); }
.lane-card h3 { margin-top: 0; }
.lane-card .pill { display: inline-block; font-size: 11px; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.12em;
  color: var(--emerald); padding: 4px 10px; background: var(--emerald-soft);
  border-radius: 6px; margin-bottom: 12px; }
.lane-card .stats { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0 14px; }
.stat-pill { display: inline-flex; align-items: center; gap: 6px;
  background: var(--stone); color: var(--ink);
  padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.source-pill { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px;
  background: var(--stone); padding: 4px 8px; border-radius: 4px; color: var(--muted);
  word-break: break-all; display: inline-block; }
.table-wrap { overflow-x: auto; margin: 16px 0 8px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; background: white; border-radius: 12px; overflow: hidden; }
thead th { text-align: left; padding: 10px 12px;
  background: var(--stone); color: var(--ink); font-weight: 700;
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em;
  border-bottom: 1px solid var(--line); }
tbody td { padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
tbody tr:hover { background: var(--stone); }
tbody td.rank { font-weight: 800; color: var(--emerald); }
tbody td.num { text-align: right; font-variant-numeric: tabular-nums; }
.pull-quote { background: var(--dark); color: white;
  padding: 28px 30px; border-radius: 24px; margin: 22px 0;
  font-family: "Playfair Display", serif; font-size: 20px; line-height: 1.4; font-style: italic; }
.pull-quote .cite { display: block; margin-top: 12px;
  font-family: Inter, sans-serif; font-size: 13px; font-style: normal;
  color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
footer { padding: 40px 0 60px; color: var(--muted); border-top: 1px solid var(--line);
  font-size: 13px; margin-top: 40px; }
.callout { background: var(--emerald-soft); border-left: 4px solid var(--emerald);
  padding: 14px 18px; border-radius: 6px; color: #064e3b; font-size: 14px; }
@media print {
  body { background: white; }
  section, .lane-card, .metric-grid { page-break-inside: avoid; }
  header.report-header { background: white; }
  .pull-quote { background: white; color: var(--dark); border: 2px solid var(--dark); }
}
"""


def fmt_cell(col, val):
    if val is None or val == "":
        return ""
    val = str(val)
    if col in ("citation_amount", "final_citation_amount", "land_value", "total_value"):
        try:
            f = float(val.replace(",", "").replace("$", ""))
            return f"${f:,.0f}"
        except Exception:
            return val
    if col == "total_acreage":
        try:
            return f"{float(val):.2f}"
        except Exception:
            return val
    if col == "is_out_of_state":
        return "✓ Yes" if val.lower() == "yes" else val
    if col == "days_to_sale" and val.lstrip("-").isdigit():
        n = int(val)
        if n <= 0:
            return f"{n}"
        return f"{n} days"
    return html.escape(val)


def build_table(lane_meta, rows, display_cols):
    if not rows:
        return "<p>No records.</p>"
    head = "<tr>" + "".join(f"<th>{html.escape(COL_LABELS.get(c, c))}</th>" for c in display_cols) + "</tr>"
    body = ""
    for r in rows:
        body += "<tr>"
        for c in display_cols:
            val = fmt_cell(c, r.get(c, ""))
            cls = "rank" if c == "rank" else ""
            if c in ("score", "total_value", "land_value", "citation_amount", "final_citation_amount", "total_acreage"):
                cls = (cls + " num").strip()
            body += f"<td{(' class=\"' + cls + '\"') if cls else ''}>{val}</td>"
        body += "</tr>"
    return f'<div class="table-wrap"><table><thead>{head}</thead><tbody>{body}</tbody></table></div>'


def load_lane(pkg_dir, lane_slug):
    lane_dir = pkg_dir / "lanes" / lane_slug
    csv_path = next((p for p in lane_dir.glob("*.csv") if "preview" not in p.name), None)
    meta_path = next(lane_dir.glob("*-meta.json"), None)
    meta = json.loads(meta_path.read_text()) if meta_path else {}
    rows = []
    if csv_path:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    return meta, rows, csv_path.name if csv_path else None


def render_report(pkg_dir):
    manifest = json.loads((pkg_dir / "manifest.json").read_text())
    county = manifest["customer_county"]
    state = manifest["state"]
    date = manifest["delivery_date"]
    pkg_id = manifest["package_id"]
    lanes_meta = manifest["lanes"]

    # Sum totals
    total_records = manifest["total_records"]
    lane_count = manifest["lane_count"]

    # Load full lanes
    lane_payloads = []
    for lm in lanes_meta:
        lane_key = lm["lane"]
        slug_map = {
            "pre_foreclosure": "pre-foreclosure",
            "code_violations_open": "code-violations",
            "lien_holder_final_orders": "lien-holder-orders",
            "city_lien_active": "open-city-liens",
            "vacant_land": "vacant-land-specialty",
            "absentee_high_value": "high-value-absentee",
        }
        slug = slug_map.get(lane_key, lane_key.replace("_", "-"))
        meta, rows, fname = load_lane(pkg_dir, slug)
        lane_payloads.append({
            "lane_key": lane_key,
            "slug": slug,
            "meta": meta if meta else lm,
            "rows": rows,
            "fname": fname,
        })

    title = f"LeadCurate · {county} delivery · {date}"

    # Build sections
    metric_html = f"""
    <div class="metric-grid">
      <div class="metric"><div class="label">Delivery county</div>
        <div class="value" style="font-size:18px; font-family:'Playfair Display', serif;">{html.escape(county)}</div>
        <div class="note">{html.escape(state)}</div></div>
      <div class="metric"><div class="label">Delivery date</div>
        <div class="value" style="font-size:20px;">{date}</div>
        <div class="note">freshly pulled from source</div></div>
      <div class="metric"><div class="label">Lanes</div>
        <div class="value">{lane_count}</div>
        <div class="note">distinct distress signals</div></div>
      <div class="metric"><div class="label">Records</div>
        <div class="value">{total_records}</div>
        <div class="note">100 per lane, scored & ranked</div></div>
    </div>
    """

    lanes_html = ""
    for i, p in enumerate(lane_payloads, 1):
        m = p["meta"]
        rows = p["rows"]
        slug = p["slug"]
        product_name = m.get("product_name", slug)
        source_url = m.get("source_url", "")
        source_date = m.get("source_pulled_at", date)
        universe = m.get("filtered_universe", m.get("source_total_rows", len(rows)))
        score_range = m.get("score_range", [0, 0])
        description = LANE_DESCRIPTIONS.get(p["lane_key"], "")
        display_cols = LANE_DISPLAY_COLS.get(p["lane_key"], list(rows[0].keys())[:7] if rows else [])

        table = build_table(m, rows, display_cols)
        stats = [
            f"<span class='stat-pill'>{universe:,} qualified</span>",
            f"<span class='stat-pill'>{len(rows)} ranked</span>",
            f"<span class='stat-pill'>score range {score_range[0]}–{score_range[1]}</span>",
            f"<span class='stat-pill'>source pulled {source_date}</span>",
        ]
        lanes_html += f"""
        <div class="lane-card">
          <span class="pill">Lane {i}</span>
          <h3>{html.escape(product_name)}</h3>
          <p>{html.escape(description)}</p>
          <div class="stats">{''.join(stats)}</div>
          <p style="font-size:13px; color:var(--muted); margin-top:0;">
            <strong>All {len(rows)} shown below.</strong> Full ranked CSV in <code>lanes/{slug}/</code>.
          </p>
          {table}
          <p style="font-size:11px; color:var(--muted); margin-top:12px;">
            Source: <span class="source-pill">{html.escape(source_url[:120])}</span>
          </p>
        </div>
        """

    final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{html.escape(title)}</title>
<meta name="description" content="LeadCurate County Seat delivery report — {html.escape(county)}, {date}." />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">
<style>{PALETTE_CSS}</style>
</head>
<body>

<header class="report-header">
  <div class="container header-row">
    <div>
      <div class="logo">Lead<span>Curate</span>.</div>
      <div class="doc-meta">County Seat delivery report · {pkg_id}</div>
    </div>
    <div class="badge"><span>●</span> Fresh — pulled {date}</div>
  </div>
</header>

<section class="cover no-divider container">
  <h4>For: County Seat customer</h4>
  <h1>Your {html.escape(county)} batch.</h1>
  <p class="lead">This is your monthly County Seat delivery. {lane_count} distinct distress lanes, {total_records} ranked records pulled fresh from official county portals on {date}. Each lane is sold separately so the same record never crosses to another buyer.</p>
</section>

<section class="container">
  <h4>At a glance</h4>
  <h2>The package.</h2>
  {metric_html}
  <div class="callout" style="margin-top:18px;">
    <strong>How to work this report.</strong> Start with the lanes below — they're ranked, so rank 1 is the highest-priority record per lane. The full unranked file for each lane lives in this package as a CSV (in <code>lanes/{{lane-slug}}/</code>). Use this HTML report for quick triage; load the CSVs into your CRM or spreadsheet tool when you're ready to dial in.
  </div>
</section>

<section class="container">
  <h4>Your lanes this month</h4>
  <h2>{lane_count} distress signals, scored and ranked.</h2>
  {lanes_html}
</section>

<section class="container">
  <h4>Freshness</h4>
  <h2>Why this is fresher than the alternatives.</h2>
  <div class="pull-quote">
    "A name that hits the {html.escape(county)} public record on the first of the month is in your batch within days. The same name does not appear in PropStream's data for another 30 to 90 days."
    <span class="cite">LeadCurate freshness posture</span>
  </div>
  <p>LeadCurate pulls directly from official county portals. PropStream, BatchLeads, and DealMachine license property data from CoreLogic, ATTOM, and DataTree — those feeds refresh on a 30–90 day cycle. Every record in this delivery includes its source URL and source pull date so you can verify provenance yourself.</p>
</section>

<section class="container">
  <h4>How to use the data</h4>
  <h2>The workflow your batch is built for.</h2>
  <ol style="font-size:15px; line-height:1.8; color:#334155; padding-left:20px;">
    <li><strong>Triage from this report.</strong> The top 15 of each lane is shown above. The full 100-record file per lane is in <code>lanes/{{lane-slug}}/*.csv</code>.</li>
    <li><strong>Work each lane in rank order.</strong> Rank 1 is the highest-priority record based on freshness + distress + value signals (see <code>meta.json</code> for the per-lane formula).</li>
    <li><strong>Cross-reference mailing vs property address.</strong> Out-of-state mailing addresses are flagged in the data. Out-of-state = absentee = higher motivation in most lanes.</li>
    <li><strong>Skip-trace through your existing tool.</strong> This package ships property-record data only — no phone numbers, no email addresses, no DNC scrub. Run skip trace through PropStream, BatchLeads, BatchData, Skip Genie, or whatever you already use. You stay free of TCPA / DNC compliance burden on our end.</li>
    <li><strong>Mark and exclude records you've worked.</strong> We'll exclude them from your next batch automatically.</li>
  </ol>
</section>

<section class="container">
  <h4>Compliance</h4>
  <h2>What's in the file. What's not.</h2>
  <p><strong>Included:</strong> Property addresses, owner names, mailing addresses, parcel IDs, distress signals, scoring, freshness dates, and the source URL for every record.</p>
  <p><strong>Not included:</strong> Skip-traced phone numbers, email addresses, DNC scrub status. You handle owner contact lookup, skip trace, DNC compliance, TCPA compliance, and outreach decisions on your side.</p>
  <p>LeadCurate provides data and educational tools only. We do not guarantee deals, motivated sellers, or that any record is safe to contact. Your execution closes the deal.</p>
</section>

<footer>
  <div class="container">
    <p><strong>LeadCurate</strong> · County Seat delivery report · {pkg_id} · Delivered {date}</p>
    <p>Source URLs and pull dates are stamped in each lane's <code>meta.json</code>. The matching machine-readable index is at <code>manifest.json</code>. Questions: reply to the email this report was attached to.</p>
    <p>Better data. Cleaner workflow. No hype. Your execution closes the deal.</p>
  </div>
</footer>

</body>
</html>
"""
    out_path = pkg_dir / "delivery-report.html"
    out_path.write_text(final_html, encoding="utf-8")
    print(f"  -> {out_path}  ({out_path.stat().st_size} bytes)")
    return out_path


if __name__ == "__main__":
    targets = sys.argv[1:] or [
        "louisville-ky-2026-06-19",
        "charlotte-nc-2026-06-19",
    ]
    for pid in targets:
        pdir = PACKAGES / pid
        if not pdir.exists():
            print(f"!! package not found: {pdir}")
            continue
        print(f"\n=== {pid} ===")
        render_report(pdir)
