#!/usr/bin/env python3
from _auction_scraper_common import main
raise SystemExit(main(
    'wake-nc',
    'https://www.wake.gov/departments-government/tax-administration/real-estate/property-tax-foreclosure-sales',
    '/opt/leadcurate/snapshots/auction_calendars/wake_auctions.csv'
))
