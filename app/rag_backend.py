"""Retrieval and generation behind the Career Log Assistant UI.

The UI (app.py) only calls get_answer() and backend_label(). Everything else in
this file can change without touching the UI.

Two backends:
  sample  Built-in sample career log and canned bullets. Needs nothing but Streamlit.
  live    Your real pipeline in src/careerlog (Chroma search + LLM bullets + checks).

Choose with the CAREERLOG_BACKEND environment variable: "auto" (default),
"sample" or "live". Auto uses live when the careerlog package imports, the log
has entries and GROQ_API_KEY is set; otherwise it falls back to sample.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# Data shapes the UI relies on
# --------------------------------------------------------------------------
@dataclass
class Source:
    id: str
    project: str
    date: str
    text: str
    score: float | None  # cosine similarity from 0 to 1, or None when not scored
    note: str = ""       # shown instead of a match label when score is None


@dataclass
class Bullet:
    text: str
    source_ids: list[str]
    issues: list[str] = field(default_factory=list)  # reasons to double-check this bullet


@dataclass
class Answer:
    intro: str
    bullets: list[Bullet]
    sources: list[Source]  # in citation order: source 1 is the first one cited
    mode: str  # "sample" or "live"


NO_MATCH = ("Your log has nothing that directly matches this, so no bullets were written. "
            "Try naming a project, tool or skill you have used.")


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def get_answer(question: str) -> Answer:
    """Return bullets and the sources behind them for one question."""
    mode = os.environ.get("CAREERLOG_BACKEND", "auto").lower()
    if mode == "sample":
        return _sample_answer(question)
    ok, _count, reason = _live_status()
    if ok:
        return _live_answer(question)
    if mode == "live":
        raise RuntimeError("Live backend unavailable: " + reason)
    return _sample_answer(question)


def backend_label() -> tuple[str, bool]:
    """Text for the header chip, and whether it is the live backend."""
    mode = os.environ.get("CAREERLOG_BACKEND", "auto").lower()
    if mode != "sample":
        ok, count, _reason = _live_status()
        if ok:
            return "Your log: " + str(count) + " entries", True
    return "Sample data", False


# --------------------------------------------------------------------------
# Sample backend (mock retrieval and generation)
# --------------------------------------------------------------------------
# (id, project, date, text)
_SAMPLE_LOG = [
    ("s01", "retail-demand-forecasting", "2026-03-12",
     "Built weekly demand forecasts for 120 product lines with LightGBM and a seasonal-naive baseline."),
    ("s02", "retail-demand-forecasting", "2026-03-26",
     "Cut forecast error (MAPE) from 18.4% to 12.1% on a held-out quarter by adding promotion and holiday features."),
    ("s03", "support-ticket-classifier", "2026-02-04",
     "Fine-tuned a DistilBERT model to route support tickets into 9 categories using 14,000 labelled tickets."),
    ("s04", "support-ticket-classifier", "2026-02-18",
     "Reached macro F1 of 0.81 on a held-out month; most errors were between billing and refunds."),
    ("s05", "churn-dashboard", "2026-01-15",
     "Built a Streamlit dashboard tracking customer churn by plan and region, refreshed from a weekly CSV export."),
    ("s06", "churn-dashboard", "2026-01-29",
     "Presented the findings to the product team, who used them to change the onboarding email sequence."),
    ("s07", "sql-reporting-automation", "2025-11-10",
     "Replaced a manual weekly sales report with a scheduled SQL job and a Python script that emails a summary."),
    ("s08", "sql-reporting-automation", "2025-11-24",
     "Report preparation dropped from about three hours to ten minutes a week."),
]

_SAMPLE_PROJECTS = {
    "retail-demand-forecasting": {
        "keywords": "forecasting forecast time series machine learning model lightgbm demand",
        "ids": ["s01", "s02"],
        "bullet": "Built weekly demand forecasts for 120 product lines with LightGBM, cutting MAPE from "
                  "18.4% to 12.1% against a seasonal-naive baseline on a held-out quarter.",
    },
    "support-ticket-classifier": {
        "keywords": "nlp text classification machine learning deep learning model distilbert tickets",
        "ids": ["s03", "s04"],
        "bullet": "Fine-tuned DistilBERT to route support tickets into 9 categories, reaching macro F1 "
                  "0.81 on a held-out month; most errors were between billing and refunds.",
    },
    "churn-dashboard": {
        "keywords": "dashboard streamlit analytics visualization churn presentation stakeholders",
        "ids": ["s05", "s06"],
        "bullet": "Built a Streamlit churn dashboard by plan and region and presented the findings to the "
                  "product team, who used them to revise the onboarding emails.",
    },
    "sql-reporting-automation": {
        "keywords": "sql automation reporting python reports etl scheduling",
        "ids": ["s07", "s08"],
        "bullet": "Automated the weekly sales report with a scheduled SQL job and a Python email script, "
                  "reducing preparation from about three hours to ten minutes.",
    },
}

_FILLER = set(
    "what are my the for a an of in on and to with me show tell about give which is i have do did "
    "used using work worked experience write any can you your from that this".split()
)
_GENERIC = {"strongest", "best", "top", "highlight", "resume", "project", "projects", "bullets", "bullet"}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9+#]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in _FILLER}


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 4 and word.endswith("s") else word


def _sample_answer(question: str) -> Answer:
    topic = {_stem(w) for w in _tokens(question) if w not in _GENERIC}

    ranked = []
    for name, info in _SAMPLE_PROJECTS.items():
        words = {_stem(w) for w in _tokens(info["keywords"])}
        ranked.append((len(topic & words), name))

    if not topic:
        chosen = [(1, name) for _o, name in ranked][:3]
    else:
        chosen = sorted([r for r in ranked if r[0] > 0], key=lambda r: -r[0])[:3]

    if not chosen:
        return Answer(intro=NO_MATCH, bullets=[], sources=[], mode="sample")

    entries = {e[0]: e for e in _SAMPLE_LOG}
    bullets: list[Bullet] = []
    sources: list[Source] = []
    for overlap, name in chosen:
        info = _SAMPLE_PROJECTS[name]
        bullets.append(Bullet(info["bullet"], list(info["ids"])))
        for i, sid in enumerate(info["ids"]):
            _id, project, day, text = entries[sid]
            score = min(0.95, 0.42 + 0.17 * overlap - 0.06 * i)  # mock score
            sources.append(Source(sid, project, day, text, score))

    return Answer(
        intro="Here are the closest matches in your log. Each number points to the entries behind the bullet.",
        bullets=bullets, sources=sources, mode="sample",
    )


# --------------------------------------------------------------------------
# Live backend (your real pipeline in src/careerlog)
# --------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _prepare() -> None:
    """Load .env, make src/ importable, and run from the project root.

    careerlog reads data/log.jsonl and chroma_db relative to the working directory.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    os.chdir(ROOT)


