#!/usr/bin/env python3
"""Small Hostinger Agentic Mail sender for LeadCurate server-side jobs.

Requires:
  HOSTINGER_MAIL_TOKEN
  HOSTINGER_MAILBOX_RESOURCE_ID

By default this loads /opt/leadcurate/.env, then falls back to the process env.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_ENV_PATH = "/opt/leadcurate/.env"
DEFAULT_BASE_URL = "https://api.mail.hostinger.com"


def load_env_file(path: str = DEFAULT_ENV_PATH) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def env_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def discover_mailbox_resource_id(token: str, base_url: str) -> str:
    request = urllib.request.Request(
        f"{base_url}/api/v1/me",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
            payload = json.loads(body)
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Hostinger Mail /me {error.code}: {error_body}") from error

    mailboxes = payload.get("data", {}).get("mailboxes", [])
    preferred_address = os.environ.get("LEADCURATE_FROM_EMAIL", "hello@leadcurate.com")
    if "<" in preferred_address and ">" in preferred_address:
        preferred_address = preferred_address.split("<", 1)[1].split(">", 1)[0]
    preferred_address = preferred_address.strip().lower()

    for mailbox in mailboxes:
        if str(mailbox.get("address", "")).strip().lower() == preferred_address:
            resource_id = str(mailbox.get("resourceId", "")).strip()
            if resource_id:
                return resource_id

    if len(mailboxes) == 1:
        resource_id = str(mailboxes[0].get("resourceId", "")).strip()
        if resource_id:
            return resource_id

    raise RuntimeError("Could not discover HOSTINGER_MAILBOX_RESOURCE_ID from Hostinger Mail /me")


def send_mail(
    to: str | list[str],
    subject: str,
    body_html: str,
    body_text: str | None = None,
    *,
    display_name: str = "LeadCurate",
) -> dict[str, Any]:
    """Send one email through Hostinger Agentic Mail."""

    load_env_file(os.environ.get("LEADCURATE_ENV_FILE", DEFAULT_ENV_PATH))

    token = env_required("HOSTINGER_MAIL_TOKEN")
    base_url = os.environ.get("HOSTINGER_MAIL_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    mailbox_resource_id = os.environ.get("HOSTINGER_MAILBOX_RESOURCE_ID", "").strip()
    if not mailbox_resource_id:
        mailbox_resource_id = discover_mailbox_resource_id(token, base_url)

    recipients = [to] if isinstance(to, str) else to
    payload: dict[str, Any] = {
        "to": recipients,
        "displayName": display_name,
        "subject": subject,
        "html": body_html,
    }
    if body_text:
        payload["text"] = body_text

    url = f"{base_url}/api/v1/mailboxes/{mailbox_resource_id}/send"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            if response.status != 204:
                raise RuntimeError(f"Hostinger Mail {response.status}: {response_body}")
            return {"sent": True, "provider": "hostinger", "status": response.status}
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Hostinger Mail {error.code}: {error_body}") from error


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "Usage: send_mail.py TO SUBJECT BODY_HTML BODY_TEXT",
            file=sys.stderr,
        )
        return 2

    result = send_mail(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
