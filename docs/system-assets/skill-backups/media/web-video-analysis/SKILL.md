---
name: web-video-analysis
description: Analyze embedded videos and social-media commercials from URLs when the user wants the actual video content, transcript, storyline, or on-screen text—not just surrounding post/page text.
tags:
  - media
  - video
  - browser
  - social-media
---

# Web Video Analysis

Use this skill when the user shares a URL to a page containing an embedded video, short commercial, social post video, or marketing clip and asks what it says/shows, asks for a review, or appears to expect analysis of the video itself.

## Core rule

Do not stop at the surrounding post text. If a page has a video player, inspect the video/commercial directly before summarizing. A user correction like “I thought you would be able to see the commercial as well” means the workflow missed the primary artifact.

## Workflow

1. Open the page in the browser and dismiss sign-in or modal overlays if possible.
2. Confirm whether a video is present using the page snapshot and browser vision.
3. Watch or sample the actual video:
   - Use browser vision on visible frames to describe scenes and read burned-in subtitles/on-screen text.
   - Seek through the video at several timestamps when the player allows it.
   - Prefer start/middle/end plus any caption-heavy portions.
4. If DOM access is needed, inspect video elements, including shadow DOM:
   - `document.querySelectorAll('video')` may be empty for custom players.
   - Recursively walk shadow roots and inspect `video.currentSrc`, `data-sources`, `data-captions-url`, `poster`, `duration`, `currentTime`, and `textTracks`.
5. If a direct media URL is visible and download is appropriate, fetch it for richer analysis.
   - Some hosts require browser-like headers or a referer.
   - For LinkedIn-style DMS URLs, `curl -L -A 'Mozilla/5.0 ...' -e 'https://www.linkedin.com/' URL -o /tmp/video.mp4` can succeed when a plain Python/urllib request gets 403.
6. Use `ffprobe` to verify duration/streams.
7. For concise visual review, create a contact sheet with ffmpeg, e.g.:
   - `ffmpeg -y -i /tmp/video.mp4 -vf "fps=1/2,scale=480:-1,tile=4x6:padding=8:margin=8:color=white" -frames:v 1 /tmp/contact.jpg`
   - Analyze the contact sheet with vision to reconstruct storyline and captions.
8. If captions are not available as text tracks, compile visible subtitles from sampled frames and label them as “visible/likely” rather than claiming a perfect transcript.
9. Final answer should clearly separate:
   - What the surrounding post says, if relevant.
   - What the video/commercial itself shows.
   - Any extracted or approximate caption/transcript sequence.
   - End-card/contact information visible in the video.

## Pitfalls

- Social pages often expose post text in the accessibility tree while the actual video is only visible through the rendered player. Do not infer video content from the post caption alone.
- `document.querySelectorAll('video')` can miss players inside shadow DOM; recurse through shadow roots.
- Browser canvas export may fail with a tainted-canvas security error when drawing cross-origin video. Use direct download + ffmpeg contact sheets when possible.
- If direct download initially fails with 403, retry with browser-like user agent and referer before giving up.
- Avoid hard negative claims like “I can’t see the video” until you have tried browser vision on the visible player and DOM/media URL inspection.

## References

- `references/linkedin-commercial-analysis.md` — Example workflow notes from analyzing a LinkedIn-hosted TMA Insurance Trust commercial, including shadow-DOM media extraction and ffmpeg contact-sheet review.
