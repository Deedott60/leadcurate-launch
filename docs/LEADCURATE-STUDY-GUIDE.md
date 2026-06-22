# LeadCurate Business Study Guide
**For Derrick — plain English, no fluff**
*Last updated: 2026-06-22*

---

## SECTION 1 — List Types (what we sell)

### Tax Delinquent List
**What it is:** A list of property owners who owe back taxes to the county. They haven't paid their property taxes for at least one year, sometimes several.

**Why investors want it:** People behind on taxes are often motivated sellers. They're facing potential tax sale or foreclosure and may take a lower offer just to get out from under it.

**Where we get it:** Directly from county tax commissioner records. Public information.

**Industry term?** Yes. Every wholesaler and investor knows "tax delinquent list."

---

### Pre-Foreclosure List
**What it is:** Properties where the bank or court has started the foreclosure process but the sale hasn't happened yet. The owner still has time to sell.

**Why investors want it:** Owner is under pressure, often motivated. There's a window before the bank takes it.

**Where we get it:** County court filings, trustee records.

**Industry term?** Yes. Standard.

---

### Absentee Owner List
**What it is:** Properties where the owner's mailing address is different from the property address. They don't live there — they're a landlord or investor.

**Why investors want it:** Out-of-state landlords with problem properties are often willing to sell. They can't drive by and fix it themselves.

**Out-of-state absentee** = mailing address is in a different STATE than the property. Even more motivated.

**Industry term?** Yes. Very common.

---

### Probate List
**What it is:** Properties tied to a deceased person's estate. Heirs need to settle the estate and often just want to sell fast.

**Why investors want it:** Motivated sellers who need to close quickly and split the money. Often priced below market.

**Where we get it:** County probate court records.

**Industry term?** Yes. Standard.

---

### Permit Burnout Lane *(our term — not standard industry)*
**What it is:** We made this up at LeadCurate. It means properties that have open or recent building permits for damage — fire loss, demolition, storm damage, emergency repairs. The owner filed a permit because something broke or burned.

**Why investors want it:** Property is distressed. Owner may be overwhelmed with repairs and open to selling as-is.

**"Burnout"** = burned out on dealing with the property. Not a standard term — it's our branding for this lane.

---

