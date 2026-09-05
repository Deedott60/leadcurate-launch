#!/usr/bin/env python3
import argparse
import pathlib
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime

DISPATCHER = '/opt/leadcurate/scripts/scrape_dispatcher.py'
ESCALATE = '/opt/leadcurate/scripts/scrape_repair_escalate.py'


def main() -> int:
    ap = argparse.ArgumentParser(description='Run LeadCurate scrape dispatcher; escalate failures to Sonnet repair lane only.')
    ap.add_argument('--market', required=True)
    ap.add_argument('--lane', required=True)
    ap.add_argument('--no-escalate', action='store_true')
    ap.add_argument('extra', nargs=argparse.REMAINDER, help='extra args passed to scrape_dispatcher.py')
    args = ap.parse_args()

    cmd = ['python3', DISPATCHER, '--market', args.market, '--lane', args.lane]
    if args.extra:
        extra = args.extra[1:] if args.extra and args.extra[0] == '--' else args.extra
        cmd.extend(extra)

    print('Running:', ' '.join(shlex.quote(x) for x in cmd))
    proc = subprocess.run(cmd, cwd='/opt/leadcurate', text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end='')
    if proc.stderr:
        print(proc.stderr, end='', file=sys.stderr)
    if proc.returncode == 0:
        return 0

    log_dir = pathlib.Path('/opt/leadcurate/logs/scrape_failures')
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    log_path = log_dir / f'{stamp}_{args.market}_{args.lane}.log'
    log_path.write_text(
        'COMMAND: ' + ' '.join(shlex.quote(x) for x in cmd) + '\n'
        + f'EXIT: {proc.returncode}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n',
        errors='replace',
    )
    print(f'Scrape failed. Log: {log_path}', file=sys.stderr)
    if args.no_escalate:
        return proc.returncode

    esc_cmd = [
        'python3', ESCALATE,
        '--market', args.market,
        '--lane', args.lane,
        '--failed-command', ' '.join(shlex.quote(x) for x in cmd),
        '--error-file', str(log_path),
    ]
    print('Escalating scrape failure to Sonnet repair lane...', file=sys.stderr)
    return subprocess.call(esc_cmd, cwd='/opt/leadcurate')

if __name__ == '__main__':
    raise SystemExit(main())
