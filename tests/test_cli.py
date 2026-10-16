import sys

from careerlog.cli import main
from careerlog.store import load_entries


def run_cli(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["careerlog", *args])
    main()


def test_add_and_load(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # CLI writes to data/log.jsonl, so use a temp folder
    run_cli(monkeypatch, "add", "Built a model", "--tags", "ml,python", "--date", "2026-10-01")
    entries = load_entries()
    assert len(entries) == 1
    assert entries[0].tags == ["ml", "python"]


def test_import_skips_comments_and_blank_lines(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "seed.txt").write_text(
        "# a comment\n"
        "\n"
        "2026-10-01 | python,ml | First entry\n"
        "2026-10-02 | sql | Second entry | with a pipe in the text\n",
        encoding="utf-8",
    )
    run_cli(monkeypatch, "import", "seed.txt")
    entries = load_entries()
    assert len(entries) == 2
    assert entries[1].text == "Second entry | with a pipe in the text"