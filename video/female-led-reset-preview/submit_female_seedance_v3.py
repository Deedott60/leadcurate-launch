import json
import base64
import time
import urllib.request
import pathlib

ROOT = pathlib.Path('/root/leadcurate-launch/video/female-led-reset-preview')
ASSETS = ROOT
JOBS = ROOT / 'jobs'
CLIPS = ROOT / 'clips'
for p in (JOBS, CLIPS):
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
        'file': 'scene1.png',
        'prompt': 'Premium cinematic female-led insurance-style commercial shot. Slow push-in on a Black professional woman in her 30s at an acquisitions desk reviewing county property records. Warm late-afternoon light, serious but calm expression, elegant realism, shallow depth of field, restrained commercial tone. No hype, no logos, no readable private data, no distortion.'
    },
    {
        'idx': 2,
        'file': 'scene2.png',
        'prompt': 'Premium trust-building female-led commercial shot. Close-up of the same Black professional woman turning a pen thoughtfully at the desk. Warm natural side light, quiet reflective mood, slight natural movement in shoulders and hands, cinematic realism, calm premium pacing. No logos, no readable data, no extra fingers.'
    },
    {
        'idx': 3,
        'file': 'scene3.png',
        'prompt': 'Premium female-led over-the-shoulder commercial shot of the same Black professional woman working at a laptop with a clean dark-mode property workflow interface. Warm dim room glow, subtle hand motion on trackpad, restrained ad look, shallow depth of field, professional confidence. No logos, no readable private data, no fake busy UI.'
    },
    {
        'idx': 4,
        'file': 'scene4.png',
        'prompt': 'Premium editorial female-led commercial shot, top-down view of the same woman placing elegant process cards across a dark walnut desk. Warm natural light, deliberate slow motion, calm insurance-ad pacing, polished but real. No logos, no clutter, no gimmicky animation.'
    },
    {
        'idx': 5,
        'file': 'scene5.png',
        'prompt': 'Premium cinematic female-led product-insert shot. The same Black professional woman gently scrolls a tablet with a sparse curated property list. Warm ambient light, shallow depth of field, clean restrained UI, quiet professional ad style, calm hand movement. No readable private data, no logos, no morphing UI.'
    },
    {
        'idx': 6,
        'file': 'scene6.png',
        'prompt': 'Premium final female-led commercial brand shot. The same Black professional woman stands beside a clean desk with county map, organized file stack, and warm window light. Very slow push-in, subtle confident expression, elegant negative space for later CTA, refined insurance-commercial mood. No logos, no readable data, no distortion.'
    },
]

NEGATIVE = 'cartoon, CGI, plastic skin, stock photo smile, luxury influencer vibe, hype marketing, fast cuts, extra fingers, distorted hands, fake readable text, warped screens, duplicated faces, oversaturated neon, scammy course aesthetic, cluttered desk, blue corporate lighting, changing ethnicity, changing hairstyle, changing wardrobe'

headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'HTTP-Referer': 'https://leadcurate.local',
    'X-Title': 'LeadCurate female Seedance v3',
}

def post_json(url, payload, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def get_json(url, timeout=60):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

print('Submitting female-led Seedance jobs...')
for s in scenes:
    img = (ASSETS / s['file']).read_bytes()
    data_url = 'data:image/png;base64,' + base64.b64encode(img).decode()
    payload = {
        'model': 'bytedance/seedance-2.0',
        'prompt': s['prompt'],
        'negative_prompt': NEGATIVE,
        'aspect_ratio': '16:9',
        'duration': 5,
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
    jid = json.loads(jf.read_text())['job']['id']
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
