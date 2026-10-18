import sys
import types
from datetime import date

from careerlog import generate
from careerlog.schema import LogEntry


def _entries():
    return [
        LogEntry(id="e1", date=date(2026, 10, 9), project="cloud-cover-detective",
                 text="Built the Cloud Cover Detective image analytics case study to detect clouds and shadows in satellite images."),
        LogEntry(id="e2", date=date(2026, 10, 13), project="load-forecasting",
                 text="Ensemble of LightGBM and LSTM reached MAE 1,467 MW and MAPE 4.40% on the test period."),
    ]


def _setup(monkeypatch, model_output):
    entries = _entries()
    hits = [{"id": e.id, "project": e.project, "text": e.text, "distance": 1.0} for e in entries]
    monkeypatch.setitem(sys.modules, "careerlog.index", types.SimpleNamespace(search=lambda q, k=8: hits))
    monkeypatch.setattr(generate, "load_entries", lambda: entries)
    monkeypatch.setattr(generate, "_call_model", lambda system, user: model_output)


def test_invented_word_and_number_are_flagged(monkeypatch):
    _setup(monkeypatch, {"bullets": [
        {"text": "Developed an image analytics pipeline to detect clouds and shadows in satellite images.",
         "source_ids": ["e1"]},
        {"text": "Built an ensemble of LightGBM and LSTM reaching MAPE 3.10%.", "source_ids": ["e2"]},
    ]})
    bullets, _ = generate.generate_bullets("machine learning")
    assert any("pipeline" in i for i in bullets[0]["issues"])
    assert any("3.10" in i for i in bullets[1]["issues"])


def test_faithful_bullet_has_no_issues(monkeypatch):
    _setup(monkeypatch, {"bullets": [
        {"text": "Built an ensemble of LightGBM and LSTM reaching MAE 1,467 MW and MAPE 4.40% on the test period.",
         "source_ids": ["e2"]},
    ]})
    bullets, _ = generate.generate_bullets("forecasting")
    assert bullets[0]["issues"] == [] and bullets[0]["supported"]


def test_unknown_ids_are_dropped_and_extra_citations_are_trimmed(monkeypatch):
    _setup(monkeypatch, {"bullets": [
        {"text": "Built an ensemble of LightGBM and LSTM reaching MAE 1,467 MW and MAPE 4.40% on the test period.",
         "source_ids": ["e1", "e2", "ghost"]},
    ]})
    bullets, _ = generate.generate_bullets("forecasting")
    assert bullets[0]["source_ids"] == ["e2"]


def test_job_mode_keeps_only_requirements_found_in_the_jd_and_checks_bullets(monkeypatch):
    entries = _entries()
    searched = []

    def fake_search(query, k=8):
        searched.append(query)
        return [{"id": e.id, "project": e.project, "text": e.text, "distance": 1.0 + i * 0.2}
                for i, e in enumerate(entries)]

    def fake_model(system, user):
        if system == generate.EXTRACT_PROMPT:
            return {"requirements": ["LightGBM", "Kubernetes", "satellite images"]}
        return {"bullets": [{"text": "Built an ensemble of LightGBM and LSTM reaching MAPE 4.40% on the test period.",
                             "source_ids": ["e2"]}]}

    monkeypatch.setitem(sys.modules, "careerlog.index", types.SimpleNamespace(search=fake_search))
    monkeypatch.setattr(generate, "load_entries", lambda: entries)
    monkeypatch.setattr(generate, "_call_model", fake_model)

    jd = ("We need someone who has used LightGBM for forecasting and can detect clouds in satellite images. "
          "You will present results to the product team every week.")
    out = generate.generate_for_job(jd)
    assert out["requirements"] == ["LightGBM", "satellite images"]  # Kubernetes is not in the job description
    assert searched == ["LightGBM", "satellite images"]
    assert out["bullets"][0]["issues"] == []
    assert set(out["distance"]) == {"e1", "e2"}


def test_job_mode_with_no_usable_requirements_raises(monkeypatch):
    monkeypatch.setattr(generate, "_call_model", lambda system, user: {"requirements": ["Kubernetes"]})
    jd = "We want a friendly teammate who enjoys working with others and learning new things every single day."
    import pytest
    with pytest.raises(ValueError, match="specific skills"):
        generate.generate_for_job(jd)
