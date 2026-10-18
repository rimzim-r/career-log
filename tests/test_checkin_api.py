import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer


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


def test_checkin_validation_and_duplicates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CHECKIN_TOKEN", "secret-token")
    from careerlog import api
    from careerlog.store import load_entries

    server = HTTPServer(("127.0.0.1", 0), api.Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        good = "demo | Trained the hybrid model and wrote up the results"
        assert _post(port, "wrong", good)[0] == 401
        assert _post(port, "secret-token", "short")[0] == 400
        status, body = _post(port, "secret-token", "demo | Built the model: [what you did and the result]")
        assert status == 400 and "placeholder" in body["error"]
        assert _post(port, "secret-token", good)[0] == 201
        status, body = _post(port, "secret-token", good)  # a retry from n8n
        assert status == 200 and body["duplicate"] is True
    finally:
        server.shutdown()
    entries = load_entries()
    assert len(entries) == 1
    assert entries[0].source == "n8n" and entries[0].tags == ["weekly-checkin"] and entries[0].project == "demo"
