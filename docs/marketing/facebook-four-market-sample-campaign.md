# Facebook Four-Market Sample Campaign

Status: ready for Derrick to post manually. Nothing is auto-posted, and no group is joined automatically.

## Offer

Share one 25-record address-only file with up to five people per market, twenty people total. Each person chooses one market and one category. The source is refreshed as needed and the exact shipping file must pass QA.

| Market | Categories | First checked group |
|---|---|---|
| Detroit / Wayne County | Tax delinquent, vacant, pre-foreclosure, high equity | [Metro Detroit Real Estate Investors, Contractors, Builders, Flippers](https://www.facebook.com/groups/1036455453903927/) |
| Charlotte / Mecklenburg County | Out-of-state owners, high equity, high-value absentee, entity-owned | [Charlotte, NC Real Estate Investors](https://www.facebook.com/groups/1612137285724634/) |
| Atlanta / Fulton County | Vacant, high equity, entity-owned, multifamily | [Real Estate Investors Atlanta GA](https://www.facebook.com/groups/114197495951725/) |
| Memphis / Shelby County | Out-of-state owners, entity-owned, multifamily, industrial | [Real Estate Investors Memphis Tennessee](https://www.facebook.com/groups/1930307087217775/) |

All four groups were public and displayed no promotion or self-promotion ban on their About pages when checked July 29, 2026. Read the visible rules again immediately before posting because group rules can change.

Do not post this offer in [Raleigh Real Estate Investors](https://www.facebook.com/groups/raleighrealestateinvestors/). Its About page explicitly prohibited promotions, spam, and self-promotion without permission when checked.

## Profile Post

Hey everyone. I pulled some property data from four areas and separated it by category. I cleaned up the addresses and parcel information and removed duplicate parcels.

- Detroit / Wayne County: tax delinquent, vacant, pre-foreclosure, or high equity
- Charlotte / Mecklenburg County: out-of-state owners, high equity, high-value absentee, or entity-owned
- Atlanta / Fulton County: vacant, high equity, entity-owned, or multifamily
- Memphis / Shelby County: out-of-state owners, entity-owned, multifamily, or industrial

I'm sharing a 25-record file with up to 20 people who work in one of these areas.

If you want one, comment or message me with the market and one category you want.

## Group Post Pattern

Use the market-specific copy in Command OS under Marketing. Do not put an external link, price, package, or sales pitch in the public post. The person chooses one category, then the conversation moves to Messenger.

First reply:

> Got you. Which [market] category do you want, and what email should I send the 25-record file to?

Do not send an intake form for the free file.

## Delivery Gate

1. Log the reply in Command OS Marketing. It appears in Pipeline at Replied.
2. Confirm one requested market, one category, and the delivery email.
3. Refresh the official source when the current source is no longer fresh enough for delivery.
4. Build the exact 25-row sample, standardize addresses, and remove duplicate parcels.
5. Run `qa_lane_gate.py` against the exact shipping file. Do not send a failed file.
6. Deliver address/property data only. Do not claim phone, email, DNC, guaranteed motivation, or guaranteed deals.
7. Follow up for useful feedback and ask whether the prospect wants a larger current batch.

## QA Basis

The full current QA gate was run before selecting these lanes:

- Wayne MI tax-debt: 3,000 sampled; 0.8% institutional; 0.0% front-50 outliers.
- Mecklenburg NC out-of-state owners: 3,000 sampled; 0.7% owner-occupied; 0.3% institutional.
- Fulton GA vacant: 3,000 sampled; 0.6% institutional; 2.0% front-50 outliers.
- Shelby TN out-of-state owners: 3,000 sampled; 0.0% owner-occupied; 0.5% institutional.

Texas and tired-landlord offers are excluded from this campaign by Derrick's decision.