@lru_cache(maxsize=1)
def _live_status() -> tuple[bool, int, str]:
    """Returns (available, number of log entries, reason if unavailable)."""
    _prepare()

    try:
        from careerlog.store import load_entries

        count = len(load_entries())
    except Exception as exc:  # missing package, bad log file, missing dependency
        return False, 0, "careerlog could not be loaded (" + str(exc)[:80] + ")"
    if count == 0:
        return False, 0, "data/log.jsonl is empty"
    if not os.environ.get("GROQ_API_KEY"):
        return False, count, "GROQ_API_KEY is not set in .env"
    return True, count, ""


def _live_answer(question: str, k: int = 8) -> Answer:
    from careerlog.generate import generate_bullets
    from careerlog.index import search
    from careerlog.store import load_entries

    entries = {e.id: e for e in load_entries()}
    # Chroma returns squared L2 distance on normalised vectors, so cosine = 1 - d / 2.
    scores = {h["id"]: max(0.0, min(1.0, 1 - h["distance"] / 2)) for h in search(question, k=k)}
    raw, _used = generate_bullets(question, k=k)

    bullets: list[Bullet] = []
    sources: list[Source] = []
    seen: set[str] = set()
    for b in raw:
        ids = [i for i in b["source_ids"] if i in entries]
        if not ids:
            continue  # never show a bullet that cites nothing
        bullets.append(Bullet(b["text"], ids, list(b.get("issues", []))))
        for sid in ids:
            if sid not in seen:
                seen.add(sid)
                e = entries[sid]
                sources.append(Source(sid, e.project or "other", str(e.date), e.text,
                                      scores.get(sid), "Included from a matching project"))

    if not bullets:
        return Answer(intro=NO_MATCH, bullets=[], sources=[], mode="live")
    return Answer(
        intro="Here are bullets written only from your log. Each number points to the entries behind the bullet.",
        bullets=bullets, sources=sources, mode="live",
    )


# --------------------------------------------------------------------------
# Adding entries (used by the "Add an entry" form)
# --------------------------------------------------------------------------
def can_add_entries() -> tuple[bool, str]:
    """Whether the form can write to the real log, and why not if it cannot."""
    if os.environ.get("CAREERLOG_BACKEND", "auto").lower() == "sample":
        return False, "Sample mode is on, so adding entries is switched off."
    _prepare()
    try:
        import careerlog.store  # noqa: F401
    except Exception as exc:
        return False, "The careerlog package could not be loaded (" + str(exc)[:80] + ")."
    return True, ""


def existing_projects() -> list[str]:
    """Project names in the log, most recently used first."""
    if not can_add_entries()[0]:
        return []
    from careerlog.store import load_entries

    latest: dict[str, str] = {}
    for e in load_entries():
        if e.project:
            latest[e.project] = max(latest.get(e.project, ""), str(e.date))
    return sorted(latest, key=lambda name: latest[name], reverse=True)


def add_log_entry(project: str, day, text: str, tags_raw: str = "") -> str:
    """Add one entry to the log and the search index.

    Returns a short success message. Raises ValueError with a message for the user.
    """
    ok, reason = can_add_entries()
    if not ok:
        raise ValueError(reason)
    from careerlog.entry import build_entry
    from careerlog.store import add_entry, load_entries

    entry = build_entry(project, day, text, tags_raw)
    if any(e.project == entry.project and e.text == entry.text for e in load_entries()):
        raise ValueError("That entry is already in your log.")
    add_entry(entry)

    note = ""
    try:
        from careerlog.index import build_index

        build_index([entry])
    except Exception as exc:
        note = (" It was saved, but the search index was not updated (" + str(exc)[:60]
                + "). Run: python -m careerlog index")
    _live_status.cache_clear()  # so the header count and live mode refresh
    return "Added to " + entry.project + "." + note
