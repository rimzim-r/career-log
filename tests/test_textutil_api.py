import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

from careerlog.textutil import check_entry_text, parse_message, slugify


def test_slugify():
    assert slugify("Churn Model v2!") == "churn-model-v2"


def test_parse_message_with_and_without_project():
    assert parse_message("phishing | Trained the hybrid model and wrote results") == (
        "phishing", "Trained the hybrid model and wrote results")
    assert parse_message("Just a plain sentence about my week") == (
        "weekly-checkin", "Just a plain sentence about my week")


def test_check_entry_text():
    assert check_entry_text("too short") is not None
    assert check_entry_text("Built a forecasting model with LightGBM.") is None


def _post(port, token, message):
    req = urllib.request.Request(
        "http://127.0.0.1:%d/entries" % port,
        data=json.dumps({"message": message}).encode(),
        headers={"Content-Type": "application/json", "X-Token": token},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_webhook_adds_entry_and_rejects_bad_token(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CHECKIN_TOKEN", "secret-token")
    from careerlog import api
    from careerlog.store import load_entries

    server = HTTPServer(("127.0.0.1", 0), api.Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert _post(port, "wrong", "demo | Built something useful this week")[0] == 401
        assert _post(port, "secret-token", "short")[0] == 400
        status, body = _post(port, "secret-token", "demo | Built something useful this week")
        assert status == 201 and body["project"] == "demo"
    finally:
        server.shutdown()
    entries = load_entries()
    assert len(entries) == 1 and entries[0].source == "n8n" and entries[0].tags == ["weekly-checkin"]
