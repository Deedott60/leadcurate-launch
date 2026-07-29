# Facebook Four-Market Sample Campaign

Status: ready for Derrick to post manually. Nothing is auto-posted, and no group is joined automatically.

## Offer

Open three test spots in each market. Each qualified person receives a 25-property address-only starter sample after the source is refreshed as needed and the exact shipping file passes QA.

| Market | Offer | Keyword | First checked group |
|---|---|---|---|
| Detroit / Wayne County | Live tax-debt owners | DETROIT | [Metro Detroit Real Estate Investors, Contractors, Builders, Flippers](https://www.facebook.com/groups/1036455453903927/) |
| Charlotte / Mecklenburg County | Out-of-state owners | CHARLOTTE | [Charlotte, NC Real Estate Investors](https://www.facebook.com/groups/1612137285724634/) |
| Atlanta / Fulton County | Verified vacant land | ATLANTA | [Real Estate Investors Atlanta GA](https://www.facebook.com/groups/114197495951725/) |
| Memphis / Shelby County | Out-of-state owners | MEMPHIS | [Real Estate Investors Memphis Tennessee](https://www.facebook.com/groups/1930307087217775/) |

All four groups were public and displayed no promotion or self-promotion ban on their About pages when checked July 29, 2026. Read the visible rules again immediately before posting because group rules can change.

Do not post this offer in [Raleigh Real Estate Investors](https://www.facebook.com/groups/raleighrealestateinvestors/). Its About page explicitly prohibited promotions, spam, and self-promotion without permission when checked.

## Profile Post

I've been cleaning and organizing public-record property data in four markets:

- Detroit / Wayne County: live tax-debt owners
- Charlotte / Mecklenburg County: out-of-state owners
- Atlanta / Fulton County: verified vacant land
- Memphis / Shelby County: out-of-state owners

The records are organized by parcel, addresses are standardized, and duplicate parcels are removed.

I'm opening 3 test spots in each market for active investors who will actually review a free 25-property starter sample and give honest feedback.

This is address/property data only: no skip-traced phone numbers or emails, and no promise that a property will turn into a deal.

Comment SAMPLE or DM me the market plus what you buy: wholesale, buy-and-hold, vacant land, flips, or commercial.

## Group Post Pattern

Use the market-specific copy in Command OS under Marketing. Do not put an external link in the public post. The post asks for a market keyword and investment strategy, then moves the conversation to Messenger.

First reply:

> Thanks for reaching out. Before I assign a sample, what do you buy in [market]: wholesale, buy-and-hold, vacant land, flips, or commercial? And have you worked a public-record list before?

After they answer, send the intake privately:

`https://leadcurate.com/intake/`

## Delivery Gate

1. Log the reply in Command OS Marketing. It appears in Pipeline at Replied.
2. Confirm the requested market and buying strategy.
3. Refresh the official source when the current source is no longer fresh enough for delivery.
4. Build the exact 25-row sample, standardize addresses, and remove duplicate parcels.
5. Run `qa_lane_gate.py` against the exact shipping file. Do not send a failed file.
6. Deliver address/property data only. Do not claim phone, email, DNC, guaranteed motivation, or guaranteed deals.
7. Follow up for useful feedback and ask whether the prospect wants a larger current batch.

## Verified Starting Lanes

The full current QA gate was run before selecting these lanes:

- Wayne MI tax-debt: 3,000 sampled; 0.8% institutional; 0.0% front-50 outliers.
- Mecklenburg NC out-of-state owners: 3,000 sampled; 0.7% owner-occupied; 0.3% institutional.
- Fulton GA verified vacant land: 3,000 sampled; 0.6% institutional; 2.0% front-50 outliers.
- Shelby TN out-of-state owners: 3,000 sampled; 0.0% owner-occupied; 0.5% institutional.

Texas and tired-landlord offers are excluded from this campaign by Derrick's decision.
