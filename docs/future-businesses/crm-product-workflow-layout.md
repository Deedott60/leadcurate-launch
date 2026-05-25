# CRM — Product Workflow Layout

## What it is
A lightweight client dashboard / CRM / automation portal that lets us onboard clients, collect payment, store leads/files, control email/SMS settings, and route work through automations without needing an expensive all-in-one platform.

## Goal
Create a simple, repeatable internal + client-facing system that supports:
- client onboarding
- form capture
- payment confirmation
- email/SMS automation toggles
- lead/file delivery
- client-specific views/downloads
- low-touch monthly service delivery

## Core promise
Simple enough to run without heavy babysitting.
Cheap enough to start.
Expandable later.

## V1 Scope
### Admin side
- create client record
- choose package
- set email on/off
- set SMS on/off
- set lead/file delivery method
- track payment status
- view activity / job status

### Client side
- login or protected client page later
- view/download files
- see basic status
- receive messages/updates

## Core layers
1. **CRM layer**
   - EspoCRM or Twenty
   - stores client/contact records, notes, statuses

2. **Chat / inbox layer**
   - Chatwoot
   - website chat widget, inbox, possible shared communication channel

3. **Automation layer**
   - n8n
   - drives workflows behind the scenes
   - triggers email/SMS, lead delivery, follow-up, notifications

4. **Booking layer**
   - Cal.com
   - client booking / setup / support calls

5. **Email layer**
   - Mautic or provider + n8n
   - onboarding emails, follow-up, drip sequences, notifications

6. **SMS layer**
   - Twilio or similar provider through n8n
   - optional per client

7. **Payments layer**
   - Stripe
   - package/payment confirmation hooks

8. **Storage / file delivery layer**
   - simple file storage path first
   - lead CSV/XLSX delivery
   - client download area later

## Intake flow
1. Admin creates or imports client
2. Admin selects package
3. Admin sets communication preferences
4. Payment is confirmed
5. Workflow creates or updates client automation state
6. Deliverables begin routing automatically

## Example onboarding fields
- client/business name
- main contact
- email
- phone
- package
- SMS enabled yes/no
- email enabled yes/no
- booking link needed yes/no
- chat widget needed yes/no
- lead/file delivery destination
- notes

## Backend workflow logic
- form submitted or admin entry created
- record written to CRM/database
- payment status checked
- automation flags set
- SMS/email paths activated only if enabled
- delivery workflow connected to that client profile
- activity logged

## Human vs automated
### Automated
- create/update client workflow state
- send email/SMS sequences
- payment-triggered events
- file-ready notifications
- status changes

### Human
- initial setup QA
- custom package exceptions
- lead QA before delivery
- edge cases / support

## What to delay until later
- fancy website builder
- full white-label SaaS polish
- advanced analytics dashboards
- deep role/permission matrix
- complex multi-tenant productization before the base works

## First execution order
1. choose CRM core
2. choose file storage method
3. choose SMS provider
4. connect Stripe
5. build onboarding/admin form
6. connect n8n workflow
7. create one client flow end-to-end
8. test with one internal/client pilot
9. simplify anything annoying before scaling

## Stop condition
If setup or monthly maintenance still feels too manual after one pilot client, simplify the offer and reduce moving parts before adding features.
