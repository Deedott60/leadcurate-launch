# Ella handoff — LeadCurate / Hermes coordination

This file is for the local Hermes agent “Ella” running on Derrick's laptop.

## Current project

- Repo: `https://github.com/Deedott60/leadcurate-launch.git`
- Main working directory on VPS Hermes: `/root/leadcurate-launch`
- Product/brand: LeadCurate — premium property-owner lead/data product for real estate investors.
- Goal: build high-quality landing page, visuals, and eventually a realistic commercial-style video.

## Current status

- Landing page exists and was used for HyperFrames experiments.
- Fast website-walkthrough promo was cleaner but too much like a site scroll.
- A commercial-style HyperFrames draft was rejected as not good enough.
- Direction changed: use realistic image/video generation + voice + editing, not HyperFrames alone.
- OpenAI/Codex image generation was configured on VPS Hermes:
  - `image_gen.provider = openai-codex`
  - `image_gen.model = gpt-image-2`
- Visual storyboard frames were generated and committed.

## Important committed assets

- `docs/commercial-storyboard.md` — written storyboard structure
- `assets/storyboard/leadcurate-commercial-visual-storyboard.png` — 4-panel storyboard contact sheet
- `assets/storyboard/frame-01-problem.png`
- `assets/storyboard/frame-02-solution-tablet.png`
- `assets/storyboard/frame-03-advisor-call.png`
- `assets/storyboard/frame-04-brand-close.png`

## User creative direction

Derrick wants:

- realistic female professional character
- real work desk / work-from-home or small office environment
- believable property/data workflow, not fake luxury office stock-photo vibes
- tablet/laptop, county/property printouts, notes, real work materials
- premium, trustworthy, serious, commercial-quality tone
- not a website walkthrough
- similar pacing/tone/aesthetic to a LinkedIn commercial reference he shared earlier: realistic person, calm voiceover, professional trust-building, problem → helpful solution → brand promise

## Suggested next work for Ella

1. Pull the repo:
   ```bash
   git clone https://github.com/Deedott60/leadcurate-launch.git
   cd leadcurate-launch
   ```

2. Review:
   ```bash
   docs/commercial-storyboard.md
   assets/storyboard/leadcurate-commercial-visual-storyboard.png
   ```

3. Help define a better character board:
   - same female character from multiple angles
   - home/work desk setup
   - tablet/laptop/product interaction
   - close-up of hands/tablet
   - CTA/end-card pose

4. Coordinate with VPS Hermes through GitHub:
   - commit changes to repo branches or main as directed by Derrick
   - leave notes in `docs/` or issues if needed
   - avoid editing the same files at the same time without communicating

## Tool notes

- VPS Hermes has GitHub access for this repo.
- Local Ella can use Codex/Hermes locally for laptop-side work.
- For high-quality commercial production, still needed or helpful:
  - video generation backend such as FAL or xAI video
  - high-quality voice provider such as ElevenLabs or OpenAI voice
  - stable image iteration using OpenAI/Codex image generation

## Coordination pattern

Preferred simple pattern:

- GitHub repo = shared source of truth
- Docs in `docs/` = creative direction / decisions
- Assets in `assets/` = images/storyboards/references
- Branches or commits = work handoff
- Derrick can ask either Hermes agent to read this handoff and continue
