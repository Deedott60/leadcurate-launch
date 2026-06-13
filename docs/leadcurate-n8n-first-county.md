# LeadCurate v1 n8n workflow - first county

This is the concrete node-by-node workflow for the *first pilot county* in LeadCurate v1.

## County configuration object

Use one config row in Postgres / Supabase for the pilot county:

- `county_key`: `pilot_county_001`
- `state`: `<STATE>`
- `county`: `<COUNTY>`
- `territory_type`: `county`
- `lead_lane`: `default` or the lane being sold first
- `source_id`: public-record source ID
- `source_url`: source landing page or API endpoint
- `refresh_cadence`: `monthly`
- `seat_count`: `1` for launch
- `delivery_format`: `csv`
- `skip_trace_enabled`: `true`
- `dnc_scrub_enabled`: `true`

## Node architecture

### 1) Trigger: `Cron - County Pull`
**Purpose:** Start the county batch on schedule.

**Inputs:**
- none

**Outputs:**
- `county_key`
- `run_id`
- `run_date`
- `trigger_type`

**Branch conditions:**
- If manual override flag is set, route to manual review start.
- Else continue to source fetch.

**Failure handling:**
- On cron failure or disabled workflow, send alert to `#ops` and create audit log entry.

---

### 2) `Set - County Config`
**Purpose:** Load the county metadata and control flags.

**Inputs:**
- `county_key`

**Outputs:**
- `state`
- `county`
- `source_id`
- `source_url`
- `seat_count`
- `skip_trace_enabled`
- `dnc_scrub_enabled`
- `delivery_format`
- `min_score`
- `suppression_list_id`

**Failure handling:**
- If config is missing, stop workflow and alert.

---

### 3) `HTTP Request - Fetch Source`
**Purpose:** Pull the raw county record feed or page data.

**Inputs:**
- `source_url`
- `source_auth` if needed
- `county_key`

**Outputs:**
- `raw_payload`
- `http_status`
- `fetched_at`
- `content_type`

**Branch conditions:**
- `2xx` -> continue
- `429/403/5xx` -> retry path
- empty body -> failure path

**Failure handling:**
- Retry up to 3 times with backoff.
- If still failing, create `raw_imports.status = failed`, log source outage, notify ops, and end run.

---

### 4) `Code - Raw File Hash + Store`
**Purpose:** Create immutable raw storage metadata before parsing.

**Inputs:**
- `raw_payload`
- `source_url`
- `county_key`
- `run_id`

**Outputs:**
- `file_hash`
- `file_url`
- `storage_key`
- `raw_record_count_estimate`

**Branch conditions:**
- If `file_hash` already exists for same source/date, mark as duplicate pull and stop downstream processing.

**Failure handling:**
- If storage write fails, do not parse; log and alert.

---

### 5) `Supabase - Insert raw_imports`
**Purpose:** Persist the source pull metadata.

**Inputs:**
- `county_key`
- `source_id`
- `source_date`
- `fetched_at`
- `file_url`
- `file_hash`
- `record_count`
- `status = imported`

**Outputs:**
- `raw_import_id`

**Failure handling:**
- If insert fails, abort run and notify ops.

---

### 6) `Execute Command - Normalize Source`
**Purpose:** Run the parser/normalizer script.

**Inputs:**
- `raw_payload` or `file_url`
- `county_key`
- `raw_import_id`

**Outputs:**
- normalized JSON array, one item per candidate lead

**Required output fields per item:**
- `raw_import_id`
- `county`
- `state`
- `source_type`
- `source_date`
- `owner_name`
- `property_address`
- `mailing_address`
- `parcel_id`
- `zip_code`
- `property_type`
- `distress_type`
- `event_key`
- `source_row_id`
- `parse_warnings[]`

**Failure handling:**
- If parser returns zero rows, send to QA failure path.
- If parse error rate exceeds threshold, mark raw import as failed and stop.

---

### 7) `Split In Batches - Normalize Items`
**Purpose:** Process each lead candidate individually.

**Inputs:**
- normalized lead items

**Outputs:**
- one item per candidate lead

---

### 8) `Function/Code - Field Standardization`
**Purpose:** Clean names and addresses.

**Transforms:**
- uppercase county/state
- title-case owner name
- normalize street suffixes
- trim whitespace
- split mailing vs property address
- standardize parcel format

**Outputs:**
- `owner_name_clean`
- `property_address_clean`
- `mailing_address_clean`
- `address_quality_flag`
- `name_quality_flag`

