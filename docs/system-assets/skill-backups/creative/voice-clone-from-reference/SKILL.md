---
name: voice-clone-from-reference
description: "Build a voice workflow from a reference clip: transcription, pacing analysis, legal/safety checks, and tool choices for cloning or matching tone."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [voice, cloning, reference-audio, pacing, tts]
---

# Voice Clone From Reference

Use when Derrick provides a reference voice clip and wants similar narration.

## Rules
- First separate two asks:
  1. exact voice cloning
  2. accent/tone/style matching
- Do not promise exact cloning if the tools are not installed or the legal/consent status is unclear.
- Prefer style-match over exact identity-match unless the user explicitly owns/has permission.

## Workflow
1. Get the reference audio or video clip.
2. Transcribe it and note:
   - speaking rate
   - pause lengths
   - pitch impression
   - accent / regional markers
   - emotional tone
3. Choose stack:
   - Draft / quick: edge/OpenAI/Cartesia/PlayHT with guided style notes
   - Open-source clone path: XTTS-v2, F5-TTS, OpenVoice
4. If exact clone is not feasible, create a voice spec instead:
   - gender/age band
   - accent
   - warmth
   - pacing map
   - emphasis map
5. Render line-by-line if needed and assemble with ffmpeg.

## Recommended tools
- XTTS-v2
- F5-TTS
- OpenVoice
- Kokoro for fast non-clone drafts
- ffmpeg for silence insertion, tempo, loudness, and mixing

## Output
Return:
- whether exact clone or style match is realistic
- chosen stack
- pacing map
- final audio path or next install step
