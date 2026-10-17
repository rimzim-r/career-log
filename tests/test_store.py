from datetime import date

from careerlog.schema import LogEntry
from careerlog.store import add_entry, load_entries


def test_roundtrip(tmp_path):
    p = tmp_path / "log.jsonl"
    add_entry(LogEntry(date=date(2026, 10, 1), text="Built model", tags=["ml"]), p)
    add_entry(LogEntry(date=date(2026, 10, 8), text="Deployed app", project="proj-a"), p)
    entries = load_entries(p)
    assert len(entries) == 2
    assert entries[0].tags == ["ml"]
    assert entries[1].project == "proj-a"


def test_load_missing_file_returns_empty(tmp_path):
    assert load_entries(tmp_path / "nope.jsonl") == []
