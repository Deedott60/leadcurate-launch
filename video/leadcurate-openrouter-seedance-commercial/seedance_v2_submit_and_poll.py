import json
import base64
import time
import urllib.request
import pathlib

ROOT = pathlib.Path('/root/leadcurate-launch/video/leadcurate-openrouter-seedance-commercial-v2')
ASSETS = ROOT / 'assets'
JOBS = ROOT / 'jobs'
CLIPS = ROOT / 'clips'
for p in (ASSETS, JOBS, CLIPS):
    p.mkdir(parents=True, exist_ok=True)

key = None
for line in pathlib.Path('/root/.hermes/.env').read_text().splitlines():
    if line.startswith('OPENROUTER_API_KEY='):
        key = line.split('=', 1)[1].strip().strip('"')
        break
if not key:
    raise SystemExit('OPENROUTER_API_KEY not found')

scenes = [
    {
        'idx': 1,
        'file': '01-desk-fatigue.png',
        'prompt': 'Premium cinematic insurance-style commercial shot. Slow push-in over the shoulder of a professional acquisitions desk in warm late-afternoon light. One hand rests on printed spreadsheets and parcel records, pen nearby, half-empty coffee cup, tasteful dark wood desk, subtle fatigue and realism, shallow depth of field, restrained color grade. No face visible. No readable private data, no logos, no distortion.',
    },
    {
        'idx': 2,
        'file': '02-thoughtful-hands.png',
        'prompt': 'Premium trust-building commercial shot. Close-up of two thoughtful hands at a desk, one turning a pen slowly, blurred monitor glow in the background, warm natural side light, quiet and reflective, shallow depth of field, realistic skin texture, cinematic stillness. No face visible. No logos, no readable data, no extra fingers.',
    },
    {
        'idx': 3,
        'file': '03-laptop-solution.png',
        'prompt': 'Premium cinematic over-the-shoulder low angle of a laptop on a tasteful desk showing a clean minimal dark-mode property workflow interface with sparse rows and subtle green status markers. Hand on trackpad moving gently. Warm dim room glow, shallow depth of field, restrained ad look. No face visible, no fake busy UI, no readable private data, no logos.',
    },
    {
        'idx': 4,
        'file': '04-process-cards.png',
        'prompt': 'Premium editorial commercial shot, top-down flat lay on dark walnut desk. Four physical process cards arranged cleanly across the desk with understated motion, representing source, refine, prioritize, reserve. Warm natural light, minimalist composition, cinematic overhead shot, calm insurance-ad pacing. No hands, no screens, no logos, no clutter.',
    },
    {
        'idx': 5,
        'file': '05-tablet-product.png',
        'prompt': 'Premium cinematic product-insert shot. Slow dolly across a tablet lying flat on a desk showing a sparse curated property list with subtle green status indicators. Hand enters frame gently to scroll once. Warm ambient light, shallow depth of field, clean restrained UI, quiet professional ad style. No readable private data, no logos, no morphing UI.',
    },
    {
        'idx': 6,
        'file': '06-brand-endcard-desk.png',
        'prompt': 'Premium final commercial brand shot. Clean desk with warm window light, county map folded neatly, organized file stack, dark laptop softly blurred in background, emerald accent folder, elegant negative space reserved for later CTA text. Very slow pull-back, refined insurance-commercial mood. No faces, no logos, no readable data, no distortion.',
    },
]

NEGATIVE = 'cartoon, CGI, plastic skin, stock photo smile, luxury influencer vibe, hype marketing, fast cuts, extra fingers, distorted hands, fake readable text, warped screens, duplicated faces, oversaturated neon, scammy course aesthetic, cluttered desk, blue corporate lighting'

headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'HTTP-Referer': 'https://leadcurate.local',
    'X-Title': 'LeadCurate Seedance v2',
}


def post_json(url, payload, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def get_json(url, timeout=60):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


print('Submitting Seedance 2.0 v2 jobs...')
for s in scenes:
    img = (ASSETS / s['file']).read_bytes()
    data_url = 'data:image/png;base64,' + base64.b64encode(img).decode()
    payload = {
        'model': 'bytedance/seedance-2.0',
        'prompt': s['prompt'],
        'negative_prompt': NEGATIVE,
        'aspect_ratio': '16:9',
        'duration': 5 if s['idx'] != 6 else 6,
        'resolution': '720p',
        'first_frame': data_url,
        'generate_audio': False,
        'watermark': False,
    }
    out = post_json('https://openrouter.ai/api/v1/videos', payload)
    record = {'scene': s['idx'], 'image': s['file'], 'job': out, 'prompt': s['prompt']}
    (JOBS / f"scene{s['idx']}-job.json").write_text(json.dumps(record, indent=2))
    print(f"submitted scene {s['idx']}: {out.get('id')} status={out.get('status')}")
    time.sleep(1)

print('Polling jobs...')
for s in scenes:
    jf = JOBS / f"scene{s['idx']}-job.json"
    job = json.loads(jf.read_text())['job']
    jid = job['id']
    while True:
        status = get_json(f'https://openrouter.ai/api/v1/videos/{jid}')
        st = status.get('status')
        print(f"scene {s['idx']} status={st}")
        if st == 'completed':
            url = status['unsigned_urls'][0]
            req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
            data = urllib.request.urlopen(req, timeout=180).read()
            outpath = CLIPS / f"scene{s['idx']}.mp4"
            outpath.write_bytes(data)
            print(f"downloaded scene {s['idx']} -> {outpath} ({outpath.stat().st_size} bytes)")
            break
        if st in ('failed', 'error', 'cancelled'):
            raise RuntimeError(f"scene {s['idx']} failed: {status}")
        time.sleep(10)

print('All scenes complete.')
for p in sorted(CLIPS.glob('scene*.mp4')):
    print(p.name, p.stat().st_size)
