import pytest

from careerlog.jd import clean_jd, ground_requirements

JD = ("We are hiring a data scientist. You will build forecasting models in Python, work with SQL and "
      "Docker, and present dashboards to stakeholders. Experience with LightGBM is a plus.")


def test_clean_jd_collapses_whitespace_and_caps_length():
    assert clean_jd("a  b\n\n" + "word " * 30) .startswith("a b word")
    assert len(clean_jd("word " * 5000)) == 6000


def test_clean_jd_rejects_short_text():
    with pytest.raises(ValueError, match="Paste more"):
        clean_jd("Looking for a data scientist.")


def test_requirements_not_in_the_job_description_are_dropped():
    found = ["forecasting models", "SQL", "Kubernetes", "LightGBM", "sql", "quantum computing", 42]
    assert ground_requirements(found, JD) == ["forecasting models", "SQL", "LightGBM"]


def test_requirements_are_capped_at_six():
    jd = " ".join("skill%d" % i for i in range(10)) + " " * 5 + "x" * 80
    assert len(ground_requirements(["skill%d" % i for i in range(10)], jd)) == 6
