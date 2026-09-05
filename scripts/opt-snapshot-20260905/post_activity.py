#!/usr/bin/env python3
"""Post a message to activity_feed. Usage: python3 post_activity.py <event_type> <source> <title> <body> <target>"""
import sys, json, urllib.request, os

SB_URL = os.getenv('LEADCURATE_SUPABASE_URL', 'https://jdmlsraqioigbukspduo.supabase.co')
SB_KEY = os.getenv('LEADCURATE_SUPABASE_KEY', 'sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4')

def post_activity(event_type, source, title, body, target='all'):
    payload = {
        'event_type': event_type,
        'source': source,
        'title': title,
        'body': body,
        'target': target
    }
    req = urllib.request.Request(
        SB_URL.rstrip() + '/rest/v1/activity_feed',
        data=json.dumps(payload).encode(),
        method='POST',
        headers={
            'apikey': SB_KEY,
            'Authorization': 'Bearer ' + SB_KEY,
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body_resp = r.read().decode()
            print(f"HTTP {r.status}: {body_resp[:500]}")
            return True
    except Exception as e:
        print(f"activity post failed: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: post_activity.py <event_type> <source> <title> <body> [target]")
        sys.exit(1)
    event_type = sys.argv[1]
    source = sys.argv[2]
    title = sys.argv[3]
    body_text = sys.argv[4]
    target = sys.argv[5] if len(sys.argv) > 5 else 'all'
    post_activity(event_type, source, title, body_text, target)
