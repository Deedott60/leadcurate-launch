import csv, sys

path = "/opt/leadcurate/processed/massachusetts-statewide/2026-07-15/tired-landlords/massachusetts-statewide-tired-landlords-2026-07-15.csv"
csv.field_size_limit(100_000_000)

total = 0
out_of_state = 0
diff_city = 0
same_city_same_state = 0

with open(path, newline="", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        total += 1
        own_state = (row.get("OWN_STATE") or "").strip().upper()
        own_city = (row.get("OWN_CITY") or "").strip().upper()
        prop_city = (row.get("CITY") or "").strip().upper()
        if own_state and own_state != "MA":
            out_of_state += 1
        elif own_city and prop_city and own_city != prop_city:
            diff_city += 1
        else:
            same_city_same_state += 1

print("total tired-landlord rows:", total)
print("strong signal, owner out of state:", out_of_state)
print("strong signal, owner in different MA city:", diff_city)
print("weak signal, same city or unresolvable (possible formatting mismatch):", same_city_same_state)
print("strong pct:", round((out_of_state + diff_city) / total * 100, 1))
