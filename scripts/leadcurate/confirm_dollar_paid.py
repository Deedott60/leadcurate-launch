#!/usr/bin/env python3
"""Queue a real Dollar Leads order after Derrick confirms Cash App payment."""
from __future__ import annotations

import argparse
import json
from urllib import error, request

from dollar_fulfillment_worker import CONTROL_URL, ENV


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", required=True)
    args = parser.parse_args()
    code = args.code.strip().upper()
    token = ENV.get("HOSTINGER_WEBHOOK_SECRET", "")
    if not token:
        raise SystemExit("HOSTINGER_WEBHOOK_SECRET is missing")

    payload = json.dumps({"action": "confirm_paid", "order_code": code}).encode()
    req = request.Request(
        CONTROL_URL,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-leadcurate-agent-token": token,
        },
    )
    try:
        with request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read())
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"Could not confirm {code}: {detail}") from exc

    if not result.get("ok"):
        raise SystemExit(f"Could not confirm {code}: {result.get('error', 'unknown error')}")
    job = result.get("job") or {}
    print(f"{code} queued for Danny. Status: {job.get('status', 'queued')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
