# Shelby / Memphis Universal Key

Status: verified sample, manual-trigger only.

## The Unlock

Memphis/Shelby can be worked from one repeatable key:

- Register GIS `PARID`, normalized as parcel id.
- Register GIS also returns `TRUSTEE_ID` when available.
- Tax sale, code enforcement, and permits can be joined back to that key.

The practical automation door is not the public ArcGIS server directly. From the VPS, `scgis.shelbycountytn.gov` and the Trustee parcel endpoint fail with OpenSSL legacy TLS renegotiation errors. The usable path is the Register GIS web backend:

- `https://gis.register.shelby.tn.us/details`
- `https://gis.register.shelby.tn.us/completedetails`

The JavaScript file that exposes this is:

- `https://gis.register.shelby.tn.us/javascripts/gis.js`

## Intake Lane Coverage

Base owner/value/mailing fields:

- Source: Register GIS `/details` and `/completedetails`
- Fields: owner, owner mailing address, property class, land use, current land/building/total/assessed values, acres, sales instrument codes, tax-sale status when present.

Derived from base:

- `absentee`: owner mailing state is not TN, or owner mailing ZIP differs from property ZIP.
- `individual-homeowner`: residential class and owner name does not match entity pattern.
- `entity-owned`: owner name matches LLC/inc/bank/trust/church/city/county/agency/etc.
- `vacant-land`: land-use text contains vacant.
- `high-equity`: current total value is above threshold. This is a value/equity proxy until mortgage/debt is reviewed.

Overlay sources:

- `tax-delinquent`: Trustee S3 tax-sale extract joined by parcel id: `https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv`
- `code-violations`: Data Midsouth `historical-code-enforcement-requests` API joined by `parcel_id`.
- `active-permits`: Data Midsouth `shelby-county-building-and-demolition-permits` API joined by `parid`.

Specialty signals that need QA:

- `probate`: Register sales instrument codes `PC` or `DN`, or owner text containing estate/heir. Needs court/source review before selling as premium probate.
- `liens`: Register sales instrument codes such as `FJ` or `L`. Needs document/source review.
- `pre-foreclosure`: Register sales instrument codes such as `CH`, `D`, or `TD`, and/or the Assessor Foreclosures GIS layer. Needs quality review; `CH` alone can mean chancery court, not always foreclosure.

Unavailable from these public sources:

- phone/email
- skip-trace numbers
- DNC status
- mortgage balance / true free-and-clear proof
- Trustee delinquent balance from the VPS path, because the Trustee endpoint fails TLS handshake under current OpenSSL.

## Verified Sample

Script:

```bash
python3 /opt/leadcurate/scripts/shelby_universal_key.py --prefix 001 --max-prefix-rows 150 --max-details 30 --overlay-limit 1000 --sleep 0.03
```

Output:

- CSV: `/opt/leadcurate/processed/shelby-tn/2026-07-04/shelby-tn-universal-key-sample-2026-07-04.csv`
- Meta: `/opt/leadcurate/processed/shelby-tn/2026-07-04/shelby-tn-universal-key-sample-2026-07-04-meta.json`

Result:

- prefix `001` returned 150 sampled parcel candidates from Register GIS.
- 30 completed parcel detail records were written.
- overlay keys loaded:
  - tax sale: 4,976 keys
  - code violations: 1,032 keys from sample overlay pull
  - active permits: 1,054 keys from sample overlay pull

Sample lane counts:

- absentee: 3
- entity-owned: 19
- high-equity: 17
- individual-homeowner: 8
- pre-foreclosure signal: 4
- vacant-land: 2

## Operating Rule

Do not sell the raw universal-key pull as-is. Use it as the master source, then apply lane-specific filters and the Quality Contract before delivery:

- dedupe by normalized parcel id
- remove government/exempt/institution records unless the buyer asked for entity/institution targets
- residential by default for homeowner/absentee/high-equity
- court/sales-instrument signals require review before being labeled probate, lien, or pre-foreclosure
- contact fields require skip tracing and DNC process outside the county source

## Customer Explanation

Shelby does not hand over one perfect investor-ready list. The county publishes different slices in different places. LeadCurate uses the Register GIS parcel id as the master key, enriches ownership and property value from parcel records, then joins tax-sale, code-enforcement, permit, absentee, entity, vacant-land, and other signals back onto that same parcel. That is the repeatable Memphis process.
