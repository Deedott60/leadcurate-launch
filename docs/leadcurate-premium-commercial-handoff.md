# LeadCurate Premium Commercial Handoff

## Important production rule
Do **not** use Ella's footage and do **not** finish this in HyperFrames. This is a fresh, Danny-built commercial package.

## Model/API usage verified
OpenRouter key works for director/planning/QA models. Relevant available OpenRouter models observed:

- `openai/gpt-4o` — director, script, visual QA, image critique
- `openai/gpt-4o-mini` — fast prompt iteration
- `openai/gpt-audio` / `openai/gpt-audio-mini` — audio-capable text/audio model endpoint
- `google/gemini-3.5-flash` — multimodal video/image analysis
- `google/gemini-3.1-flash-image-preview` — text/image output via OpenRouter if supported by account
- `bytedance-seed/seed-2.0-lite` / `bytedance-seed/seed-2.0-mini` — multimodal analysis/planning (`text+image+video -> text`), not direct video render in OpenRouter inventory
- `anthropic/claude-sonnet-4.6` — premium script/brand critique

For actual image-to-video rendering, use whichever video backend is connected in the execution environment: Seedance/SeaDance, Kling, Runway, Luma, Minimax/Hailuo, Higgsfield, Veo, or FAL/Replicate wrapper. Use the prompts below.

## Concept
A realistic LinkedIn/trust-ad style commercial: one serious investor/operator moves from messy public records to a reviewed, limited-seat LeadCurate county batch. Slow push-ins, natural desk light, close-up hands, phone follow-up, restrained overlays, premium voice, soft ambient music. No hype. No guaranteed deals.

## Voiceover, 35s
Most investors are working the same recycled property lists. LeadCurate starts with the county first: reviewing source records, checking usable volume, and refining batches before access is sold. Your team gets cleaner files, score reasons, source dates, contact data where available, and practical tools to work the batch with confidence. No hype. No guaranteed deals. Just better starting data for serious investors. LeadCurate. Check county availability.

## Scene timing and image-to-video prompts

### 1 — 0:00-0:06 — Problem / desk
Use `assets/01-morning-desk.png`.
Prompt: slow cinematic push-in toward the investor at the desk, realistic breathing and small eye movement, morning window light, subtle paper movement, professional LinkedIn insurance commercial pacing, 35mm lens, shallow depth of field, no text warping, no extra fingers.
Overlay: `Stale property lists waste time.`

### 2 — 0:06-0:12 — Review source records
Use `assets/02-review-records.png`.
Prompt: over-the-shoulder slow dolly movement, the investor reviews blurred county records, gentle hand movement near laptop, realistic screen glow, premium trust-building ad, no readable fake text, no distorted UI.
Overlay: `Review the county first.`

### 3 — 0:12-0:17 — County selectivity
Use `assets/03-map-marker.png`.
Prompt: macro close-up, hand places marker pin on county parcel map, subtle rack focus from pin to records, warm light, realistic hand anatomy, no logos, no fake readable addresses.
Overlay: `Source context before access is sold.`

### 4 — 0:17-0:23 — Clean batch/product insert
Use `assets/04-tablet-batch.png`.
Prompt: slow slider move across tablet and record sheets, minimal clean blurred rows and green score badges, premium product-insert style, no legible private data, no morphing rows.
Overlay: `Cleaner files. Score reasons. Source dates.`

### 5 — 0:23-0:29 — Human follow-up/process
Use `assets/05-phone-call.png`.
Prompt: subtle handheld push-in while investor takes a calm professional phone call, natural smile, confident but restrained, desk environment consistent, warm daylight, realistic human micro-movements.
Overlay: `Practical tools for real follow-up.`

### 6 — 0:29-0:35 — Trust/CTA
Use `assets/06-final-cta-space.png`.
Prompt: slow pull-back or very slow push-in, protagonist looks toward camera calmly, left negative space preserved for brand CTA, premium trust-ad ending, no text generated in video.
Overlay/End card: `LeadCurate.` + `Limited-seat county property data.` + `Check county availability.`

## Negative prompt for all video scenes
cartoon, CGI, plastic skin, luxury influencer ad, hype marketing, fast cuts, distorted hands, extra fingers, fake readable text, warped screens, duplicated faces, changing protagonist, flickering logo, stock-photo smile, unrealistic office, oversaturated neon, scammy course aesthetic.

## Music direction
Subtle premium bed: warm piano/pad, low pulse, no trap drums, no hype risers. Mix under voice. Fade in first second, fade out last two seconds.

## Voice direction
Professional, calm, grounded, mid-30s to 50s, trust-building. Not radio-announcer. Slightly warm, confident, restrained.
