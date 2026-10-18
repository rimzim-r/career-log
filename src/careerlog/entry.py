"""Validation for a new log entry typed into the Streamlit form."""
from __future__ import annotations

import re
from datetime import date

from .schema import LogEntry

MIN_CHARS = 25
MAX_CHARS = 1000
MAX_TAGS = 8


def slugify(name: str) -> str:
    """'Churn Model v2' becomes 'churn-model-v2'."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def parse_tags(raw: str) -> list[str]:
    tags: list[str] = []
    for part in raw.split(","):
        tag = slugify(part)
        if tag and tag not in tags:
            tags.append(tag)
    return tags[:MAX_TAGS]


def build_entry(project: str, day: date, text: str, tags_raw: str = "") -> LogEntry:
    """Return a clean LogEntry, or raise ValueError with a message for the user."""
    slug = slugify(project or "")
    if not slug:
        raise ValueError("Choose a project, or type a name for a new one.")

    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) < MIN_CHARS:
        raise ValueError(
            "Write at least %d characters: what you did, and a real result if you have one." % MIN_CHARS
        )
    if len(text) > MAX_CHARS:
        raise ValueError("Keep an entry under %d characters. Split it into two entries." % MAX_CHARS)
    if re.search(r"\[[^\]]+\]", text):
        raise ValueError("Replace the [bracketed] placeholder with real details before adding.")
    if day > date.today():
        raise ValueError("The date cannot be in the future.")

    return LogEntry(date=day, project=slug, text=text, tags=parse_tags(tags_raw), source="manual")
