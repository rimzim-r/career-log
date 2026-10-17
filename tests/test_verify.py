from careerlog.verify import check_bullet, tighten_citations


def test_clean_bullet_has_no_issues():
    src = ["Built a Hinglish sentiment classifier; TF-IDF reached macro F1 0.699 on 319 comments."]
    assert check_bullet("Built a sentiment classifier reaching macro F1 0.699 on 319 comments.", src) == []


def test_number_not_in_source_is_flagged():
    src = ["Built a classifier that reached macro F1 0.699."]
    issues = check_bullet("Built a classifier that reached macro F1 0.85.", src)
    assert any("0.85" in i for i in issues)


def test_risky_word_not_in_source_is_flagged():
    src = ["Built the Cloud Cover Detective image analytics case study."]
    issues = check_bullet("Developed an image analytics pipeline.", src)
    assert any("pipeline" in i for i in issues)


def test_no_citation_is_flagged():
    assert check_bullet("Built something.", []) == ["it cites no log entry"]


def test_tighten_drops_unrelated_entry_and_keeps_related_ones():
    texts = {
        "a": "Built day-ahead electricity load forecasts with LightGBM, LSTM and SARIMA.",
        "b": "Found my first LightGBM used fewer recent inputs than the LSTM and looked 25% worse.",
        "c": "Ensemble of LightGBM and LSTM reached MAE 1,467 MW on the test period.",
    }
    bullet = "Built day-ahead electricity load forecasts with LightGBM and LSTM, reaching MAE 1,467 MW."
    assert tighten_citations(bullet, ["a", "b", "c"], texts) == ["a", "c"]


def test_tighten_keeps_original_when_nothing_matches():
    assert tighten_citations("Wrote code.", ["a"], {"a": "Something else entirely."}) == ["a"]


def test_citations_are_capped_at_three_best_entries():
    texts = {
        "a": "Built day-ahead electricity load forecasts with LightGBM and LSTM models.",
        "b": "Built day-ahead electricity load forecasts evaluated on a strict time split.",
        "c": "Electricity load forecasts used LightGBM and LSTM with day-ahead targets.",
        "d": "Day-ahead electricity load forecasts compared LightGBM, LSTM and SARIMA.",
    }
    bullet = "Built day-ahead electricity load forecasts with LightGBM and LSTM."
    assert len(tighten_citations(bullet, ["a", "b", "c", "d"], texts)) == 3
