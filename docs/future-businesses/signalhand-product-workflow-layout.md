# SignalHand — Product Workflow Layout

## Working name
SignalHand

## One-sentence offer
A human-reviewed public-intent feed that finds people openly asking for local services online and routes vetted opportunities to businesses by niche and city.

## Why this matters
Instead of cold outreach or generic ads, the system looks for people who are already saying things like:
- need a plumber
- any electrician recommendations
- looking for a mover
- emergency locksmith

Then it helps a business respond faster and more intelligently.

## Best first niche
Emergency home services.

### Best first vertical
- plumbers

### Next possible verticals
- electricians
- HVAC repair
- locksmiths
- movers
- cleaners
- restoration/cleanup

## Best first sources
### Core MVP sources
1. Reddit local/city communities
2. Public local forums / request boards / community sites
3. Optional X only if access/search cost is viable

### Secondary / more manual sources
4. Public Facebook pages and public community posts
5. TikTok search/comments for validation, not core infrastructure

### Avoid as core automation
- private Facebook groups
- closed neighborhood networks
- anything that requires brittle, policy-risky access

## Product structure
### Core promise
We surface public, local service-intent posts you would likely miss.

### What the client gets
- reviewed opportunities
- niche/category tagging
- urgency tagging
- location filtering
- links back to original posts
- digest, dashboard, or CRM/webhook delivery

## Workflow
### 1. Source monitoring
Monitor selected approved public sources on a schedule.

### 2. Intent detection
Detect phrases that signal active need.

Examples:
- need a plumber
- who do I call for a leak
- looking for emergency electrician
- any good movers in [city]
- can someone recommend a locksmith

### 3. Classification
Classify:
- niche/service type
- urgency
- city/metro confidence
- recommendation request vs direct hire request

### 4. Scoring
Score by:
- intent strength
- urgency
- recency
- location confidence
- fit with client territory

### 5. Human review queue
A human reviews:
- approve
- reject
- fix category/location
- assign to client

### 6. Delivery / routing
Send approved items by:
- email digest
- dashboard queue
- CRM sync
- webhook/Zapier/n8n route

## Manual vs automated
### Automated
- source pulls
- parsing
- intent keyword matching
- initial scoring
- dedupe
- routing into review queue
- delivery after approval

### Human-in-the-loop
- source selection
- borderline lead review
- assigning to the right client
- deciding reply strategy
- QA for relevance and location

## MVP architecture
### Data layer
- PostgreSQL or Supabase Postgres

### Workflow layer
- n8n for scheduling, routing, notifications, CRM/webhook delivery

### Parsing/classification layer
- Python scripts for:
  - pulling/parsing public sources
  - text normalization
  - dedupe
  - scoring

### Review layer
- simple internal dashboard or admin table first
- approve/reject/assign actions

### Delivery layer
- email
- webhook
- CRM
- CSV export if needed

## Minimum schema
- sources
- posts
- lead_candidates
- extracted_signals
- clients
- territories
- review_decisions
- delivery_events

## First proof step
Build one proof monitor for:
- one city
- one niche
- one source type

Best first proof:
- plumbers
- one city
- Reddit + one public local request board

## First paid offer
### Option A — reviewed opportunity feed
Monthly fee for:
- reviewed intent posts
- one niche
- one service territory

### Option B — alert + dashboard package
Monthly fee for:
- dashboard access
- immediate alerts
- approved opportunities
- one outbound reply draft per opportunity

## Good first traction signal
- client says the leads are relevant
- client requests expansion to more cities or keywords
- client wants same system for second service category

## Stop condition
Stop or reframe if:
- too much noise for too little signal
- location confidence is too weak
- sources are too brittle
- clients do not value the reviewed opportunities enough to pay

## Biggest risks
- platform access/policy changes
- weak location data
- noisy recommendation posts
- clients expecting booked jobs instead of opportunity signals
- operational burden if too many sources are added too early

## Recommended first execution order
1. finalize working name
2. pick first niche (plumbers)
3. pick first city
4. define keyword list
5. define source list
6. build parser + scoring prototype
7. build review queue
8. route approved leads by email/dashboard
9. test with one pilot business
10. simplify before expanding

## Positioning note
This should be sold as:
- public service-intent monitoring
- reviewed opportunity routing
- local lead intelligence

Not as:
- guaranteed booked jobs
- magical auto-reply bot everywhere
- surveillance of private groups
