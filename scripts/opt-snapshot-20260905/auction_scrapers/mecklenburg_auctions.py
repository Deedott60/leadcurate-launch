#!/usr/bin/env python3
from _auction_scraper_common import main
raise SystemExit(main(
    'mecklenburg-nc',
    'https://www.mecksheriff.com/index.php/civil-process/foreclosures',
    '/opt/leadcurate/snapshots/auction_calendars/mecklenburg_auctions.csv'
))
