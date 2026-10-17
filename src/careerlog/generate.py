import json
import os

from dotenv import load_dotenv
from groq import Groq

from .index import search
from .store import load_entries

load_dotenv()

SYSTEM_PROMPT = """You write resume bullets from a personal career log.

Each log entry shows its id in [brackets] and its project in <angle brackets>.

Rules:
- Use ONLY facts stated in the log entries. Never add numbers, tools, metrics, or outcomes that are not in the entries.
- Do not use words like deployed, production, scaled, launched, or improved unless an entry says so. Use the entry's own verbs when unsure (built, evaluated, compared).
- Write exactly ONE bullet per project, and only for projects that fit the request. Combine the project's entries into that one bullet and cite every id you used.
- Lead each bullet with the project's strongest concrete result and copy its numbers exactly as written.
- If an entry states a caveat about a headline number (for example a small test set or a favourable split), keep a short version of that caveat in the bullet.
- Each bullet starts with a strong past-tense verb, is a single line under 40 words, and has no first-person words.
- Order bullets from most to least relevant to the request. Write at most 5 bullets.
- If the entries do not support a good bullet for the request, return fewer bullets or none.

Return only JSON in this shape:
{"bullets": [{"text": "...", "source_ids": ["id1", "id2"]}]}"""


def generate_bullets(request: str, k: int = 8):
    """Find matching projects, then write one cited bullet per project."""
    hits = search(request, k=k)
    hit_ids = {h["id"] for h in hits}

    rank = {}
    for i, h in enumerate(hits):
        if h.get("project"):
            rank.setdefault(h["project"], i)

    entries = [
        e for e in load_entries()
        if e.id in hit_ids or (e.project and e.project in rank)
    ]
    entries.sort(key=lambda e: (rank.get(e.project, 999), e.project or "", str(e.date)))

    rows = []
    for e in entries:
        rows.append(
            "[" + e.id + "] <" + (e.project or "no-project") + "> ("
            + str(e.date) + ") " + e.text
        )
    context = "\n".join(rows)

    client = Groq()
    resp = client.chat.completions.create(
        model=os.environ["GROQ_MODEL"],
        temperature=0.2,
        max_tokens=2000,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Request: " + request + "\n\nLog entries:\n" + context,
            },
        ],
    )
    data = json.loads(resp.choices[0].message.content)

    valid_ids = {e.id for e in entries}
    bullets = []
    for b in data.get("bullets", []):
        ids = [i for i in b.get("source_ids", []) if i in valid_ids]
        bullets.append({
            "text": b["text"],
            "source_ids": ids,
            "supported": bool(ids),
        })

    used = [{"id": e.id, "text": e.text, "project": e.project} for e in entries]
    return bullets, used
