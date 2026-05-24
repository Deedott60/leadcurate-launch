---
name: open-source-voice-stack
description: Choose and run reusable voice-generation stacks with realistic pacing; prefer GPU-aware choices and avoid pretending NVIDIA Riva is feasible without an NVIDIA GPU.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [voice, tts, audio, open-source, pacing, realism]
---

# Open-Source Voice Stack

Use when Derrick asks for reusable high-quality voice creation, lip-sync-adjacent narration prep, or ElevenLabs-like alternatives.

## First checks
1. Check whether `nvidia-smi` exists.
2. If no NVIDIA GPU is present, do **not** recommend NVIDIA Riva as the main path.
3. Prefer solutions that match the actual machine.

## Provider ranking

### If NVIDIA GPU exists
- Consider: NVIDIA Riva, XTTS-v2, CosyVoice, F5-TTS.
- Riva is realistic only with a supported NVIDIA GPU + Docker/NIM/Riva setup.

### If no NVIDIA GPU exists
- Prefer: Kokoro, XTTS-v2 CPU tests, edge/OpenAI/Cartesia/PlayHT fallback for production.
- Be honest that CPU-only open-source voices are usually slower and less polished than ElevenLabs.

## Reusable recommendation format
For any voice recommendation, provide:
- realism level
- latency level
- hardware requirement
- best use (drafts vs finals)
- whether it is good enough for commercial narration

## Commercial rule
For premium narration:
- drafts can use open-source
- finals should use the best-sounding available provider if the open-source result is not there yet

## Honesty rule
Do not promise interruption-ready, conversational, Realtime-voice quality unless the stack actually supports it in this environment.
