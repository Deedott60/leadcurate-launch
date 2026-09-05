#!/usr/bin/env python3
from _auction_scraper_common import main
raise SystemExit(main(
    'fulton-ga',
    'https://www.fultonsheriff.org/services/tax-sales',
    '/opt/leadcurate/snapshots/auction_calendars/fulton_auctions.csv'
))
