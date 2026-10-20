"""Checks that a generated bullet only says what its cited entries say."""
from __future__ import annotations

import re

# Words matched exactly. A bullet may only use one if its cited entries use it too.
WATCH_TERMS = [
    "production", "led", "real-time", "end-to-end", "state-of-the-art",
    "kubernetes", "docker", "aws", "azure", "gcp", "spark", "hadoop", "tensorflow", "pytorch",
    "keras", "scikit-learn", "sklearn", "flask", "fastapi", "django", "tableau", "power bi",
    "sql", "mlops", "ci/cd", "api", "react", "java",
]
# Roots matched as word beginnings, so "deploy" also covers deployed, deploying and deployment.
WATCH_ROOTS = [
    "deploy", "launch", "scal", "optimi", "automat", "improv", "mentor", "manag",
    "pipeline", "platform", "framework", "system", "robust",
]

NUM = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
_WORD = re.compile(r"[a-z][a-z\-]{4,}")
MAX_CITATIONS = 3


def norm(text: str) -> str:
    for ch in ("\u2010", "\u2011", "\u2013", "\u2014"):
        text = text.replace(ch, "-")
    return text.lower()


def numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in NUM.findall(text)}


def has(text: str, term: str) -> bool:
    pattern = r"(?<![\w-])" + re.escape(term) + r"(?![\w-])"
    return re.search(pattern, text) is not None


def _find_root(text: str, root: str):
    match = re.search(r"(?<![\w-])" + re.escape(root) + r"[\w-]*", text)
    return match.group(0) if match else None


def risky_words(bullet_text: str, source_text: str) -> list[str]:
    """Risky words that the bullet uses and the source does not."""
    text, source = norm(bullet_text), norm(source_text)
    found = []
    for term in WATCH_TERMS:
        if has(text, term) and not has(source, term):
            found.append(term)
    for root in WATCH_ROOTS:
        word = _find_root(text, root)
        if word and _find_root(source, root) is None:
            found.append(word)
    return found


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
    for word in risky_words(bullet_text, " ".join(source_texts)):
        issues.append('the word "' + word + '" is not in the cited entries')
    return issues


def _content_words(text: str) -> set[str]:
    return set(_WORD.findall(norm(text)))


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


def add_number_sources(bullet_text: str, ids: list[str], project_by_id: dict, text_by_id: dict) -> list[str]:
    """Cite the entry that holds a number the bullet uses, when it is in the same project.

    A number borrowed from a different project is never added, so it stays flagged.
    At the citation cap, the weakest citation is swapped out, unless it supports a
    number the bullet uses. The result never exceeds MAX_CITATIONS.
    """
    cited = list(ids)
    projects = {project_by_id.get(i) for i in cited} - {None}
    if not projects:
        return cited
    bullet_nums = numbers(norm(bullet_text))
    known = numbers(norm(" ".join(text_by_id.get(i, "") for i in cited)))
    for number in sorted(bullet_nums - known):
        if number in known:
            continue
        source_id = next(
            (other for other, text in text_by_id.items()
             if other not in cited and project_by_id.get(other) in projects
             and number in numbers(norm(text))),
            None,
        )
        if source_id is None:
            continue
        if len(cited) >= MAX_CITATIONS:
            weakest = cited[-1]
            if numbers(norm(text_by_id.get(weakest, ""))) & bullet_nums:
                continue  # the weakest entry still supports a number the bullet uses
            cited.pop()
        cited.append(source_id)
        known = numbers(norm(" ".join(text_by_id.get(i, "") for i in cited)))
    return cited