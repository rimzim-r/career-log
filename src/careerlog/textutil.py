"""Small text helpers shared by the Streamlit app and the n8n webhook."""
from __future__ import annotations

import re

MIN_ENTRY_CHARS = 20
MAX_ENTRY_CHARS = 1500


def slugify(name: str) -> str:
    """'Churn Model v2' becomes 'churn-model-v2'."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:60]


def parse_message(message: str, default_project: str = "weekly-checkin") -> tuple[str, str]:
    """Split 'project | what I did' into (project, text).

    Without a pipe the whole message is the text and the default project is used.
    """
    message = message.strip()
    if "|" in message:
        left, right = message.split("|", 1)
        project = slugify(left)
        if project and right.strip():
            return project, right.strip()
    return default_project, message


def check_entry_text(text: str) -> str | None:
    """Return a problem message, or None when the text is fine to save."""
    text = text.strip()
    if len(text) < MIN_ENTRY_CHARS:
        return "Write at least a full sentence about what you did (%d characters or more)." % MIN_ENTRY_CHARS
    if len(text) > MAX_ENTRY_CHARS:
        return "That is too long for one entry. Split it into smaller entries."
    return None
