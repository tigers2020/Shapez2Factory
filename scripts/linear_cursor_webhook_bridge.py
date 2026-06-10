#!/usr/bin/env python3
"""Linear webhook → Cursor Automation webhook bridge.

Linear cannot attach Authorization headers. This service verifies Linear
webhooks, filters Shapez2Factory status/label events, and POSTs a compact
JSON payload to a Cursor Automation webhook trigger.

Environment (never commit secrets):
  CURSOR_AUTOMATION_WEBHOOK_URL  full URL from Automations UI after save
  CURSOR_AUTOMATION_WEBHOOK_TOKEN  Bearer token (crsr_...) without "Bearer "
  LINEAR_WEBHOOK_SECRET          optional; Linear signing secret
  WEBHOOK_BRIDGE_HOST            default 127.0.0.1
  WEBHOOK_BRIDGE_PORT            default 8766
  WEBHOOK_BRIDGE_PATH            default /linear/webhook

Run (local + ngrok):
  set CURSOR_AUTOMATION_WEBHOOK_URL=https://api2.cursor.sh/automations/webhook/...
  set CURSOR_AUTOMATION_WEBHOOK_TOKEN=crsr_...
  python scripts/linear_cursor_webhook_bridge.py

Point Linear Settings → API → Webhooks at your public URL, e.g.
  https://<ngrok-host>/linear/webhook
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

# Shapez2Factory team (Linear)
TEAM_ID = "3e7df740-a09e-4fa1-bc8c-43d4bbb47ddb"
STATE_TODO_ID = "56f97879-de6e-44f4-9335-a7ef84b536f7"
ROUTING_LABELS = frozenset(
    {
        "auto:research-done",
        "auto:spec-brainstorming",
        "auto:impl-blocked",
        "auto:verify-done",
    }
)
SKIP_TITLE_PREFIX = "[AUTOTEST]"
SKIP_LABEL = "reviewing"


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def verify_linear_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not secret:
        return True
    if not signature:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    expected = signature.removeprefix("sha256=")
    return hmac.compare_digest(digest, expected)


def _issue_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return data if isinstance(data, dict) else {}


def _state_id(data: dict[str, Any]) -> str:
    state = data.get("state")
    if isinstance(state, dict) and state.get("id"):
        return str(state["id"])
    return str(data.get("stateId") or "")


def _state_name(data: dict[str, Any]) -> str:
    state = data.get("state")
    if isinstance(state, dict) and state.get("name"):
        return str(state["name"])
    return ""


def _label_names(data: dict[str, Any]) -> list[str]:
    labels = data.get("labels")
    if isinstance(labels, list):
        return [str(x.get("name") or x) if isinstance(x, dict) else str(x) for x in labels]
    return []


def _state_changed(payload: dict[str, Any], data: dict[str, Any]) -> bool:
    updated_from = payload.get("updatedFrom")
    if not isinstance(updated_from, dict):
        return payload.get("action") == "create"
    if "stateId" in updated_from:
        before = str(updated_from.get("stateId") or "")
        after = _state_id(data)
        return bool(before and after and before != after)
    if "state" in updated_from:
        return True
    return False


def _labels_changed(payload: dict[str, Any]) -> bool:
    updated_from = payload.get("updatedFrom")
    if not isinstance(updated_from, dict):
        return False
    return "labelIds" in updated_from or "labels" in updated_from


def _in_team(data: dict[str, Any]) -> bool:
    team = data.get("team")
    if isinstance(team, dict) and str(team.get("id") or "") == TEAM_ID:
        return True
    return str(data.get("teamId") or "") == TEAM_ID


def _should_forward(payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
    if payload.get("type") != "Issue":
        return False, "ignore:not-issue", None

    data = _issue_data(payload)
    if not _in_team(data):
        return False, "ignore:team", None

    title = str(data.get("title") or "")
    if title.startswith(SKIP_TITLE_PREFIX):
        return False, "ignore:autotest", None

    labels = _label_names(data)
    if SKIP_LABEL in labels:
        return False, "ignore:reviewing", None

    identifier = str(data.get("identifier") or data.get("id") or "")
    url = str(data.get("url") or "")
    state_name = _state_name(data)
    state_id = _state_id(data)

    if _state_changed(payload, data):
        updated_from = payload.get("updatedFrom") if isinstance(payload.get("updatedFrom"), dict) else {}
        previous_state_id = str(updated_from.get("stateId") or "")
        if state_id == STATE_TODO_ID:
            body = {
                "event": "issue.status_changed",
                "issue_id": identifier,
                "issue_url": url,
                "team": "Shapez2Factory",
                "state": state_name or "Todo",
                "state_id": state_id,
                "previous_state_id": previous_state_id,
                "labels": labels,
            }
            return True, "forward:entered-todo", body

    if _labels_changed(payload, data) and state_name == "Todo":
        hit = [name for name in labels if name in ROUTING_LABELS]
        if hit:
            body = {
                "event": "issue.labels_changed",
                "issue_id": identifier,
                "issue_url": url,
                "team": "Shapez2Factory",
                "state": state_name,
                "labels": labels,
                "routing_labels": hit,
            }
            return True, "forward:todo-label", body

    return False, "ignore:no-match", None


class _Dedupe:
    def __init__(self, ttl_seconds: float = 90.0) -> None:
        self._ttl = ttl_seconds
        self._seen: dict[str, float] = {}

    def seen(self, key: str) -> bool:
        now = time.time()
        expired = [k for k, ts in self._seen.items() if now - ts > self._ttl]
        for k in expired:
            del self._seen[k]
        if key in self._seen:
            return True
        self._seen[key] = now
        return False


def forward_to_cursor(body: dict[str, Any]) -> tuple[int, str]:
    url = _env("CURSOR_AUTOMATION_WEBHOOK_URL")
    token = _env("CURSOR_AUTOMATION_WEBHOOK_TOKEN")
    if not url or not token:
        return 500, "missing CURSOR_AUTOMATION_WEBHOOK_URL or CURSOR_AUTOMATION_WEBHOOK_TOKEN"

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return resp.status, text[:500]
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return exc.code, text[:500]


def process_linear_payload(payload: dict[str, Any], dedupe: _Dedupe) -> dict[str, Any]:
    ok, reason, body = _should_forward(payload)
    if not ok or body is None:
        return {"ok": True, "action": reason}

    key = f"{body.get('event')}:{body.get('issue_id')}:{json.dumps(body, sort_keys=True)}"
    if dedupe.seen(key):
        return {"ok": True, "action": "dedupe", "reason": reason}

    status, detail = forward_to_cursor(body)
    return {
        "ok": 200 <= status < 300,
        "action": reason,
        "cursor_status": status,
        "cursor_detail": detail,
        "forwarded": body,
    }


def make_handler(dedupe: _Dedupe, linear_secret: str, path: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        def do_POST(self) -> None:
            if self.path.rstrip("/") != path.rstrip("/"):
                self.send_response(404)
                self.end_headers()
                return

            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length)
            signature = self.headers.get("Linear-Signature")

            if not verify_linear_signature(raw, signature, linear_secret):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"invalid linear signature")
                return

            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"invalid json")
                return

            result = process_linear_payload(payload, dedupe)
            code = 200 if result.get("ok", True) else 502
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))

    return Handler


def main() -> int:
    host = _env("WEBHOOK_BRIDGE_HOST", "127.0.0.1")
    port = int(_env("WEBHOOK_BRIDGE_PORT", "8766"))
    path = _env("WEBHOOK_BRIDGE_PATH", "/linear/webhook")
    linear_secret = _env("LINEAR_WEBHOOK_SECRET")

    if not _env("CURSOR_AUTOMATION_WEBHOOK_URL") or not _env("CURSOR_AUTOMATION_WEBHOOK_TOKEN"):
        print(
            "Set CURSOR_AUTOMATION_WEBHOOK_URL and CURSOR_AUTOMATION_WEBHOOK_TOKEN first.",
            file=sys.stderr,
        )
        return 2

    dedupe = _Dedupe()
    server = ThreadingHTTPServer((host, port), make_handler(dedupe, linear_secret, path))
    print(f"Linear→Cursor bridge listening on http://{host}:{port}{path}")
    print("Expose with ngrok/cloudflared; register URL in Linear webhooks.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
