======================================================================
  L E A D C U R A T E   .
  ----------------------------------------------------------------------
  County Seat delivery package
======================================================================

CUSTOMER COUNTY:    Louisville (Jefferson County), KY
DELIVERY DATE:      2026-06-19
LANE COUNT:         3
TOTAL RECORDS:      300
PACKAGE ID:         louisville-ky-2026-06-19

----------------------------------------------------------------------
  WHAT'S IN THIS PACKAGE
----------------------------------------------------------------------

This folder contains your monthly County Seat delivery for Louisville (Jefferson County),
KY. It is organized into 3 distinct distress lanes, each
sold and serviced separately so the same record never appears in more
than one product across LeadCurate's customer base.

Folder layout:

  README.txt                          this file
  manifest.json                       machine-readable index
  combined-top25.csv                  the strongest 25 records from
                                      every lane, in one consolidated
                                      view for quick triage
  lanes/{lane_slug}/                  one folder per lane:
    <lane>.csv                        full ranked list (this delivery)
    <lane>-preview.csv                25-row preview (names redacted) -
                                      forward this when you want to
                                      bring on a partner without
                                      exposing the live list
    <lane>-meta.json                  source URL, pull date, universe
                                      counts, score range, compliance

----------------------------------------------------------------------
  THE LANES YOU OWN THIS MONTH
----------------------------------------------------------------------

  LANE 1: Louisville KY Pre-Foreclosure
     records delivered : 100
     filtered from    : 259 qualified  (source universe: 3,000)
     score range      : 22.11 - 109.5
     source           : https://data.louisvilleky.gov/datasets/louisville-metro-ky-property-foreclosures

  LANE 2: Louisville KY Open Code Violations
     records delivered : 100
     filtered from    : 13,398 qualified  (source universe: 17,756)
     score range      : 99.9 - 99.93
     source           : https://data.louisvilleky.gov/datasets/louisville-metro-ky-property-maintenance-inspection-violations

  LANE 3: Louisville KY Lien Holder Final Orders
     records delivered : 100
     filtered from    : 411 qualified  (source universe: 516)
     score range      : 16.0 - 55.0
     source           : https://data.louisvilleky.gov/datasets/louisville-metro-ky-lien-holder-final-orders

----------------------------------------------------------------------
  WORKING THE BATCH
----------------------------------------------------------------------

Records are pre-scored - rank 1 is the highest-priority record in
each lane based on the freshness + distress + value signals listed
in that lane's meta.json.

Suggested workflow:
  1. Start with combined-top25.csv for the highest-priority 25 records
     across all your lanes - this is the warm-up list.
  2. Move into each lane's full CSV in rank order.
  3. Cross-reference owner mailing address vs. property address in
     each row - out-of-state mailing addresses are flagged in the data.
  4. Run skip-trace through your existing tool (PropStream / BatchLeads /
     BatchData / Skip Genie). This package ships clean property-record
     data only - we do not include phone numbers in this tier so you
     stay free of TCPA/DNC exposure on our end.
  5. Mark and exclude any records you decide to skip. We track
     exclusions on our side too so the same record does not come back
     in your next batch.

----------------------------------------------------------------------
  FRESHNESS POSTURE
----------------------------------------------------------------------

LeadCurate sources directly from official county portals - not
licensed reseller feeds. Compared to PropStream / BatchLeads, which
license from ATTOM and CoreLogic on a 30 to 90 day refresh cycle,
this package was pulled fresh from the county on 2026-06-19.

A name that hits the Louisville (Jefferson County) public record on the first of the
month is in your batch within days. The same name does not appear in
PropStream's data for another 30 to 90 days.

----------------------------------------------------------------------
  COMPLIANCE
----------------------------------------------------------------------

This delivery is property-record data only - no skip-traced phone
numbers, no email addresses, no DNC scrub. You handle owner contact
lookup, skip trace, DNC compliance, TCPA, and outreach decisions on
your side. LeadCurate provides data and educational tools only and
does not guarantee deals.

For every record we ship the source URL and source pull date in the
lane's meta.json so you can verify provenance independently.

----------------------------------------------------------------------
  REPLACEMENT POLICY (SUMMARY)
----------------------------------------------------------------------

We will replace a record if:
  - the record was a duplicate inside your same monthly batch
  - the record was the wrong county / territory / lane
  - a required field was missing that should have been included
  - there was a clear parsing error in our delivery
  - the record was already assigned to another buyer in an active
    exclusivity window (this should not happen but we will make it
    right if it does)

We will NOT replace a record because the seller was unmotivated,
did not answer, did not close, was not a deal, or because you did
not follow up. The data is the data. Your execution closes the deal.

----------------------------------------------------------------------

  Better data. Cleaner workflow. No hype.

  LeadCurate.

======================================================================
