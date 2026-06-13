# LeadCurate v1 — implementation-ready n8n spec

This is the final node-by-node spec for the first county workflow.
It is designed for a single county lane first, then repeatable by county config.

## Implementation readiness audit

### Ready now
- County config-driven ingestion
- Raw file hash + immutable storage
- Normalization, dedupe, suppression, skip trace, scoring
- Delivery + audit logging
- Fail-closed handling for dedupe, suppression, export

### Gaps to resolve before production
- Final source credentials / access method per county
- Exact suppression/DNC provider account and rate limits
- Final skip-trace provider account and request/response contract
- Final storage target for raw files and exports
- Exact alert destination IDs and sender settings

### Credentials / contract handoff note
When this workflow is handed to another agent or resumed later, these are the remaining fill-in items:
- county-specific source login/API credentials, if any
- suppression/DNC provider name, API key, and rate-limit limits
- skip-trace provider name, API key, and response-field mapping
- object storage bucket / signed-link settings
- Telegram/email/slack destination IDs
- any county-specific parser profile names

If a field can be defaulted now, the workflow should default it and keep running; if it cannot be defaulted, leave the exact placeholder text in the config table and stop at the missing credential with a clear ops alert.

### Locked v1 defaults
These are the operating defaults until a county-specific source forces a change:
- Source access: HTTP first
- Browser fallback: Playwright only for JS-heavy or form-heavy pages
- Proxy fallback: per-source only after repeated `403` / `429` / challenge-page failures
- Normalization: Python + `libphonenumber` + `libpostal`
- DNC/suppression: Postgres suppression tables + exact-match scrub before and after skip trace
- Skip trace: BatchData-like property contact enrichment API
- Quality scoring: 0–100 score with fail-closed delivery gates
- Delivery: CSV/XLSX via email or signed storage link fallback
- Alerts: Telegram and/or email for ops failures
- Raw storage: immutable object storage keyed by `run_id` + file hash


### Required database objects
Use the existing Supabase schema plus these minimum additions if they do not already exist:
- `workflow_runs`
- `workflow_events`
- `raw_files`
- `lead_exclusions`
- `lead_quality_checks`

---

## Workflow contract

### Trigger scope
- One county per run
- One source per run, or one source group if the county needs it
- Output is a single delivered batch plus full audit trail

### Required run metadata
- `run_id` (uuid)
- `county_key`
- `territory_id`
- `source_id`
- `trigger_type` (`cron`, `manual`, `retry`)
- `started_at`
- `run_date`
- `workflow_version` = `LeadCurate-v1`

### Standard lead item contract
Every normalized item must carry these fields through the workflow:
- `run_id`
- `raw_import_id`
- `territory_id`
- `county`
- `state`
- `source_id`
- `source_type`
- `source_date`
- `source_row_id`
- `event_key`
- `owner_name`
- `property_address`
- `mailing_address`
- `parcel_id`
- `zip_code`
- `property_type`
- `owner_type`
- `owner_entity_type`
- `distress_type`
- `lead_lane`
- `lead_score`
- `urgency_level`
- `score_reason`
- `dedupe_status`
- `dedupe_reason`
- `suppression_status`
- `suppression_reason`
- `dnc_status`
- `skip_trace_status`
- `skip_trace_confidence`
- `phone`
- `phone_type`
- `email`
- `google_maps_url`
- `assessor_url`
- `contact_export_eligible`
- `final_eligible`
- `exclude_reason`

---

## Node-by-node n8n specification

### 1) Cron Trigger — `Cron: County Pull`
**Type:** Cron

**Purpose:** Start scheduled county processing.

**Outputs:**
- `run_id`
- `county_key`
- `run_date`
- `trigger_type = cron`

**Branching:**
- If manual override flag is present in config, route to `Manual Review Start`
- Else continue to `Load County Config`

**Failure handling:**
- If workflow is disabled or cron misfires, write `workflow_runs.status = failed` and send ops alert.

---

### 2) Set — `Load County Config`
**Type:** Set or Postgres Select

**Purpose:** Load territory, source, and policy config.

**Input fields:**
- `county_key`

**Output fields:**
- `territory_id`
- `state`
- `county`
- `source_id`
- `source_url`
- `refresh_cadence`
- `skip_trace_enabled`
- `dnc_scrub_enabled`
- `delivery_format`
- `min_score`
- `suppression_list_id`
- `customer_id`
- `alert_channel`

**Branching:**
- Missing config -> `Notify Failure`
- Config present -> `Create Run Record`

