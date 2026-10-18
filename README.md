# Career Log Assistant

A chat app that turns a personal career log into resume bullets. Every bullet carries numbered citations, and the log entries behind them show up as cards beside the chat, each with a match score and an excerpt.

## Run it

From the project root:

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

Then open http://localhost:8501. Run it from the project root so Streamlit finds `.streamlit/config.toml` and the theme applies.

With no log or API key set up, the app uses built-in sample data. The chip under the title says **Sample data**, so a demo never passes sample bullets off as real ones.

## Use your own log

The app switches to the live backend on its own when all three of these are true:

1. `src/careerlog` is importable and `data/log.jsonl` has entries.
2. The search index is built (`python -m careerlog index`).
3. `.env` contains `GROQ_API_KEY` and `GROQ_MODEL`.

The chip then reads **Your log: N entries**. To force a mode, set `CAREERLOG_BACKEND` to `sample` or `live`. In `live` mode the app shows an error instead of silently falling back.

Source cards show a relative label (Strong, Good or Partial match) compared with the best entry in that answer. Hover the label to see the raw cosine similarity, which is usually 0.2 to 0.6 for short entries.

## Add an entry

Open **Add an entry to your log** under the title. Pick a project (or type a new name), set the date, write what you did in plain words, and add optional tags. The entry is saved to `data/log.jsonl` and added to the search index, so the next question can find it. Entries under 25 characters, with `[bracketed]` placeholders, with a future date, or duplicates are rejected with a message. The form is off in sample mode.

## Tailor bullets to a job description

Open **Tailor bullets to a job description** and paste the responsibilities and requirements. The model reduces the text to up to six skills or tools, and any term that is not in the pasted text is dropped. The log is searched for each one, and bullets are written only from the matching entries, with the same citations and checks as normal questions. A skill you have not logged will not appear, so a thin match is a signal to add an entry. The text is sent to the language model, so paste only what you are comfortable sharing.

## Checks on every bullet

Each generated bullet is checked against the entries it cites. If it contains a number, or a risky word such as pipeline, deployed or SQL, that the cited entries do not contain, the bullet is marked "Check before using this bullet" and a summary line appears above the list. Each bullet cites at most three entries, chosen by how much they share with the bullet. These checks catch invented numbers and a fixed list of words. They do not catch every vague overclaim, so read the sources.

## Files

| File | What it does |
|---|---|
| `app/app.py` | The interface: chat, source cards, styling. No retrieval logic. |
| `app/rag_backend.py` | `get_answer(question)` returns an `Answer` (bullets plus sources). Holds the sample data and the adapter to `src/careerlog`. |
| `.streamlit/config.toml` | Light theme, primary color `#4F46E5`. |
| `requirements.txt` | `streamlit` is enough for sample mode. The rest is for the live backend. |

## Plug in a different backend

The UI only needs `get_answer(question) -> Answer` from `rag_backend.py`:

- `Answer.bullets`: a list of `Bullet(text, source_ids)`.
- `Answer.sources`: a list of `Source(id, project, date, text, score)` in citation order. Source 1 is the first one cited.
- `score` is a number from 0 to 1, or `None` when you have no score.

Replace the body of `_live_answer` with your own retrieval and generation and the interface needs no changes.
