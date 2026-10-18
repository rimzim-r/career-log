from datetime import date, timedelta

import pytest

from careerlog.entry import build_entry, parse_tags, slugify

GOOD = "Built a churn dashboard in Streamlit using a weekly CSV export."


def test_slugify():
    assert slugify("Churn Model v2!") == "churn-model-v2"
    assert slugify("  ") == ""


def test_parse_tags_cleans_dedupes_and_limits():
    assert parse_tags("Python, NLP, python, ,Machine Learning") == ["python", "nlp", "machine-learning"]
    assert len(parse_tags(",".join("t%d" % i for i in range(20)))) == 8


def test_good_entry_is_cleaned():
    e = build_entry("Churn Dashboard", date(2026, 10, 1), "  " + GOOD.replace(" ", "   ") + " ", "python, sql")
    assert e.project == "churn-dashboard"
    assert e.text == GOOD
    assert e.tags == ["python", "sql"]
    assert e.source == "manual"


@pytest.mark.parametrize("project,text,day,message", [
    ("", GOOD, date(2026, 10, 1), "project"),
    ("p", "Too short.", date(2026, 10, 1), "at least"),
    ("p", "x" * 1001, date(2026, 10, 1), "under"),
    ("p", "Built the model: [what you did and the result]", date(2026, 10, 1), "placeholder"),
    ("p", GOOD, date.today() + timedelta(days=1), "future"),
])
def test_bad_input_raises_a_readable_error(project, text, day, message):
    with pytest.raises(ValueError, match=message):
        build_entry(project, day, text)
