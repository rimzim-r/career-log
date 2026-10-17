"""Checks that a generated bullet only says what its cited entries say."""
from __future__ import annotations

import re

# Words a bullet should only use if its cited entries use them too.
WATCH_TERMS = [
    "deployed", "deploy", "deployment", "production", "pipeline", "scaled",
    "scalable", "launched", "improved", "optimized", "automated", "end-to-end",
    "real-time", "led", "managed", "mentored", "kubernetes", "docker", "aws",
    "azure", "gcp", "spark", "hadoop", "tensorflow", "pytorch", "keras",
    "scikit-learn", "sklearn", "flask", "fastapi", "django", "tableau",
    "power bi", "sql", "mlops", "ci/cd", "api", "react", "java",
    "platform", "framework", "system", "robust", "state-of-the-art",
]

NUM = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
_WORD = re.compile(r"[a-z][a-z\-]{4,}")


def norm(text: str) -> str:
    for ch in ("\u2010", "\u2011", "\u2013", "\u2014"):
        text = text.replace(ch, "-")
    return text.lower()


def numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in NUM.findall(text)}


def has(text: str, term: str) -> bool:
    pattern = r"(?<![\w-])" + re.escape(term) + r"(?![\w-])"
    return re.search(pattern, text) is not None


def check_bullet(bullet_text: str, source_texts: list[str]) -> list[str]:
    """Return short, readable problems. An empty list means none were found.

    This catches numbers and risky words that the cited entries do not contain.
    It cannot catch every vague overclaim, so it supports a human check, not replaces it.
    """
    if not source_texts:
        return ["it cites no log entry"]
    source = norm(" ".join(source_texts))
    text = norm(bullet_text)
    issues = []
    missing = sorted(numbers(text) - numbers(source))
    if missing:
        issues.append("the number " + ", ".join(missing) + " is not in the cited entries")
    for term in WATCH_TERMS:
        if has(text, term) and not has(source, term):
            issues.append('the word "' + term + '" is not in the cited entries')
    return issues


def _content_words(text: str) -> set[str]:
    return set(_WORD.findall(norm(text)))


MAX_CITATIONS = 3


def tighten_citations(bullet_text: str, ids: list[str], text_by_id: dict[str, str]) -> list[str]:
    """Keep the entries that best support the bullet, at most MAX_CITATIONS.

    An entry qualifies if it shares a number with the bullet or at least three
    content words. Qualifying entries are ranked by how much they share. If none
    qualify, the first MAX_CITATIONS of the original list are kept.
    """
    bullet_nums = numbers(norm(bullet_text))
    bullet_words = _content_words(bullet_text)
    scored = []
    for i in ids:
        entry = text_by_id.get(i, "")
        shared_nums = bullet_nums & numbers(norm(entry))
        shared_words = bullet_words & _content_words(entry)
        if shared_nums or len(shared_words) >= 3:
            scored.append((2 * len(shared_nums) + len(shared_words), i))
    if not scored:
        return list(ids)[:MAX_CITATIONS]
    scored.sort(key=lambda pair: -pair[0])  # stable: ties keep their original order
    return [i for _score, i in scored[:MAX_CITATIONS]]
