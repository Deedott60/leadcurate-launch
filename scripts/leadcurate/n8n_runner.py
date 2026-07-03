#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path("/opt/leadcurate/scripts")
ENV_PATH = Path("/opt/leadcurate/.env")
HOST = os.environ.get("LEADCURATE_RUNNER_HOST", "172.18.0.1")
PORT = int(os.environ.get("LEADCURATE_RUNNER_PORT", "8788"))


def load_env() -> dict[str, str]:
    env = os.environ.copy()
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return env


ENV = load_env()
RUNNER_KEY = ENV.get("N8N_API_KEY", "")


def run(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, text=True, capture_output=True, env=ENV, timeout=900)
    payload: dict[str, Any] = {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "cmd": cmd,
        "stderr": proc.stderr.strip(),
    }
    stdout = proc.stdout.strip()
    try:
        payload["result"] = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        payload["stdout"] = stdout
    return payload


def task_command(payload: dict[str, Any]) -> list[str]:
    task = payload.get("task")
    if task == "delivery":
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "leadcurate_pipeline.py"),
            "--market",
            str(payload["market"]),
            "--lane",
            str(payload["lane"]),
            "--count",
            str(int(payload.get("count") or 25)),
        ]
        if payload.get("allow_scrape"):
            cmd.append("--allow-scrape")
        return cmd
    if task == "ground_floor_seed":
        return [sys.executable, str(SCRIPT_DIR / "ground_floor_pipeline.py"), "seed-investments"]
    if task == "ground_floor_scan":
        return [sys.executable, str(SCRIPT_DIR / "ground_floor_pipeline.py"), "scan-investments"]
    if task == "ground_floor_package":
        return [sys.executable, str(SCRIPT_DIR / "ground_floor_pipeline.py"), "package-county", "--market", str(payload["market"])]
    raise ValueError(f"Unsupported task: {task}")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("leadcurate-runner " + fmt % args + "\n")

    def respond(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)
        self.close_connection = True

    def do_GET(self) -> None:
        if self.path == "/health":
            self.respond(200, {"ok": True, "service": "leadcurate-n8n-runner"})
            return
        self.respond(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/run":
            self.respond(404, {"ok": False, "error": "not found"})
            return
        if not RUNNER_KEY or self.headers.get("X-LeadCurate-Runner-Key") != RUNNER_KEY:
            self.respond(401, {"ok": False, "error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
            payload = json.loads(self.rfile.read(length) or b"{}")
            result = run(task_command(payload))
            self.respond(200 if result["ok"] else 500, result)
        except Exception as exc:
            self.respond(500, {"ok": False, "error": str(exc)})


def main() -> int:
    if not RUNNER_KEY:
        print("N8N_API_KEY is required in /opt/leadcurate/.env", file=sys.stderr)
        return 2
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"LeadCurate n8n runner listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
