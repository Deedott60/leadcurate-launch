#!/usr/bin/env python3
"""LeadCurate snapshot wrapper with prior-pull retention.

Usage:
  snapshot_with_history.py <market> <snapshot.csv> [--out <tiered.csv>]

Behavior:
  1. Finds the latest existing snapshot CSV for <market> under
     /opt/leadcurate/snapshots/<market>/, excluding _prior and *_tiered files.
  2. Copies that previous snapshot into _prior/<timestamp>.csv before tiering.
  3. Runs tier_classifier.py on the supplied snapshot with --prior pointing at
     the newest retained prior pull when one exists.
  4. Keeps only the latest 3 _prior CSVs.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/opt/leadcurate')
SNAPSHOTS = ROOT / 'snapshots'
CLASSIFIER = ROOT / 'scripts' / 'tier_classifier.py'


def is_snapshot_csv(path: Path) -> bool:
    if path.suffix.lower() != '.csv':
        return False
    if '_prior' in path.parts:
        return False
    name = path.name.lower()
    return not (name.endswith('_tiered.csv') or name.endswith('-tiered.csv'))


def latest_snapshot(market_dir: Path, current: Path) -> Path | None:
    current_resolved = current.resolve() if current.exists() else current.absolute()
    candidates: list[Path] = []
    if market_dir.exists():
        for p in market_dir.rglob('*.csv'):
            if not is_snapshot_csv(p):
                continue
            try:
                if p.resolve() == current_resolved:
                    continue
            except FileNotFoundError:
                pass
            candidates.append(p)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def retain_latest(prior_dir: Path, keep: int = 3) -> None:
    priors = sorted(prior_dir.glob('*.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in priors[keep:]:
        old.unlink()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('market', help='Market slug, e.g. wake-nc or cobb-ga')
    ap.add_argument('snapshot', help='Current snapshot CSV to classify')
    ap.add_argument('--out', help='Output CSV path; default is <snapshot>_tiered.csv')
    ap.add_argument('--classifier', default=str(CLASSIFIER), help='tier_classifier.py path')
    args = ap.parse_args()

    market = args.market.strip().lower()
    snapshot = Path(args.snapshot).expanduser().resolve()
    if not snapshot.exists():
        raise SystemExit(f'FATAL: snapshot not found: {snapshot}')

    market_dir = SNAPSHOTS / market
    prior_dir = market_dir / '_prior'
    prior_dir.mkdir(parents=True, exist_ok=True)

    previous = latest_snapshot(market_dir, snapshot)
    prior_for_classifier: Path | None = None
    if previous:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        dest = prior_dir / f'{previous.stem}_{stamp}.csv'
        shutil.copy2(previous, dest)
        prior_for_classifier = dest
        print(f'Copied previous snapshot to {dest}', file=sys.stderr)
    else:
        existing_priors = sorted(prior_dir.glob('*.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
        if existing_priors:
            prior_for_classifier = existing_priors[0]
            print(f'No current previous snapshot found; using latest retained prior {prior_for_classifier}', file=sys.stderr)
        else:
            print('No previous snapshot found; running without --prior', file=sys.stderr)

    retain_latest(prior_dir, keep=3)

    cmd = [sys.executable, args.classifier, str(snapshot)]
    if prior_for_classifier and prior_for_classifier.exists():
        cmd += ['--prior', str(prior_for_classifier)]
    if args.out:
        cmd += ['--out', args.out]

    print('Running:', ' '.join(cmd), file=sys.stderr)
    return subprocess.call(cmd)


if __name__ == '__main__':
    raise SystemExit(main())
