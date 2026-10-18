"""A tiny local webhook so n8n can add weekly check-in replies to the log.

Run it:    python -m careerlog.api
Send it:   POST http://127.0.0.1:8765/entries
           header  X-Token: <CHECKIN_TOKEN from .env>
           body    {"message": "project-name | what I did this week"}

It only appends to data/log.jsonl and never touches the search index. The
Streamlit app adds new entries to the index the next time it answers a question
(or run: python -m careerlog index). Run it from the project root.
"""
from __future__ import annotations

import json
import os
import secrets
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv

from .entry import build_entry
from .store import add_entry, load_entries
from .textutil import parse_message

load_dotenv()

HOST = os.environ.get("CHECKIN_HOST", "127.0.0.1")
PORT = int(os.environ.get("CHECKIN_PORT", "8765"))
MAX_BODY = 20_000


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        if self.path != "/entries":
            return self._send(404, {"error": "not found"})

        token = os.environ.get("CHECKIN_TOKEN", "")
        sent = self.headers.get("X-Token", "")
        if not token or not secrets.compare_digest(sent.encode(), token.encode()):
            return self._send(401, {"error": "bad or missing token"})

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._send(400, {"error": "bad length"})
        if length > MAX_BODY:
            return self._send(413, {"error": "message too large"})
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            message = str(body.get("message", ""))
        except (json.JSONDecodeError, AttributeError):
            return self._send(400, {"error": "send JSON like {\"message\": \"...\"}"})

        project, text = parse_message(message)
        try:
            entry = build_entry(project, date.today(), text, "weekly-checkin")
        except ValueError as exc:
            return self._send(400, {"error": str(exc)})
        # n8n may retry a request, so the same reply must not be added twice
        if any(e.project == entry.project and e.text == entry.text for e in load_entries()):
            return self._send(200, {"duplicate": True, "project": entry.project})
        entry = entry.model_copy(update={"source": "n8n"})
        add_entry(entry)
        self._send(201, {"id": entry.id, "project": entry.project})

    def log_message(self, fmt, *args) -> None:  # one short line per request, no client details
        print("checkin webhook:", fmt % args)


def main() -> None:
    if not os.environ.get("CHECKIN_TOKEN"):
        raise SystemExit("Set CHECKIN_TOKEN in .env first (any long random string).")
    server = HTTPServer((HOST, PORT), Handler)
    print("Listening on http://%s:%d/entries  (Ctrl+C to stop)" % (HOST, PORT))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")


if __name__ == "__main__":
    main()