### Lien List
**What it is:** Properties with a legal claim against them — could be unpaid contractor bills (mechanic's lien), court judgments, or HOA violations.

**Why investors want it:** Owners with liens can't sell clean without paying them off. Some want out badly enough to negotiate.

**Industry term?** Yes. "Lien list" or "lien-encumbered properties."

---

### Vacant Land
**What it is:** Undeveloped lots with no building on them.

**Why investors want it:** Builders, developers, and buy-and-hold investors who want to build or hold for appreciation.

**Industry term?** Yes.

---

### Entity-Owned vs Individual-Owned
**Entity-owned:** Property is owned by an LLC, corporation, trust, REIT, or other legal business structure.

**Individual-owned:** Property is owned by a real human person (their name, not a company name).

**Why it matters:** Individual owners can be called and negotiated with directly. Entity owners require going through a registered agent or lawyer — harder to reach, different conversation.

---

## SECTION 2 — Data Terms (what's inside the list)

### Parcel ID / APN
The county's unique ID number for that specific piece of land. Like a social security number for a property. Used to look it up in public records.

---

### Situs Address
The actual physical address of the property. "Situs" is Latin for "location." This is where the building sits.

---

### Mailing Address
Where the county sends tax bills. This is where the OWNER gets their mail — could be in another state entirely.

---

### Market Value / Assessed Value
**Market value** = what the county thinks the property is worth. Not always accurate but it's the best public number we have.

**Assessed value** = what the county uses to calculate taxes (often a percentage of market value).

---

### Distress Score (0–100)
A number we calculate for each property based on how motivated the owner likely is. Higher score = more distressed = better lead.

Factors that raise the score: large tax balance owed, out-of-state owner, fire/damage permit, long time delinquent, low-value property.

---

### Lane
A "lane" is a specific category of list within a market. Example: Charlotte NC has multiple lanes — tax delinquent lane, absentee owner lane, lien lane. Same county, different filter.

---

### Snapshot
Our word for a processed, ready-to-sell batch of records. We took raw county data (could be 200,000 rows) and filtered it down to the most motivated leads (top 500-2,000 rows), scored them, and cleaned them up. That cleaned file is the "snapshot."

---

### Raw Data
The unprocessed file we download from the county. Could be hundreds of thousands of rows with bad formatting, duplicate entries, missing info. Not sellable as-is. We process it into a snapshot.

---

### Preview / Redacted Preview
A sample of the list — usually 25 rows — where owner names and street numbers are hidden (redacted) so we can show it without giving away the full list. Sent to prospects before they pay.

---

## SECTION 3 — Industry Terms (real estate investor world)

### Wholesaling
Buying a contract to purchase a property at a discount, then selling that contract to another investor before closing — without ever actually owning the property. Wholesalers are one of our biggest customer types.

### MAO (Maximum Allowable Offer)
The most a wholesaler or investor will pay for a property and still make money. Formula: (After Repair Value × 70%) - Repair Cost = MAO.

### ARV (After Repair Value)
What the property would sell for after it's fixed up. Investors use this to work backwards and figure out what to pay today.

### Skip Tracing
The process of finding a property owner's phone number and email when it's not publicly listed. Services like BatchSkipTracing, REIPro, or IDI take a name and address and find contact info. This is how you get phone numbers — our lists are address-only, then customers skip-trace if they want to call.

### DNC (Do Not Call)
The National Do Not Call Registry. If someone's on this list, you can't legally cold call them without risking fines. Skip tracing services flag these. We sell address-only lists, so DNC compliance is the customer's responsibility.

### TCPA
Telephone Consumer Protection Act. Federal law governing cold calling and text messages. Customers who use our lists to call or text are responsible for their own TCPA compliance.

### Cold Calling
Calling someone who hasn't asked to be contacted. Common outreach method for wholesalers working distressed property lists.

### Mailer / Direct Mail
Sending a physical letter or postcard to the property owner's mailing address. Works with our lists because we provide mailing addresses even when there's no phone number.

---

## SECTION 4 — Tech Terms (our stack)

### VPS (Virtual Private Server)
A computer that runs 24/7 in a data center. Ours is at Hostinger, costs a few dollars a month. This is where all our raw data lives and where Danny (Hermes) runs.

### Supabase
Our database. Think of it as a spreadsheet in the cloud that our dashboard reads and writes to automatically. Stores leads from the intake form, prospects you're tracking, messages, and agent activity.

### GitHub / GitHub Pages
GitHub is where our code lives (like a filing cabinet for code). GitHub Pages is a free hosting service that turns our code files into live websites. Right now all our public URLs (intake form, dashboard, sample deliveries) run on GitHub Pages.

### CSV (Comma-Separated Values)
A plain text file where each row is a record and columns are separated by commas. Opens in Excel, Google Sheets, or any CRM. This is the standard format for list deliveries.

### XLSX
Microsoft Excel format. More formatted than CSV — supports multiple tabs, colors, fonts. Our branded delivery files are XLSX.

### RLS (Row Level Security)
A Supabase/database security feature. Controls who can read or write each row of data. We have this set up so random people can't read your customer list even if they find the database URL.

### MCP (Model Context Protocol)
How Claude Code connects to external tools like Supabase. When you see "Supabase MCP connected," it means I can run database commands directly without you pasting anything.

### Cron Job
A scheduled task that runs automatically at a set time. Danny's Wake NC cron runs every day at 6am and downloads the latest delinquent list. Like a calendar reminder that executes code instead of pinging your phone.

### Webhook
A way for one system to automatically notify another when something happens. Example: Twilio calls a webhook URL when someone texts your business number → your dashboard receives the message automatically.

---

## SECTION 5 — Agent Roles (who does what)

### Claude (that's me)
Orchestrator / CEO role. Strategy, writing, business decisions, outreach templates, processing new data, building the dashboard and forms. You talk to me here in Claude Code.

### Danny (Hermes)
VPS-resident worker agent. Runs cron jobs, pulls fresh data, processes snapshots, posts status to the Conference Room. Runs 24/7 on the VPS without you doing anything.

### Codex
IT / security / debugging agent. Reviews code for bugs, runs security audits, fixes broken things in the dashboard. You open a project in Codex desktop and assign him tasks.

### Conference Room
The shared log in your dashboard where all agents post status updates. When Danny finishes a task or Codex finds a bug, it shows up there. You read it like a team Slack channel.

---

## SECTION 6 — LeadCurate-Specific Terms

### Discovery Snapshot
What we call a finished, sellable list batch. Same as "snapshot" — just the branded name we might use with customers.

### Lane
A specific filtered cut of a market's data. Charlotte has multiple lanes (tax delinquent, absentee, lien). We can sell each lane separately.

### Seat
When we talk about "limited seats" for a county — it means we only sell access to that county's list to 1-3 buyers at a time, so the same records aren't being hammered by 100 people. Scarcity = value.

### Phase 1 / Phase 2 / Phase 3
Our internal launch sequence:
- **Phase 1:** Sell one-off lists manually to first customers. Happening now.
- **Phase 2:** Build automation (SMS, voice agents, Twilio, n8n). After Phase 1 cash.
- **Phase 3:** Launch subscription pricing and full landing page. After Phase 2 is running.

---

*Add to this guide whenever a new term comes up. Keep it honest — if it's our made-up term, say so. If it's industry standard, say so.*
