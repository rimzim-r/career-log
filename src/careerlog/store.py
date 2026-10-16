import json
from pathlib import Path
from .schema import LogEntry

DEFAULT_PATH = Path("data/log.jsonl")


def add_entry(entry: LogEntry, path: Path = DEFAULT_PATH) -> LogEntry:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")
    return entry


def load_entries(path: Path = DEFAULT_PATH) -> list[LogEntry]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [LogEntry.model_validate_json(line) for line in f if line.strip()]