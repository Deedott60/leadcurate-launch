# 10 — JS Blocker Bypass (Playwright on VPS)

**Status:** Playwright 1.60.0 + Chromium installed on the VPS (`leadcurate-vps`).
**Date:** 2026-06-20.
**Owner:** Claude (orchestrator). Codex / Hermes can use the same install.

## What changed

Three blocker classes that previously stopped data pulls are now solvable in-pipeline:

1. **JS-injected download links** (Harris HCAD pattern) — solved via Playwright `page.content()` after `networkidle`
2. **SPA + API backend** (Jefferson AL Capture CAMA pattern) — solved via Playwright network capture → server-side replay
3. **ASP.NET postback forms** (Forsyth NC pattern) — solved via `requests.Session()` with VIEWSTATE preservation

## Discovery — Jefferson AL Capture CAMA

The `eringcapture.jccal.org` portal is a React SPA backed by **CamaCloud / Capture CAMA** at `jeffersonexpress.capturecama.com` using AWS Cognito for auth.

API endpoints observed:
- `POST /GetTheme`, `/GetTenantDetails`, `/GetTenantAssets`, `/GetTenantFeatures`, `/GetGlobalValuesByString`
- `GET /get-cognito-credentials-decrypted` (Cognito identity pool)
- `GET /api/redirects?tenant=eringcapture.jccal.org`

**Importance:** Capture CAMA is the dominant assessment vendor in AL/MS/GA. Cracking this pattern unlocks every county that runs on it, not just Jefferson AL.

## Cost-control: model choice for routine ops

For Hermes-driven scraping/processing jobs, do NOT use Gemini Flash — its safety filters block ~30% of legitimate property records (names + addresses trigger PII filter). Use one of:

| Model | $/MTok | Best for |
|---|---|---|
| Claude Haiku 4.5 | ~$1 in / $5 out | Reliable parsing, mid-complexity reasoning |
| DeepSeek V3 | $0.27 in / $1.10 out | Bulk text manipulation, no safety theater |
| Local Ollama (Llama 3.1 8B) | $0 | High-volume formatting, simple filtering |

Recommendation: Set Hermes fallback chain to `openai-codex → deepseek → ollama-local`.

## Skill location

Full playbook with code templates: [`C:\Users\lenovo\.claude\skills\leadcurate-js-blocker-bypass\SKILL.md`](../../../../.claude/skills/leadcurate-js-blocker-bypass/SKILL.md).

Loaded automatically when Claude/Codex encounter scraping failures matching the symptom triggers.

## Pending work

- Click through the Capture CAMA search form to capture the actual parcel-list XHR endpoint (delinquent data isn't on the landing page — needs interaction)
- Replicate Jefferson AL pattern against other AL counties using same vendor (Mobile, Madison, Tuscaloosa)
- Add Cobb GA and Harris TX rows to the source catalog in `09-data-pipeline-status.md`