**Failure handling:**
- Hard stop if county config is missing or disabled.

---

### 3) Postgres — `Create Run Record`
**Type:** Postgres / Supabase Insert

**Purpose:** Create workflow run audit header.

**Inputs:**
- all config fields
- `run_id`
- `trigger_type`
- `started_at`

**Writes:** `workflow_runs`

**Required row fields:**
- `run_id`
- `county_key`
- `territory_id`
- `source_id`
- `trigger_type`
- `status = running`
- `started_at`
- `workflow_version`

**Failure handling:**
- If insert fails, stop immediately and alert ops.

---

### 4) HTTP Request — `Fetch Source`
**Type:** HTTP Request

**Purpose:** Pull the raw source data.

**Inputs:**
- `source_url`
- auth headers if required
- query params for `run_date` or source-specific filters

**Outputs:**
- `raw_payload`
- `http_status`
- `content_type`
- `fetched_at`

**Branching:**
- `2xx` + non-empty body -> `Hash and Store Raw`
- `429`, `403`, `5xx`, timeout -> `Retry Fetch`
- empty body -> `Notify Failure`

**Failure handling:**
- Retry up to 3 times with exponential backoff.
- After final failure, mark run failed and notify ops.

---

### 5) IF — `Fetch Success?`
**Type:** IF

**Condition:**
- `http_status >= 200 and http_status < 300`
- `raw_payload` is not empty

**True branch:** continue
**False branch:** `Retry Fetch` or `Notify Failure`

---

### 6) Code — `Hash and Store Raw`
**Type:** Code

**Purpose:** Create immutable raw file artifact and hash.

**Inputs:**
- `raw_payload`
- `source_id`
- `county_key`
- `run_id`
- `fetched_at`

**Outputs:**
- `file_hash`
- `storage_key`
- `file_url`
- `raw_record_count_estimate`

**Logic:**
- compute SHA-256 hash of raw bytes
- write raw file to storage
- generate immutable object path with `run_id` + `file_hash`

**Branching:**
- Duplicate hash already exists for same source/date -> `Duplicate Pull Log`
- Storage success -> `Insert Raw Import`

**Failure handling:**
- Storage write failure is fatal for the run.

---

### 7) Postgres — `Duplicate Pull Log`
**Type:** Postgres Insert

**Purpose:** Record that the source pull was already seen.

**Writes:** `raw_imports` or `workflow_events`

**Fields:**
- `run_id`
- `source_id`
- `file_hash`
- `status = duplicate`
- `notes = duplicate raw fetch`

**Branching:**
- Stop downstream processing for this run.

---

### 8) Postgres — `Insert Raw Import`
**Type:** Postgres Insert

**Purpose:** Persist the raw import row.

**Inputs:**
- `territory_id`
- `source_id`
- `source_date`
- `fetched_at`
- `file_url`
- `file_hash`
- `record_count`
- `status = imported`

**Writes:** `raw_imports`

**Outputs:**
- `raw_import_id`

**Failure handling:**
- Abort run if insert fails.

---

### 9) Execute Command or Code — `Normalize Source`
**Type:** Execute Command or Code

**Purpose:** Parse raw file into normalized lead candidates.

**Inputs:**
- `file_url`
- `raw_import_id`
- `county_key`
- parser profile by `source_id`

**Outputs:** one item per candidate lead with:
- `raw_import_id`
- `territory_id`
- `county`
- `state`
- `source_id`
- `source_type`
- `source_date`
- `source_row_id`
- `event_key`
- `owner_name`
- `property_address`
- `mailing_address`
- `parcel_id`
- `zip_code`
- `property_type`
- `owner_type`
- `owner_entity_type`
- `distress_type`
- `parse_warnings[]`

**Branching:**
- Zero rows -> `Notify Failure`
- Parse error rate above threshold -> `Notify Failure`
- Normal rows -> `Split In Batches`

**Failure handling:**
- If more than 20% of rows fail parsing, mark raw import failed.

---

### 10) IF — `Parser Output Valid?`
**Type:** IF

**Condition:**
- parsed rows count > 0
- parse error rate <= threshold

**True branch:** continue
**False branch:** `Mark Raw Import Failed`

---

### 11) Split In Batches — `Process Leads`
**Type:** Split In Batches

**Purpose:** Process each lead one at a time for deterministic branching.

**Batch size:** 1 to 25, depending on provider rate limits.

**Output:**
- one normalized lead item per iteration

---

