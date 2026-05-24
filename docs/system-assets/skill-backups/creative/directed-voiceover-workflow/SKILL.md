---
name: directed-voiceover-workflow
description: Turn a user script plus pacing notes into a directed voiceover workflow using available TTS, punctuation/SSML-like pause controls, and ffmpeg timing edits.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [voiceover, tts, pacing, ssml, ffmpeg, narration]
---

# Directed Voiceover Workflow

Use when Derrick gives a script and says how it should sound: slower, warmer, pause here, stress this line, male/female, calm, dramatic, etc.

## Goal
Translate plain-language direction into a repeatable voiceover pipeline.

## Inputs
- final script
- voice preference: male/female/older/younger/calm/authoritative/warm
- pacing notes: where to pause, slow down, speed up, emphasize
- output purpose: draft, commercial, narration, reel, explainer

## Workflow
1. Normalize the script into short phrases.
2. Mark pauses explicitly using line breaks and punctuation.
3. If provider supports SSML or similar controls, use them.
4. If provider does not expose pause controls directly, render phrase-by-phrase and assemble with ffmpeg.
5. Use ffmpeg to insert silence, adjust tempo, and mix music underneath.
6. Return both:
   - the final audio
   - the pacing map used to generate it

## Available local fallback
- edge-tts / Hermes TTS is good for fast drafts.
- Use ffmpeg for silence insertion, atempo, loudness control, fades, and mixing.

## Honesty rule
Do not claim perfect human acting performance from low-cost TTS. Be clear whether the result is:
- draft quality
- good enough for a promo
- final commercial quality

## Output format
When asked, provide:
- selected voice type
- pacing map
- generated audio path
- whether it is draft or final quality
