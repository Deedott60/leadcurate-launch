#!/usr/bin/env python3
from _assessed_value_join import main
# Cobb assessor data has not been staged on this VPS yet. Pass --lookup when available.
raise SystemExit(main('/opt/leadcurate/raw_imports/cobb-ga/assessor-parcels.csv'))