### 12) Code — `Standardize Fields`
**Type:** Code

**Purpose:** Clean and standardize names, addresses, and parcel values.

**Transforms:**
- trim whitespace
- uppercase `state`, `county`
- title-case `owner_name`
- normalize suffixes (`St`, `Ave`, `Rd`, etc.)
- normalize parcel/zip formatting
- split and reassemble property/mailing addresses

**Outputs:**
- `owner_name_clean`
- `property_address_clean`
- `mailing_address_clean`
- `parcel_id_clean`
- `zip_code_clean`
- `address_quality_flag`
- `name_quality_flag`

**Failure handling:**
- Missing required identity fields -> set `exclude_reason = missing_required_fields` and route to exclusion log.

---

### 13) Postgres — `Dedupe Check`
**Type:** Postgres Select

**Purpose:** Prevent duplicate resale.

**Match keys:**
- `territory_id`
- `parcel_id_clean`
- `property_address_clean`
- `owner_name_clean`
- `source_type`
- `event_key`

**Outputs:**
- `dedupe_status` = `new` / `duplicate` / `conflict`
- `dedupe_reason`
- `existing_lead_id`

**Branching:**
- `duplicate` or `conflict` -> `Exclusion Log`
- `new` -> `Suppression/DNC Scrub`

**Failure handling:**
- Dedupe query failure is fatal; fail closed.

---

### 14) Postgres or API — `Suppression/DNC Scrub`
**Type:** Postgres Select, HTTP Request, or Supabase RPC

**Purpose:** Screen against suppression and DNC rules before enrichment.

**Inputs:**
- `owner_name_clean`
- `property_address_clean`
- `mailing_address_clean`
- `parcel_id_clean`
- `phone` if present
- `email` if present
- `suppression_list_id`

**Outputs:**
- `suppression_status` = `cleared` / `suppressed`
- `suppression_reason`
- `dnc_status` = `clear` / `match` / `unknown`

**Branching:**
- `suppressed` -> `Exclusion Log`
- `cleared` -> `Classify Lane`

**Failure handling:**
- If suppression service is unavailable, fail closed for delivery.

---

### 15) Code — `Classify Lane`
**Type:** Code

**Purpose:** Assign the lead lane.

**Inputs:**
- `source_type`
- `distress_type`
- `property_type`
- `owner_type`
- source-specific tags

**Outputs:**
- `lead_lane`
- `lane_reason`
- `lane_priority`

**Allowed lanes:**
- `tax_delinquent`
- `probate_estate`
- `foreclosure`
- `vacant_property`
- `absentee_owner`
- `commercial`
- `research_only`
- `suppressed`
- `nurture`

**Branching:**
- `suppressed` -> `Exclusion Log`
- `research_only` -> `Research Only Log`
- else -> `Quality Score`

---

### 16) Code — `Quality Score`
**Type:** Code

**Purpose:** Score lead quality and urgency.

**Inputs:**
- `lead_lane`
- `property_type`
- `source_date`
- `address_quality_flag`
- `name_quality_flag`
- `dnc_status`
- `dedupe_status`
- `source_reliability_score`
- `parse_warnings[]`

**Outputs:**
- `lead_score` integer 0-100
- `urgency_level` integer 1-5
- `quality_tier` = `premium` / `standard` / `nurture` / `exclude`
- `score_reason`

**Thresholds:**
- `>= 80` => premium
- `60-79` => standard
- `40-59` => nurture
- `< 40` => exclude

**Failure handling:**
- Missing inputs -> score conservatively and tag `score_reason = incomplete_data`.

---

### 17) IF — `Skip Trace Eligible?`
**Type:** IF

**Condition:**
- `dedupe_status = new`
- `suppression_status = cleared`
- `lead_score >= min_score`
- `lead_lane != research_only`
- `lead_lane != suppressed`

**True branch:** `Skip Trace`
**False branch:** `Exclusion Log`

**Failure handling:**
- If score is below threshold, do not skip trace.

---

### 18) HTTP Request — `Skip Trace`
**Type:** HTTP Request

**Purpose:** Enrich approved records only.

**Inputs:**
- `owner_name_clean`
- `property_address_clean`
- `mailing_address_clean`
- `parcel_id_clean`
- `county`
- `state`

**Outputs:**
- `phone`
- `phone_type`
- `email`
- `skip_trace_confidence`
- `skip_trace_provider_id`
- `skip_trace_status`

**Branching:**
- Success -> `Post-Skip DNC Scrub`
- Provider failure -> set `skip_trace_status = failed` and continue to `Post-Skip DNC Scrub` without contacts