**Failure handling:**
- If required fields are missing, mark item `parse_status = incomplete` and route to exclusion log.

---

### 9) `Postgres/Supabase - Dedupe Check`
**Purpose:** Prevent duplicates at owner-property-source-event level.

**Inputs:**
- `state`
- `county`
- `parcel_id`
- `property_address_clean`
- `owner_name_clean`
- `source_type`
- `event_key`

**Outputs:**
- `dedupe_match = true/false`
- `existing_lead_id`
- `dedupe_reason`

**Branch conditions:**
- Match found -> duplicate branch
- No match -> continue

**Failure handling:**
- On query failure, stop run and alert because dedupe is mandatory.

---

### 10) `Postgres/Supabase - Suppression / DNC Match`
**Purpose:** Remove restricted records before enrichment.

**Inputs:**
- `owner_name_clean`
- `property_address_clean`
- `mailing_address_clean`
- `phone` if present
- `email` if present
- `suppression_list_id`

**Outputs:**
- `suppression_status`
- `suppression_reason`
- `dnc_status`

**Branch conditions:**
- Match on suppression list -> suppressed branch
- DNC match only -> keep record but mark DNC-aware fields and suppress for outreach export if policy requires
- No match -> continue

**Failure handling:**
- If suppression service is unavailable, default to fail-closed for delivery and alert ops.

---

### 11) `Code - Lane Classification`
**Purpose:** Assign lead lane.

**Inputs:**
- normalized fields
- source type
- distress type
- property type

**Outputs:**
- `lead_lane`
- `lane_reason`
- `lane_priority`

**Lane examples:**
- `tax_delinquent`
- `probate_estate`
- `foreclosure`
- `vacant_property`
- `absentee_owner`
- `commercial`
- `research_only`
- `suppressed`

**Branch conditions:**
- If lane is `suppressed` -> terminate from delivery path
- If lane is `research_only` -> keep for internal review only
- Else continue

---

### 12) `Code - Quality Score`
**Purpose:** Score lead usefulness for the buyer.

**Inputs:**
- `lead_lane`
- `property_type`
- `source_date`
- `address_quality_flag`
- `name_quality_flag`
- `dnc_status`
- `dedupe_status`
- `source_reliability_score`

**Outputs:**
- `lead_score` from 0-100
- `urgency_level` from 1-5
- `score_reason`
- `quality_tier`

**Typical branch thresholds:**
- `lead_score >= 80` -> premium branch
- `lead_score 60-79` -> standard branch
- `lead_score 40-59` -> nurture branch
- `< 40` -> exclude / research only

**Failure handling:**
- If scoring inputs are incomplete, assign conservative score and mark `score_reason = incomplete_data`.

---

### 13) `IF - Skip Trace Eligible?`
**Purpose:** Only skip trace records that passed quality and suppression checks.

**Condition:**
- `dedupe_status = new`
- `suppression_status = active or cleared`
- `lead_score >= min_score`
- `lead_lane != research_only`

**True branch:** skip trace
**False branch:** no enrichment, continue to QA/exclusion logging

---

### 14) `HTTP Request - Skip Trace Provider`
**Purpose:** Enrich approved records only.

**Inputs:**
- `owner_name_clean`
- `property_address_clean`
- `mailing_address_clean`
- `parcel_id`
- `county`
- `state`

**Outputs:**
- `phone`
- `email`
- `phone_type`
- `skip_trace_confidence`
- `skip_trace_provider_id`
- `skip_trace_status`

**Failure handling:**
- If provider fails, set `skip_trace_status = failed` and continue without contact data.
- Do not block the batch on enrichment failure.

---

### 15) `Post-skip-trace DNC Scrub`
**Purpose:** Apply contact-level suppression before export.

**Inputs:**
- `phone`
- `email`
- `owner_name_clean`
- `property_address_clean`

**Outputs:**
- `dnc_status`
- `scrubbed_at`
- `contact_export_eligible`

**Branch conditions:**
- DNC match -> keep lead, but remove contact fields from outbound file if policy requires
- No match -> eligible for export

**Failure handling:**
- If scrub service fails, fail closed on contact export and keep lead for non-contact export only.

---

### 16) `IF - Final Delivery Eligible?`
**Purpose:** Decide if the record enters the customer batch.

**Condition:**
- `lead_score >= min_score`
- `suppression_status != suppressed`
- `dedupe_status = new`
- `county = configured county`
- `lead_lane` allowed for customer’s territory right

**True branch:** staging table
**False branch:** exclusion log

