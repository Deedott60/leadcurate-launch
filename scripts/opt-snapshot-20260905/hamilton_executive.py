import sys, csv, re, statistics
sys.path.insert(0, '.')
import process_verified_vacant as pvv

cfg = pvv.MARKETS['hamilton-tn']

ENTITY_PATTERNS = [
    r"\bLLC\b", r"\bL L C\b", r"\bL\.L\.C\.\b",
    r"\bINC\b", r"\bINCORPORATED\b", r"\bCORP\b", r"\bCORPORATION\b",
    r"\bCOMPANY\b", r"\bCO\b",
    r"\bTRUST\b", r"\bTRUSTEE\b", r"\bTRUSTEES\b",
    r"\bPARTNERSHIP\b", r"\bLP\b", r"\bL\.P\.\b",
    r"\bPROPERTIES\b", r"\bPROPERTY\b", r"\bPROPCO\b",
    r"\bHOLDINGS\b", r"\bGROUP\b",
    r"\bASSOC\b", r"\bASSOCIATION\b",
    r"\bASSET\b", r"\bASSETS\b",
    r"\bINVESTMENT\b", r"\bINVESTMENTS\b",
    r"\bENTERPRISE\b", r"\bENTERPRISES\b",
    r"\bCHURCH\b", r"\bMINISTRIES\b", r"\bMINISTRY\b",
    r"\bCITY OF\b", r"\bCOUNTY OF\b", r"\bDEPARTMENT\b",
    r"\bAUTHORITY\b", r"\bDISTRICT\b",
    r"\bUNIVERSITY\b", r"\bCOLLEGE\b", r"\bSCHOOL\b",
    r"\bBANK\b", r"\bMORTGAGE\b", r"\bFOUNDATION\b",
    r"\bSFR\b", r"\bBORROWER\b", r"\bREIT\b", r"\bFUND\b",
    r"\bHOA\b", r"\bHOMEOWNERS\b", r"\bCONDOMINIUM\b",
    r"\bDEVELOPMENT\b", r"\bDEVELOPMENTS\b", r"\bDEVELOPER\b",
    r"\bREALTY\b", r"\bRENTALS\b", r"\bLEASING\b",
]
ENTITY_RE = re.compile("|".join(ENTITY_PATTERNS), re.I)
LLC_RE = re.compile(r"\bLLC\b|\bL\.L\.C\.\b", re.I)

rows = []
with open('/opt/leadcurate/raw_imports/hamilton-tn/2026-07-04/AssessorExport.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, fieldnames=cfg.get("csv_fields"))
    for row in reader:
        ok, rec = pvv.qualifies(row, cfg)
        if ok:
            ms = pvv.clean(rec["mail_state"]).upper()
            rec['is_absentee_owner'] = 'yes' if ms not in ("", cfg["state"]) else 'no'
            rows.append(rec)

total = len(rows)
land_values = [r['land_value'] for r in rows if r['land_value'] > 0]
acreages = [r['total_acreage'] for r in rows if r['total_acreage'] > 0]

print("total_parcels", total)
print("combined_land_value", sum(land_values))
print("avg_land_value", round(sum(land_values)/len(land_values), 2))
print("median_land_value", statistics.median(land_values))
print("max_land_value", max(land_values))
print("min_land_value_nonzero", min(land_values))
print("p10_land_value", statistics.quantiles(sorted(land_values), n=10)[0])

print("total_acreage", round(sum(acreages), 2))
print("avg_acreage", round(sum(acreages)/len(acreages), 3))
print("median_acreage", statistics.median(acreages))
print("max_acreage", max(acreages))
print("min_acreage", min(acreages))

entity = sum(1 for r in rows if ENTITY_RE.search(r['owner_name'] or ""))
llc = sum(1 for r in rows if LLC_RE.search(r['owner_name'] or ""))
individual = total - entity
print("individual_owned", individual)
print("entity_owned", entity)
print("llc_specifically", llc)

mail_ok = sum(1 for r in rows if pvv.clean(r['mail_city']) and pvv.clean(r['mail_state']) and pvv.clean(r['mail_zip']))
print("mailing_coverage_pct", round(mail_ok / total * 100, 1))

absentee = sum(1 for r in rows if r['is_absentee_owner'] == 'yes')
print("absentee_total", absentee)
absentee_entity = sum(1 for r in rows if r['is_absentee_owner'] == 'yes' and ENTITY_RE.search(r['owner_name'] or ""))
absentee_individual = absentee - absentee_entity
print("absentee_individual", absentee_individual)
print("absentee_entity", absentee_entity)

acre_bands = {"under_1": 0, "1_5": 0, "5_25": 0, "25_plus": 0}
for a in acreages:
    if a < 1: acre_bands["under_1"] += 1
    elif a <= 5: acre_bands["1_5"] += 1
    elif a <= 25: acre_bands["5_25"] += 1
    else: acre_bands["25_plus"] += 1
print("acre_bands", acre_bands)