**Failure handling:**
- Skip trace is fail-open. Do not block the batch.

---

### 19) IF — `Skip Trace Returned Contacts?`
**Type:** IF

**Condition:**
- `skip_trace_status = success`
- at least one of `phone` or `email` exists

**True branch:** `Post-Skip DNC Scrub` with contact values
**False branch:** `Post-Skip DNC Scrub` with blank contact values

---

### 20) DNC Scrub — `Post-Skip DNC Scrub`
**Type:** HTTP Request or Postgres Select

**Purpose:** Re-check contact-level suppression before delivery.

**Inputs:**
- `phone`
- `email`
- `owner_name_clean`
- `property_address_clean`

**Outputs:**
- `dnc_status`
- `scrubbed_at`
- `contact_export_eligible` boolean

**Branching:**
- `contact_export_eligible = true` -> `Final Eligibility Check`
- `false` -> `Final Eligibility Check` with contact fields removed from export

**Failure handling:**
- Fail closed on contact export if scrub service fails.

---

### 21) IF — `Final Eligibility Check`
**Type:** IF

**Condition:**
- `lead_score >= min_score`
- `suppression_status = cleared`
- `dedupe_status = new`
- `county = configured county`
- `lead_lane` allowed for customer rights

**True branch:** `Upsert Lead`
**False branch:** `Exclusion Log`

---

### 22) Postgres — `Upsert Lead`
**Type:** Postgres Upsert

**Purpose:** Store the final lead row.

**Target table:** `leads`

**Required write fields:**
- `raw_import_id`
- `territory_id`
- `state`
- `county`
- `zip_code`
- `zone_name` if available
- `owner_name`
- `property_address`
- `mailing_address`
- `parcel_id`
- `property_type`
- `owner_type`
- `owner_entity_type`
- `source_type`
- `source_date`
- `distress_type`
- `lead_lane`
- `record_tags`
- `phone`
- `phone_type`
- `email`
- `dnc_status`
- `scrubbed_at`
- `skip_trace_confidence`
- `urgency_level`
- `lead_score`
- `score_reason`
- `suppression_status`
- `google_maps_url`
- `assessor_url`
- `resale_eligibility = eligible`

**Outputs:**
- `lead_id`

**Failure handling:**
- If insert fails, stop item processing and alert ops.

---

### 23) Postgres — `Assignment Lock`
**Type:** Transactional Postgres Insert/Update

**Purpose:** Prevent duplicate sale during active customer window.

**Inputs:**
- `lead_id`
- `customer_id`
- `territory_right_id`
- `exclusivity_window_start`
- `exclusivity_window_end`

**Outputs:**
- `assignment_id`
- `assignment_status`

**Branching:**
- Lock success -> `Build Export Row`
- Lock conflict / already assigned -> `Exclusion Log`

**Failure handling:**
- Retry once on transaction conflict; then fail the item.

---

### 24) Code — `Build Export Row`
**Type:** Code

**Purpose:** Prepare customer-facing export fields.

**Outputs fields:**
- `assignment_id`
- `lead_id`
- `owner_name`
- `property_address`
- `mailing_address`
- `county`
- `state`
- `lead_lane`
- `source_type`
- `source_date`
- `lead_score`
- `score_reason`
- `urgency_level`
- `phone`
- `email`
- `dnc_status`
- `skip_trace_confidence`
- `google_maps_url`
- `assessor_url`
- `notes`

**Branching:**
- If `delivery_format = csv` -> `Generate CSV`
- If `delivery_format = xlsx` -> `Generate XLSX`

---

### 25) Spreadsheet File — `Generate CSV/XLSX`
**Type:** Spreadsheet File

**Purpose:** Produce deliverable file.

**Inputs:**
- export rows

**Outputs:**
- `delivery_file_url`
- `delivery_row_count`
- `delivery_format`

**Failure handling:**
- File generation failure is fatal for this run.

---

### 26) Postgres — `Create Delivery Record`
**Type:** Postgres Insert

**Purpose:** Register the batch delivery.

**Writes:** `deliveries`

**Fields:**
- `customer_id`
- `territory_id`
- `lead_lane`
- `delivery_date`
- `lead_count`
- `file_url`
- `status = draft` or `sent`

**Outputs:**
- `delivery_id`

---

### 27) Email / Storage Link — `Deliver Batch`
**Type:** Email, Resend, SendGrid, Mailgun, or storage link sender

