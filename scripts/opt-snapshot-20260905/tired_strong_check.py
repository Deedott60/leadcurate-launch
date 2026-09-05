import csv

csv.field_size_limit(100_000_000)

def split(path, own_state_f, own_city_f, prop_city_f, home_state):
    total = oos = diff_city = weak = 0
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            total += 1
            os_ = (row.get(own_state_f) or "").strip().upper()
            oc = (row.get(own_city_f) or "").strip().upper()
            pc = (row.get(prop_city_f) or "").strip().upper()
            if os_ and os_ != home_state:
                oos += 1
            elif oc and pc and oc != pc:
                diff_city += 1
            else:
                weak += 1
    return total, oos, diff_city, weak

jobs = [
    ("dallas", "/opt/leadcurate/processed/dallas-tx/2026-07-15/tired-landlords/dallas-tx-tired-landlords-2026-07-15.csv",
     "OWNER_STATE", "OWNER_CITY", "PROPERTY_CITY", "TX"),
    ("cook", "/opt/leadcurate/processed/cook-il/2026-07-15/tired-landlords/cook-il-tired-landlords-2026-07-15.csv",
     "ADDR_MAIL_ADDRESS_STATE", "ADDR_MAIL_ADDRESS_CITY_NAME", "ADDR_PROP_ADDRESS_CITY_NAME", "IL"),
]

for name, path, sf, cf, pf, hs in jobs:
    try:
        t, o, d, w = split(path, sf, cf, pf, hs)
        print(f"{name}: total {t} | out_of_state {o} | diff_city {d} | weak_same_city {w} | strong_pct {round((o+d)/t*100,1)}")
    except Exception as e:
        print(f"{name}: ERROR {e}")
