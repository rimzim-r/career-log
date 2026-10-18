import sys
import types
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

import rag_backend  # noqa: E402
from careerlog.schema import LogEntry  # noqa: E402


def _entry(i):
    return LogEntry(id="e%d" % i, date=date(2026, 10, i), project="p", text="Entry number %d in the log." % i)


def test_sync_indexes_only_entries_the_index_is_missing(monkeypatch):
    log = [_entry(1), _entry(2), _entry(3)]
    added = []
    fake_collection = types.SimpleNamespace(get=lambda include=None: {"ids": ["e1", "e2"]})
    monkeypatch.setitem(sys.modules, "careerlog.index", types.SimpleNamespace(
        get_collection=lambda: fake_collection, build_index=lambda es: added.extend(es)))
    monkeypatch.setattr("careerlog.store.load_entries", lambda: log)
    rag_backend._sync_index()
    assert [e.id for e in added] == ["e3"]


def test_sync_never_raises(monkeypatch):
    def boom():
        raise RuntimeError("index missing")
    monkeypatch.setitem(sys.modules, "careerlog.index", types.SimpleNamespace(get_collection=boom, build_index=boom))
    rag_backend._sync_index()  # must not raise


def test_status_cache_follows_the_log_file(tmp_path, monkeypatch):
    stamps = iter([(1, 10), (2, 20)])
    monkeypatch.setattr(rag_backend, "_log_stamp", lambda: next(stamps))
    calls = []
    monkeypatch.setattr(rag_backend, "_live_status_for", lambda stamp: calls.append(stamp) or (True, 0, ""))
    rag_backend._live_status()
    rag_backend._live_status()
    assert calls == [(1, 10), (2, 20)]