**Purpose:** Send the batch to the customer.

**Inputs:**
- `customer_email`
- `delivery_file_url`
- `delivery_id`

**Outputs:**
- `sent_message_id`
- `sent_at`
- `delivery_status = sent`

**Branching:**
- Email success -> `Write Delivery Audit`
- Email failure -> signed storage link fallback + notify ops

**Failure handling:**
- Delivery should not fail if email send fails and signed link is available.

---

### 28) Postgres — `Write Item Audit`
**Type:** Postgres Insert

**Purpose:** Log item-level decisions.

**Writes:** `workflow_events`, `lead_exclusions`, `lead_quality_checks`

**Fields:**
- `run_id`
- `raw_import_id`
- `lead_id`
- `event_type`
- `status`
- `exclude_reason`
- `metadata`

**Failure handling:**
- Audit write failure should not block delivery, but it must be alerted.

---

### 29) Postgres — `Finalize Run`
**Type:** Postgres Update

**Purpose:** Close out the run.

**Updates:** `workflow_runs`

**Fields:**
- `status = success` or `partial_success` or `failed`
- `ended_at`
- `lead_count_raw`
- `lead_count_delivered`
- `lead_count_suppressed`
- `lead_count_duplicated`
- `lead_count_enriched`
- `error_count`

**Failure handling:**
- If this step fails, send ops alert and keep the run marked unresolved until corrected.

---

### 30) Slack / Email — `Notify Failure`
**Type:** Slack or Email

**Purpose:** Alert on hard failures.

**Triggers:**
- config missing
- fetch failure after retries
- raw store failure
- parse failure above threshold
- dedupe failure
- suppression failure in fail-closed mode
- assignment lock conflict after retry
- file generation failure

**Payload fields:**
- `run_id`
- `county_key`
- `node_name`
- `error_message`
- `failed_item_count`
- `next_action`

---

## Exact branch map

### Main success path
`Cron` -> `Load County Config` -> `Create Run Record` -> `Fetch Source` -> `Fetch Success?` -> `Hash and Store Raw` -> `Insert Raw Import` -> `Normalize Source` -> `Parser Output Valid?` -> `Split In Batches` -> `Standardize Fields` -> `Dedupe Check` -> `Suppression/DNC Scrub` -> `Classify Lane` -> `Quality Score` -> `Skip Trace Eligible?` -> `Skip Trace` -> `Post-Skip DNC Scrub` -> `Final Eligibility Check` -> `Upsert Lead` -> `Assignment Lock` -> `Build Export Row` -> `Generate CSV/XLSX` -> `Create Delivery Record` -> `Deliver Batch` -> `Write Item Audit` -> `Finalize Run`

### Failure branches
- Config missing -> `Notify Failure`
- Fetch 429/403/5xx after retries -> `Notify Failure`
- Raw storage failure -> `Notify Failure`
- Parse zero rows or high error rate -> `Notify Failure`
- Dedupe query failure -> `Notify Failure`
- Suppression failure -> `Notify Failure`
- Assignment conflict after retry -> `Exclusion Log` + `Write Item Audit`
- Export generation failure -> `Notify Failure`
- Email send failure -> signed-link fallback + `Notify Failure` if fallback also fails

### Exclusion branches
- `duplicate` -> `lead_exclusions`
- `suppressed` -> `lead_exclusions`
- `research_only` -> `workflow_events` only
- `low_score` -> `lead_exclusions`
- `already_assigned` -> `lead_exclusions`
- `missing_required_fields` -> `lead_exclusions`

---

## Failure policy summary

- **Fail closed:** config, raw storage, dedupe, suppression, final export generation, assignment lock
- **Fail open:** skip trace, but only after passing quality and suppression gates
- **Fail with fallback:** delivery email, using signed storage link if email fails
- **Always audit:** every run and every excluded item must be written to audit/exclusion tables

---

## Minimum field map for delivery export

Include these columns in the delivered file:
- `assignment_id`
- `lead_id`
- `owner_name`
- `property_address`
- `mailing_address`
- `county`
- `state`
- `lead_lane`
- `source_type`
- `source_date`
- `lead_score`
- `score_reason`
- `urgency_level`
- `phone`
- `email`
- `dnc_status`
- `skip_trace_confidence`
- `google_maps_url`
- `assessor_url`
- `notes`

---

## Readiness verdict

**Ready for implementation once provider contracts and storage targets are locked.**
The workflow architecture, data fields, and branch rules are concrete enough to build in n8n now.
