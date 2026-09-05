#!/usr/bin/env python3
import argparse
import pathlib
import shlex
import subprocess
import sys

SONNET_MODEL = 'anthropic/claude-sonnet-5'
SONNET_PROVIDER = 'openrouter'


def read_text(path: str | None, limit: int = 12000) -> str:
    if not path:
        return ''
    p = pathlib.Path(path)
    if not p.exists():
        return f'[error log not found: {path}]'
    text = p.read_text(errors='replace')
    return text[-limit:]


def main() -> int:
    ap = argparse.ArgumentParser(description='Escalate a failed LeadCurate scrape/parser task to Sonnet only for focused repair.')
    ap.add_argument('--market', required=True)
    ap.add_argument('--lane', required=True)
    ap.add_argument('--failed-command', required=True)
    ap.add_argument('--error-file')
    ap.add_argument('--notes', default='')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    err = read_text(args.error_file)
    prompt = f'''LeadCurate scrape/data repair lane. You are Sonnet being used only because a scraper/parser/data build failed.

Rules:
- Do not do general chat.
- Do not browse randomly.
- Inspect only the relevant LeadCurate scripts/files.
- Prefer existing scripts and patterns.
- Patch only what is required for this market/lane failure.
- Rerun the failed command or a smaller equivalent verification.
- Maximum two repair attempts.
- Stop for CAPTCHA, login wall, paid portal, missing credentials, legal uncertainty, or uncertain delivery quality.
- Do not touch /site/, pricing, data files unrelated to this market/lane, Facebook/Hermes upgrade, or n8n workflows.

Market: {args.market}
Lane: {args.lane}
Failed command: {args.failed_command}
Notes: {args.notes}
Error/log tail:
{err}

Deliverable: fix the scraper/parser/build issue if safe, rerun verification, and report exact files changed and command output. If unsafe or not fixable in two attempts, stop with a concise blocker.'''

    cmd = [
        'hermes',
        '--provider', SONNET_PROVIDER,
        '--model', SONNET_MODEL,
        '--skills', 'scrape-failure-routing',
        '-z', prompt,
    ]
    if args.dry_run:
        print(' '.join(shlex.quote(x) for x in cmd))
        return 0
    return subprocess.call(cmd, cwd='/opt/leadcurate')

if __name__ == '__main__':
    raise SystemExit(main())
