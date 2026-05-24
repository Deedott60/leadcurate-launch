---
name: shortform-virality-heuristics
description: "Judge whether a short-form concept has enough hook, novelty, clarity, retention, and comment/share potential without relying on generic clickbait."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [shortform, virality, hooks, retention, social-video]
---

# Shortform Virality Heuristics

Use when Derrick asks whether a short-form video idea could catch.

## Core scoring dimensions
1. Pattern interrupt in first second
2. Clarity: can a stranger understand it quickly?
3. Novelty / visual surprise
4. Native-platform fit (TikTok, IG Reels, X)
5. Rewatch value
6. Share/comment bait without cheap rage bait
7. Can a business plausibly want their own version?

## Strong signs
- One visual idea people immediately copy in comments/DMs
- Easy to imagine with another business/mascot/location
- Makes viewers ask: "Can you do this for me?"
- Short enough to replicate and customize quickly

## Weak signs
- Only works because of one specific trend audio
- Too much setup before payoff
- Looks like an ordinary promo with AI frosting
- Hard to explain in one sentence

## Output format
Return:
- viral potential: low/medium/high
- why it could spread
- whether it can sell as a service/product
- what niche should copy it first
- what would make it stronger