---

### 17) `Postgres - Insert/Upsert leads`
**Purpose:** Store final lead record.

**Inputs:**
- all normalized fields
- enrichment fields
- scoring fields
- suppression flags

**Outputs:**
- `lead_id`

**Required output fields in the leads row:**
- `raw_import_id`
- `territory_id`
- `state`
- `county`
- `zip_code`
- `owner_name`
- `property_address`
- `mailing_address`
- `parcel_id`
- `property_type`
- `owner_type`
- `source_type`
- `source_date`
- `lead_lane`
- `phone`
- `email`
- `dnc_status`
- `skip_trace_confidence`
- `urgency_level`
- `lead_score`
- `score_reason`
- `suppression_status`
- `google_maps_url`
- `assessor_url`

---

### 18) `Postgres - Lead Assignment Lock`
**Purpose:** Prevent resale during active customer window.

**Inputs:**
- `lead_id`
- `customer_id`
- `territory_right_id`
- `exclusivity_window_start`
- `exclusivity_window_end`

**Outputs:**
- `assignment_id`
- `assignment_status`

**Branch conditions:**
- If lead already assigned inside active window -> exclude and log replacement/block reason
- If seat capacity reached -> hold or reject based on county rules

**Failure handling:**
- On lock conflict, use transaction retry once; if still conflicted, stop assignment for that item and alert.

---

### 19) `Code - Export Mapping`
**Purpose:** Build delivery columns.

**Inputs:**
- final lead rows

**Outputs:** CSV-ready export object

**Export fields:**
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
- `notes`
- `google_maps_url`
- `assessor_url`

---

### 20) `Spreadsheet File - Generate CSV/XLSX`
**Purpose:** Create deliverable file.

**Inputs:**
- export rows

**Outputs:**
- `delivery_file_url`
- `delivery_format`
- `delivery_row_count`

**Failure handling:**
- If file generation fails, keep records in staging and alert ops.

---

### 21) `Supabase - Insert deliveries`
**Purpose:** Register the delivery batch.

**Inputs:**
- `customer_id`
- `territory_id`
- `lead_lane`
- `delivery_file_url`
- `lead_count`
- `status = draft or sent`

**Outputs:**
- `delivery_id`

---

### 22) `Send Email / Storage Link`
**Purpose:** Deliver the batch.

**Inputs:**
- `customer_email`
- `delivery_file_url`
- `delivery_id`

**Outputs:**
- `sent_message_id`
- `sent_at`
- `delivery_status = sent`

**Failure handling:**
- If email fails, fall back to signed storage link and notify ops.

---

### 23) `Supabase - Audit Log`
**Purpose:** Record the whole run.

**Inputs:**
- `run_id`
- `county_key`
- `raw_import_id`
- `lead_count_raw`
- `lead_count_delivered`
- `lead_count_suppressed`
- `lead_count_duplicated`
- `lead_count_enriched`
- `status`

**Outputs:**
- audit record stored

---

### 24) `Slack/Email - Failure Alert`
**Purpose:** Notify ops when anything hard-fails.

**Triggers:**
- fetch failure after retries
- config missing
- dedupe failure
- suppression failure in fail-closed mode
- transaction conflict after retry
- export generation failure

**Payload:**
- `county_key`
- `run_id`
- `node_name`
- `error_message`
- `failed_item_count`
- `next_action`

## Recommended branch map

- **Fetch OK** -> raw storage -> raw_imports -> normalize
- **Fetch failed** -> alert + audit + stop
- **Duplicate pull** -> log only + stop downstream
- **Dedupe hit** -> exclusion log
- **Suppression hit** -> exclusion log or DNC-only path
- **Low score** -> nurture/research-only path
- **Skip trace eligible** -> enrich -> scrub -> final eligibility
- **Final eligible** -> leads insert -> assignment lock -> export -> delivery
- **Export ineligible** -> log exclusion reason

## Minimum failure rules

- Dedupe and suppression are fail-closed.
- Skip trace is fail-open, but only after quality approval.
- Export generation is fail-closed.
- Delivery email is fail-open to signed-link fallback.
- Every excluded row must have one exclusion reason.
- Every run must end with an audit log entry.

## LeadCurate v1 output contract

At the end of one county run, LeadCurate should produce:

- raw file stored immutably
- raw import row in database
- normalized lead candidates
- dedupe/suppression decision per record
- scored and classified leads
- enriched leads where approved
- final export file
- delivery log
- audit log
- failure log for anything excluded or blocked
