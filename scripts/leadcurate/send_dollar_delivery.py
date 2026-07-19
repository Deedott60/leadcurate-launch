#!/usr/bin/env python3
"""Send a completed Dollar Leads delivery through Hostinger Agentic Mail."""
from __future__ import annotations

import base64
import html
import json
import os
from pathlib import Path
from typing import Any
from urllib import error, request


ENV_PATH = Path("/opt/leadcurate/.env")
MAIL_BASE = "https://api.mail.hostinger.com"


def load_env() -> None:
    if not ENV_PATH.exists():
        return
    for raw in ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def mailbox_id(token: str, base: str) -> str:
    configured = os.environ.get("HOSTINGER_MAILBOX_RESOURCE_ID", "").strip()
    if configured:
        return configured
    req = request.Request(f"{base}/api/v1/me", headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    with request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read())
    mailboxes = payload.get("data", {}).get("mailboxes", [])
    if not mailboxes:
        raise RuntimeError("Hostinger mailbox was not found")
    return str(mailboxes[0]["resourceId"])


def attachment(path: Path, content_type: str) -> dict[str, str]:
    return {"filename": path.name, "content": base64.b64encode(path.read_bytes()).decode("ascii"), "contentType": content_type}


def send_delivery(job: dict[str, Any], delivery_dir: Path) -> dict[str, Any]:
    load_env()
    token = os.environ.get("HOSTINGER_MAIL_TOKEN", "").strip()
    if not token:
        raise RuntimeError("HOSTINGER_MAIL_TOKEN is missing")
    csv_files = list(delivery_dir.glob("*.csv"))
    xlsx_files = list(delivery_dir.glob("*.xlsx"))
    if len(csv_files) != 1 or len(xlsx_files) != 1:
        raise RuntimeError("delivery directory must contain exactly one CSV and one XLSX")

    code = html.escape(str(job["order_code"]))
    name = html.escape(str(job["customer_name"]))
    market = html.escape(str(job["market_display"]))
    lane = html.escape(str(job["lane_display"]))
    count = int(job["pack_size"])
    body_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:580px;margin:0 auto;color:#101418;line-height:1.55;">
      <div style="background:#101418;color:#fff;padding:18px 22px;border-radius:10px 10px 0 0;font-size:20px;font-weight:800;">DOLLAR<span style="color:#16a34a;">LEADS</span></div>
      <div style="border:1px solid #e4e8ec;border-top:0;border-radius:0 0 10px 10px;padding:22px;">
        <p>Hi {name},</p>
        <p>Your Dollar Leads order is attached in both CSV and Excel formats.</p>
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr><td style="padding:5px 0;color:#5b6672;">Order</td><td style="font-weight:700;">{code}</td></tr>
          <tr><td style="padding:5px 0;color:#5b6672;">Market</td><td style="font-weight:700;">{market}</td></tr>
          <tr><td style="padding:5px 0;color:#5b6672;">Category</td><td style="font-weight:700;">{lane}</td></tr>
          <tr><td style="padding:5px 0;color:#5b6672;">Records</td><td style="font-weight:700;">{count:,}</td></tr>
        </table>
        <p>This file contains public-record property data. It does not include skip-traced phone numbers or email addresses. You are responsible for outreach compliance.</p>
        <p>Questions? Reply to this email.</p>
        <p>The Dollar Leads Team</p>
      </div>
    </div>"""
    body_text = f"Hi {job['customer_name']},\n\nYour Dollar Leads order {job['order_code']} is attached in CSV and Excel formats.\n\nMarket: {job['market_display']}\nCategory: {job['lane_display']}\nRecords: {count}\n\nThis file does not include skip-traced phone numbers or email addresses. You are responsible for outreach compliance.\n\nThe Dollar Leads Team"
    base = os.environ.get("HOSTINGER_MAIL_BASE_URL", MAIL_BASE).rstrip("/")
    mailbox = mailbox_id(token, base)
    payload = {
        "to": [job["customer_email"]],
        "displayName": "Dollar Leads",
        "subject": f"Your Dollar Leads files: {job['order_code']}",
        "html": body_html,
        "text": body_text,
        "attachments": [
            attachment(csv_files[0], "text/csv"),
            attachment(xlsx_files[0], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ],
    }
    req = request.Request(f"{base}/api/v1/mailboxes/{mailbox}/send", data=json.dumps(payload).encode(), method="POST", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=90) as response:
            if response.status != 204:
                raise RuntimeError(f"Hostinger Mail returned {response.status}")
    except error.HTTPError as exc:
        raise RuntimeError(f"Hostinger Mail {exc.code}: {exc.read().decode('utf-8', 'replace')}") from exc
    return {"sent": True, "to": job["customer_email"], "csv": csv_files[0].name, "xlsx": xlsx_files[0].name}
