#!/usr/bin/env python3
"""Always-on deterministic Dollar Leads fulfillment worker for Danny's VPS."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error, request

from send_dollar_delivery import send_delivery


ENV_PATH = Path("/opt/leadcurate/.env")
REPO = Path("/root/leadcurate-launch")
CONTROL_URL = "https://jdmlsraqioigbukspduo.supabase.co/functions/v1/dollar-fulfillment-control"
DELIVERY_ROOT = Path("/opt/leadcurate/deliveries/dollar-leads")


def load_env() -> dict[str, str]:
    env = os.environ.copy()
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return env


ENV = load_env()


def control(action: str, **payload: Any) -> dict[str, Any]:
    token = ENV.get("HOSTINGER_WEBHOOK_SECRET", "")
    if not token:
        raise RuntimeError("HOSTINGER_WEBHOOK_SECRET is missing")
    body = json.dumps({"action": action, **payload}).encode()
    req = request.Request(CONTROL_URL, data=body, method="POST", headers={"Content-Type": "application/json", "x-leadcurate-agent-token": token})
    try:
        with request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read())
    except error.HTTPError as exc:
        raise RuntimeError(f"control {action} failed ({exc.code}): {exc.read().decode('utf-8', 'replace')}") from exc
    if not result.get("ok"):
        raise RuntimeError(str(result.get("error") or f"control {action} failed"))
    return result


def cut(job: dict[str, Any], batch_no: int) -> Path:
    final_dir = DELIVERY_ROOT / job["order_code"]
    if final_dir.exists() and (final_dir / "manifest.json").exists():
        return final_dir
    if int(job["pack_size"]) == 20:
        raise RuntimeError("Fresh Scrub requires a same-day verification artifact before automated fulfillment")
    cmd = [
        sys.executable,
        str(REPO / "scripts/leadcurate/cut_dollar_pack.py"),
        "--code", job["order_code"],
        "--market", job["market"],
        "--lane", job["lane"],
        "--batch-no", str(batch_no),
        "--pack-size", str(job["pack_size"]),
        "--cycle-slug", job["cycle_slug"],
        "--job-id", job["id"],
    ]
    proc = subprocess.run(cmd, cwd=REPO, env=ENV, text=True, capture_output=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "cutter failed")
    if not final_dir.exists():
        raise RuntimeError("cutter succeeded without creating the delivery directory")
    return final_dir


def fulfill(job: dict[str, Any]) -> None:
    batch_no = int(control("next_batch", job_id=job["id"])["batch_no"])
    delivery_dir = cut(job, batch_no)
    send_delivery(job, delivery_dir)
    control("complete", job_id=job["id"], delivery_dir=str(delivery_dir), batch_no=batch_no)


def main() -> int:
    while True:
        try:
            job = control("claim").get("job")
            if not job:
                time.sleep(5)
                continue
            try:
                fulfill(job)
            except Exception as exc:
                control("fail", job_id=job["id"], error=str(exc))
        except Exception as exc:
            print(f"fulfillment poll failed: {exc}", flush=True)
            time.sleep(15)


if __name__ == "__main__":
    raise SystemExit(main())
