"""Career Log Assistant: a chat UI for asking questions about a career log.

Run from the project root:   streamlit run app/app.py

This file only draws the interface. Retrieval and generation live in
rag_backend.py, which returns an Answer (bullets, plus the sources behind them).
"""
from __future__ import annotations

import html

import streamlit as st

from rag_backend import Answer, backend_label, get_answer

st.set_page_config(page_title="Career Log Assistant", page_icon="🗂️", layout="wide")

ACRONYMS = {"ott": "OTT", "sql": "SQL", "nlp": "NLP", "ml": "ML", "ai": "AI", "etl": "ETL"}

SUGGESTIONS = [
    "What are my strongest machine learning projects for a resume?",
    "Which projects show I can work with SQL?",
    "Write bullets about dashboards and analytics",
    "Do I have any Kubernetes experience?",
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&display=swap');

:root {
  --brand: #4F46E5;
  --brand-soft: #EEF0FF;
  --brand-line: #DADDFF;
  --ink: #1B1B2F;
  --body: #3B3D54;
  --muted: #686C84;
  --line: #E6E8F2;
  --surface: #FFFFFF;
  --bg: #F6F7FB;
}

.stApp, .stApp .stMarkdown, .stApp .stMarkdown p, .stApp .stMarkdown li,
.stApp textarea, .stApp button p, .stApp summary {
  font-family: 'Figtree', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.stApp { background: var(--bg); color: var(--ink); }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppDeployButton"], .stAppDeployButton, .stDeployButton { display: none; }
footer, #MainMenu { visibility: hidden; }
.block-container { max-width: 1180px; padding-top: 2.4rem; padding-bottom: 8rem; }

/* Header */
.hero-title { font-size: 1.95rem; font-weight: 700; letter-spacing: -0.02em; color: var(--ink); line-height: 1.15; }
.hero-sub { margin-top: .4rem; color: var(--muted); font-size: 1.02rem; max-width: 40rem; line-height: 1.5; }
.chip { display: inline-block; margin-top: .9rem; padding: .22rem .7rem; border-radius: 999px;
        border: 1px solid var(--line); background: var(--surface); color: var(--muted);
        font-size: .8rem; font-weight: 500; }
.chip.live { background: var(--brand-soft); border-color: var(--brand-line); color: var(--brand); }

/* Messages */
[data-testid="stChatMessage"] {
  background: var(--surface); border: 1px solid var(--line); border-radius: 16px;
  padding: 1rem 1.15rem; margin-bottom: .9rem;
  box-shadow: 0 1px 2px rgba(27, 27, 47, .04);
}
[data-testid="stChatMessage"] p { line-height: 1.6; color: var(--body); }
.user-msg { display: flex; gap: .8rem; align-items: baseline; background: var(--brand-soft);
            border: 1px solid var(--brand-line); border-radius: 16px; padding: .85rem 1.15rem;
            margin-bottom: .9rem; color: var(--ink); line-height: 1.55; }
.user-msg .who { flex: none; font-weight: 600; font-size: .85rem; color: var(--brand); }

/* Resume bullets, citation badges and check warnings */
ul.bullets { list-style: none; margin: .6rem 0 .2rem; padding: 0; display: flex; flex-direction: column; gap: .85rem; }
ul.bullets li { position: relative; padding-left: 1.2rem; line-height: 1.6; color: var(--ink); font-size: 1rem; }
ul.bullets li::before { content: ""; position: absolute; left: .1rem; top: .66em; width: 6px; height: 6px;
                        border-radius: 50%; background: var(--brand); }
.cite { display: inline-block; min-width: 1.2rem; padding: 0 .35rem; margin-left: .3rem; border-radius: 999px;
        background: var(--brand-soft); color: var(--brand); font-size: .72rem; font-weight: 600;
        line-height: 1.25rem; text-align: center; vertical-align: .08em; }
.flag { margin-top: .4rem; padding: .4rem .7rem; border-radius: 8px; background: #FEF6E0; color: #7A4B00;
        border: 1px solid #F5E1A4; font-size: .85rem; line-height: 1.45; }
.flag strong { font-weight: 650; }
.flag-summary { margin: .5rem 0 .2rem; }

/* Welcome card */
.welcome { background: var(--surface); border: 1px solid var(--line); border-radius: 16px;
           padding: 1.3rem 1.4rem; margin-bottom: 1rem; box-shadow: 0 1px 2px rgba(27, 27, 47, .04); }
.welcome-title { font-weight: 650; font-size: 1.12rem; color: var(--ink); }
.welcome p { margin: .35rem 0 0; color: var(--muted); line-height: 1.55; }

/* Buttons */
.stButton > button { border-radius: 12px; border: 1px solid var(--line); background: var(--surface);
                     color: var(--ink); font-weight: 500; justify-content: flex-start; text-align: left;
                     padding: .6rem .9rem; transition: border-color .15s, color .15s; }
.stButton > button:hover { border-color: var(--brand); color: var(--brand); }
.stButton > button:focus-visible { outline: 2px solid var(--brand); outline-offset: 2px; }

/* Sources panel */
.st-key-sources { position: sticky; top: 4rem; max-height: calc(100vh - 11rem); overflow-y: auto; padding-right: .2rem; }
.panel-title { display: flex; align-items: center; gap: .5rem; font-weight: 650; font-size: 1.05rem;
               color: var(--ink); margin-bottom: .8rem; }
.panel-count { padding: 0 .5rem; border-radius: 999px; background: var(--brand-soft); color: var(--brand);
               font-size: .76rem; font-weight: 600; line-height: 1.35rem; }
.src { background: var(--surface); border: 1px solid var(--line); border-radius: 14px;
       padding: .95rem 1rem; margin-bottom: .85rem;
       box-shadow: 0 1px 2px rgba(27, 27, 47, .04), 0 10px 22px -14px rgba(27, 27, 47, .22); }
.src-head { display: flex; align-items: center; gap: .6rem; }
.src-num { flex: none; width: 1.4rem; height: 1.4rem; border-radius: 50%; background: var(--brand); color: #fff;
           font-size: .74rem; font-weight: 600; display: grid; place-items: center; }
.src-title { font-weight: 600; font-size: .95rem; color: var(--ink); line-height: 1.25; }
.src-date { margin-left: auto; padding-left: .5rem; color: var(--muted); font-size: .78rem; white-space: nowrap; }
.meter { height: 5px; background: #ECEEF8; border-radius: 99px; overflow: hidden; margin: .7rem 0 .25rem; }
.meter > span { display: block; height: 100%; background: var(--brand); border-radius: 99px; }
.src-score { font-size: .78rem; color: var(--muted); margin-top: .55rem; }
.meter + .src-score { margin-top: 0; }
.src-snip { margin-top: .55rem; font-size: .88rem; color: var(--body); line-height: 1.5; }
details.full { margin-top: .5rem; }
details.full summary { cursor: pointer; font-size: .8rem; font-weight: 500; color: var(--brand); }
details.full p { margin: .4rem 0 0; font-size: .86rem; color: var(--body); line-height: 1.5; }
.src-empty { border: 1px dashed #CBCEE3; border-radius: 14px; padding: 1.1rem 1.1rem; color: var(--muted);
             font-size: .92rem; line-height: 1.55; background: rgba(255, 255, 255, .6); }

/* Chat input and footer */
[data-testid="stChatInput"] { border-radius: 14px; border: 1px solid var(--line);
                              box-shadow: 0 6px 24px -12px rgba(27, 27, 47, .25); }
[data-testid="stChatInput"]:focus-within { border-color: var(--brand); }
.foot { margin-top: 1.6rem; color: var(--muted); font-size: .82rem; line-height: 1.5; }

@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
"""


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def pretty(project: str | None) -> str:
    words = (project or "other").replace("_", "-").split("-")
    return " ".join(ACRONYMS.get(w.lower(), w.capitalize()) for w in words if w)


def bullets_html(answer: Answer) -> str:
    number = {s.id: i for i, s in enumerate(answer.sources, start=1)}
    items = []
    for b in answer.bullets:
        cites = "".join('<span class="cite">%d</span>' % number[i] for i in b.source_ids if i in number)
        warning = ""
        if b.issues:
            warning = ('<div class="flag"><strong>Check before using this bullet:</strong> %s.</div>'
                       % esc("; ".join(b.issues)))
        items.append("<li>" + esc(b.text) + cites + warning + "</li>")
    return '<ul class="bullets">' + "".join(items) + "</ul>"


def match_label(score: float, best: float) -> tuple[str, int]:
    """Label a score relative to the best one in this answer, and give a bar width."""
    ratio = score / best if best > 0 else 0
    if ratio >= 0.9:
        return "Strong match", 100 if ratio >= 0.99 else round(ratio * 100)
    if ratio >= 0.7:
        return "Good match", round(ratio * 100)
    return "Partial match", max(round(ratio * 100), 8)


def source_card_html(n: int, s, best: float) -> str:
    if s.score is None:
        score = '<div class="src-score">%s</div>' % esc(s.note or "Included with the matching project")
    else:
        label, width = match_label(s.score, best)
        score = ('<div class="meter"><span style="width:%d%%"></span></div>'
                 '<div class="src-score" title="Cosine similarity %.2f">%s</div>'
                 % (width, s.score, esc(label)))
    short = s.text if len(s.text) <= 150 else s.text[:147].rstrip() + "…"
    full = ""
    if len(s.text) > 150:
        full = '<details class="full"><summary>Show full entry</summary><p>%s</p></details>' % esc(s.text)
    day = '<span class="src-date">%s</span>' % esc(s.date) if s.date else ""
    return (
        '<div class="src">'
        '<div class="src-head"><span class="src-num">%d</span>'
        '<span class="src-title">%s</span>%s</div>'
        '%s<div class="src-snip">%s</div>%s</div>'
    ) % (n, esc(pretty(s.project)), day, score, esc(short), full)


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def render_answer(answer: Answer) -> None:
    st.markdown(answer.intro)
    if not answer.bullets:
        return
    flagged = sum(1 for b in answer.bullets if b.issues)
    if flagged:
        st.markdown(
            '<div class="flag flag-summary"><strong>%d of %d bullets need a check.</strong> '
            'They contain a number or word that the cited entries do not contain. '
            'Each one is marked below.</div>' % (flagged, len(answer.bullets)),
            unsafe_allow_html=True,
        )
    st.markdown(bullets_html(answer), unsafe_allow_html=True)
    with st.expander("Copy as plain text"):
        text = "\n".join("- " + b.text for b in answer.bullets)
        try:
            st.code(text, language=None, wrap_lines=True)
        except TypeError:  # older Streamlit without wrap_lines
            st.code(text, language=None)


def render_assistant(entry: dict) -> None:
    if entry.get("error"):
        st.error(entry["error"])
    else:
        render_answer(entry["answer"])


def render_message(entry: dict) -> None:
    if entry["role"] == "user":
        st.markdown('<div class="user-msg"><span class="who">You</span><span>%s</span></div>'
                    % esc(entry["text"]), unsafe_allow_html=True)
    else:
        with st.chat_message("assistant", avatar=":material/auto_stories:"):
            render_assistant(entry)


def render_sources(entry: dict | None) -> None:
    answer = entry.get("answer") if entry else None
    if answer is None or not answer.sources:
        st.markdown('<div class="panel-title">Sources</div>', unsafe_allow_html=True)
        text = ("No log entries matched, so there is nothing to cite." if entry
                else "Ask a question and the log entries behind each bullet appear here, "
                     "with a match label and a short excerpt.")
        st.markdown('<div class="src-empty">%s</div>' % esc(text), unsafe_allow_html=True)
        return
    scored = [s.score for s in answer.sources if s.score is not None]
    best = max(scored) if scored else 0.0
    st.markdown('<div class="panel-title">Sources<span class="panel-count">%d</span></div>'
                % len(answer.sources), unsafe_allow_html=True)
    cards = "".join(source_card_html(i, s, best) for i, s in enumerate(answer.sources, start=1))
    st.markdown(cards, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
st.markdown(CSS, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

label, is_live = backend_label()
head_left, head_right = st.columns([5, 1])
with head_left:
    st.markdown(
        '<div class="hero-title">Career Log Assistant</div>'
        '<div class="hero-sub">Ask about your work and get resume bullets that point back to the '
        'log entries behind them.</div>'
        '<span class="chip%s">%s</span>' % (" live" if is_live else "", esc(label)),
        unsafe_allow_html=True,
    )
with head_right:
    if st.session_state.messages and st.button("New chat", key="new_chat"):
        st.session_state.messages = []
        st.rerun()

# Called at the top level so Streamlit pins the input to the bottom of the page.
question = st.chat_input("Ask about your projects, skills or results") or st.session_state.pop("pending", None)

st.write("")
left, right = st.columns([1.75, 1], gap="large")

with left:
    for entry in st.session_state.messages:
        render_message(entry)

    if not st.session_state.messages and not question:
        st.markdown(
            '<div class="welcome"><div class="welcome-title">Ask your career log</div>'
            '<p>Describe a role, skill or topic. You get resume bullets built only from your own '
            'entries, each numbered to the sources behind it.</p></div>',
            unsafe_allow_html=True,
        )
        for i, text in enumerate(SUGGESTIONS):
            if st.button(text, key="suggestion_%d" % i, use_container_width=True):
                st.session_state.pending = text
                st.rerun()

    if question:
        user_entry = {"role": "user", "text": question}
        st.session_state.messages.append(user_entry)
        render_message(user_entry)

        with st.chat_message("assistant", avatar=":material/auto_stories:"):
            with st.spinner("Searching your log and writing bullets…"):
                try:
                    reply = {"role": "assistant", "answer": get_answer(question)}
                except Exception as exc:
                    reply = {
                        "role": "assistant",
                        "answer": None,
                        "error": "Something went wrong while writing bullets: " + str(exc)[:240] +
                                 " Try rephrasing the question. If it keeps failing, check your API key and rate limit.",
                    }
            render_assistant(reply)
        st.session_state.messages.append(reply)

with right:
    with st.container(key="sources"):
        last = st.session_state.messages[-1] if st.session_state.messages else None
        render_sources(last if last and last["role"] == "assistant" else None)

st.markdown(
    '<div class="foot">Responses are generated from your career log. '
    'Check each bullet against its sources before you use it.</div>',
    unsafe_allow_html=True,
)
