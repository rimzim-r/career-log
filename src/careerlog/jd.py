"""Helpers for job-description mode."""
from __future__ import annotations

import re

MIN_JD_CHARS = 80
MAX_JD_CHARS = 6000
MAX_REQUIREMENTS = 6

_STOP = set(
    "and the for with from that this your you our are will have has can using use work experience "
    "skills skill ability strong knowledge years year plus etc including such other more able good "
    "of in on to a an or as at by be is it".split()
)


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9+#]+", text.lower())


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 4 and word.endswith("s") else word


def clean_jd(text: str) -> str:
    """Collapse whitespace and cap the length. Raises ValueError if there is too little text."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) < MIN_JD_CHARS:
        raise ValueError(
            "Paste more of the job description. The responsibilities and requirements sections work best."
        )
    return text[:MAX_JD_CHARS]


def ground_requirements(candidates, jd_text: str) -> list[str]:
    """Keep only requirements whose words all appear in the job description.

    The model proposes the list, but nothing it invents survives this filter.
    """
    jd_words = {_stem(w) for w in _words(jd_text)}
    kept: list[str] = []
    for item in candidates or []:
        if not isinstance(item, str):
            continue
        item = re.sub(r"\s+", " ", item).strip(" .;,-")
        if not 2 <= len(item) <= 60:
            continue
        tokens = [_stem(w) for w in _words(item) if w not in _STOP]
        if not tokens or any(t not in jd_words for t in tokens):
            continue
        if item.lower() not in [k.lower() for k in kept]:
            kept.append(item)
    return kept[:MAX_REQUIREMENTS]
