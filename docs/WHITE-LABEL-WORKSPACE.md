# White-label workspace: operating model

## Direct answer

The Property Decision Tool is one workspace. Search results, the selected property, deal analysis, comparable records, complete source fields, and the map are different views inside the same application. A customer should not be sent through separate disconnected websites for ordinary property work.

## Current state

The application lives at `C:\Users\lenovo\Documents\Leadcurate\property-decision-tool` and the current hosted build is `https://property-decision-tool.mimiderrick.chatgpt.site`.

Working now:

- Browse demonstration records or records imported from CSV.
- Search loaded records and select a result without leaving the workspace.
- Review organized property facts plus extra source columns.
- Run flip, rental, BRRRR, wholesale, MAO, ROI, and cash-flow calculations.
- Review loaded comparable-sale records.
- Display records with valid coordinates on a MapLibre map.
- Prepare a field brief, print a decision report, and preview white-label settings.
- Call the existing `/api/connectors/search` adapter when an upstream API is configured.

Not production-ready yet:

- No LeadCurate VPS property-search API is configured.
- No production customer authentication or tenant/market authorization.
- No server-backed saved searches, notes, statuses, assignments, or persistent branding.
- No bulk export job service.
- No Next/Previous cursor controls. The UI requests up to 100 connected records and renders the best 12 search matches.
- No map clustering or bounding-box API for large result sets.

The tool is usable now as an interface, calculator, CSV-import workspace, and connection proof. It is not yet a finished multi-customer database product.

## User flow after connection

1. The customer signs in and the server resolves their tenant and allowed markets.
2. They browse or search by address, parcel, owner, category, location, value, or supported plain language.
3. The VPS searches the full authorized database and returns one bounded page, a total count, and `nextCursor`.
4. The result navigator appears inside the workspace. Selecting a result changes the active property.
5. The customer moves between Opportunities, Analyze, Market & Record, and Map & Field without leaving the application.
6. Next/Previous requests more pages. The browser never loads a complete county into memory.
7. A large export runs on the VPS and returns a private expiring download link.

## What 250 means

The connector bounds one response to 250 records. This is a page-size safety limit, not a database-size or customer-access limit. If a search has 8,420 matches, a response may contain records 1-100 plus `total: 8420` and a cursor. A server-side export can still contain all authorized matches.

## VPS API design

The browser must not connect directly to raw VPS files or hold a private API key.

```text
Customer browser
  -> Property Decision Tool
  -> tool server /api/connectors/search
  -> HTTPS VPS property API
  -> authentication and tenant/market authorization
  -> normalized parcel and signal store
  <- records, total, nextCursor
```

Recommended contract:

```http
GET /v1/properties/search?q=detroit+absentee+under+150000&market=wayne-mi&limit=100&cursor=...
Authorization: Bearer <server credential or verified customer session>
```

```json
{"records": [], "total": 8420, "nextCursor": "opaque-cursor"}
```

Each record can include parcel ID, property and mailing addresses, owner, market, property type, values, source date, coordinates, lane signals, and additional source fields. Missing fields remain missing.

## Data structure

- Keep official raw files as evidence and refresh inputs.
- Normalize one base record per parcel.
- Attach lane signals separately rather than duplicating the full property for each category.
- Store source date, retrieval date, source URL, and data version.
- Grant markets through customer/tenant permissions instead of duplicating counties per customer.
- Use Supabase for users, tenants, permissions, saved work, export jobs, and audit logs when appropriate.
- Keep large source files and generated exports on the VPS or private object storage.

## Map behavior

The current map works when records contain latitude and longitude. Production should return coordinates for the current page or map viewport. Large searches use clustering or bounding-box requests so a phone is not asked to draw hundreds of thousands of markers.

## Production build order

1. Choose the first customer and authorized markets.
2. Define the normalized parcel and lane-signal schema.
3. Build a read-only HTTPS VPS search API against one verified market.
4. Add Supabase login and server-side tenant/market enforcement.
5. Add cursor pagination to the adapter and workspace UI.
6. Add map clustering or viewport queries.
7. Add persistent notes, saved searches, assignments, and branding.
8. Add asynchronous CSV/XLSX exports with private expiring links.
9. Test mobile, desktop, permissions, pagination, maps, and exports before launch.
