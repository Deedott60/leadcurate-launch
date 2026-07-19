#!/usr/bin/env python3
"""Route known Dollar Leads customer email to Hermes for guarded replies.

The worker only consumes activity_feed events explicitly typed mail:hermes.
Hermes drafts a strict JSON decision. This process, not the model, performs the
authenticated send. High-risk messages are escalated and never auto-replied.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import parse, request


SB_URL = "https://jdmlsraqioigbukspduo.supabase.co"
SB_KEY = "sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4"
REPLY_URL = f"{SB_URL}/functions/v1/send-reply"
ENV_PATH = Path("/opt/leadcurate/.env")
STATE_PATH = Path("/var/lib/leadcurate/hermes-mail-state.json")
HERMES = Path("/usr/local/lib/hermes-agent/venv/bin/hermes")
REPO = Path("/root/leadcurate-launch")
RISK_WORDS = re.compile(
    r"\b(refund|chargeback|dispute|cancel|cancellation|lawyer|attorney|legal|"
    r"sue|lawsuit|fraud|scam|complaint|wrong list|change category|switch category|"
    r"custom order|duplicate charge)\b",
    re.I,
)


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


def api(method: str, path: str, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
    merged = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}", "Content-Type": "application/json"}
    merged.update(headers or {})
    body = json.dumps(payload).encode() if payload is not None else None
    req = request.Request(f"{SB_URL}{path}", data=body, method=method, headers=merged)
    with request.urlopen(req, timeout=45) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


def post_activity(event_type: str, title: str, body: str) -> None:
    api("POST", "/rest/v1/activity_feed", {
        "event_type": event_type,
        "source": "hermes-mail-worker",
        "title": title,
        "body": body,
        "target": "derrick",
    }, {"Prefer": "return=minimal"})


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state = {"started_at": datetime.now(timezone.utc).isoformat(), "processed_ids": []}
    save_state(state)
    return state


def save_state(state: dict[str, Any]) -> None:
    temp = STATE_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    temp.replace(STATE_PATH)


def events(state: dict[str, Any]) -> list[dict[str, Any]]:
    query = parse.urlencode({
        "target": "eq.hermes",
        "event_type": "eq.mail:hermes",
        "created_at": f"gte.{state['started_at']}",
        "order": "created_at.asc",
        "limit": "100",
    })
    rows = api("GET", f"/rest/v1/activity_feed?{query}") or []
    done = set(state.get("processed_ids", []))
    return [row for row in rows if row.get("id") not in done]


def parse_decision(output: str) -> dict[str, str]:
    candidates = re.findall(r"\{[^{}]*\}", output, flags=re.S)
    for candidate in reversed(candidates):
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if data.get("action") in {"reply", "escalate"}:
            return {str(k): str(v) for k, v in data.items()}
    raise ValueError("Hermes did not return a valid reply/escalate JSON decision")


def ask_hermes(message: dict[str, Any]) -> dict[str, str]:
    prompt = f"""You are Danny, the guarded Dollar Leads customer-email operator.
Draft a concise, natural reply only for routine questions about payment steps, order status, file format, included fields, delivery timing, or how to use a delivered file.
Never approve or negotiate refunds, cancellations, disputes, custom work, category changes, legal issues, complaints, pricing exceptions, or promises outside the recorded order. Escalate those.
Do not claim payment was received unless the supplied message explicitly says the operator confirmed it.
Do not include owner data or property data. Do not use em dashes. Do not use a personal-name signature.
Return exactly one JSON object and nothing else:
{{"action":"reply","body":"reply text ending with The Dollar Leads Team"}}
or {{"action":"escalate","reason":"short reason"}}.

Inbound email:
{json.dumps(message, ensure_ascii=False)}"""
    proc = subprocess.run(
        [str(HERMES), "chat", "-Q", "-q", prompt, "--source", "dollar-leads-mail", "--max-turns", "1"],
        cwd=REPO,
        env=ENV,
        text=True,
        capture_output=True,
        timeout=240,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"Hermes exited {proc.returncode}")
    return parse_decision(proc.stdout)


def send_reply(message: dict[str, Any], body: str) -> None:
    token = ENV.get("HOSTINGER_WEBHOOK_SECRET", "")
    if not token:
        raise RuntimeError("HOSTINGER_WEBHOOK_SECRET is missing on the VPS")
    api("POST", "/functions/v1/send-reply", {
        "to": message["from_addr"],
        "subject": message.get("subject") or "Your Dollar Leads order",
        "body": body,
        "inbound_email_id": message["inbound_email_id"],
    }, {"x-leadcurate-agent-token": token})


def handle(event: dict[str, Any]) -> None:
    message = json.loads(event.get("body") or "{}")
    required = {"inbound_email_id", "from_addr", "subject", "preview"}
    if not required.issubset(message):
        raise ValueError("mail:hermes event is missing required fields")
    combined = f"{message.get('subject', '')}\n{message.get('preview', '')}"
    if RISK_WORDS.search(combined):
        post_activity("conf:urgent", "Customer email needs your approval", f"From {message['from_addr']}: {message.get('subject')}. Danny did not reply because the message matched a human-review topic.")
        return
    decision = ask_hermes(message)
    if decision["action"] == "escalate":
        post_activity("conf:urgent", "Customer email needs your approval", f"From {message['from_addr']}: {message.get('subject')}. Danny's reason: {decision.get('reason', 'human review requested')}.")
        return
    body = decision.get("body", "").strip()
    if not body:
        raise ValueError("Hermes returned an empty reply")
    send_reply(message, body)
    post_activity("conf:done", "Danny replied to Dollar Leads email", f"Routine reply sent through hello@leadcurate.com to {message['from_addr']} for subject: {message.get('subject')}.")


def main() -> int:
    state = load_state()
    while True:
        try:
            for event in events(state):
                try:
                    handle(event)
                except Exception as exc:
                    post_activity("conf:blocker", "Danny email automation failed", f"Event {event.get('id')}: {exc}")
                state.setdefault("processed_ids", []).append(event["id"])
                state["processed_ids"] = state["processed_ids"][-2000:]
                save_state(state)
        except Exception as exc:
            print(f"poll failed: {exc}", flush=True)
        time.sleep(20)


if __name__ == "__main__":
    raise SystemExit(main())
