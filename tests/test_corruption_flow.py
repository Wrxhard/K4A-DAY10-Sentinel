from pathlib import Path
from types import SimpleNamespace

import pandas as pd

import pipelines.corruption_flow as flow


def _settings(tmp_path: Path):
    data = tmp_path / "data"
    clean = data / "clean"
    results = data / "results"
    quality = data / "quality"
    reports = data / "reports"
    for directory in (clean, results, quality, reports, data / "raw", data / "embeddings"):
        directory.mkdir(parents=True, exist_ok=True)

    paths = SimpleNamespace(
        clean_json=clean / "papers_clean.json",
        corrupted_clean_csv=clean / "papers_clean_corrupted.csv",
        corrupted_clean_json=clean / "papers_clean_corrupted.json",
        repaired_clean_csv=clean / "papers_clean_repaired.csv",
        repaired_clean_json=clean / "papers_clean_repaired.json",
        raw_records_json=data / "raw" / "crossref_records.json",
        corruption_log=results / "corruption_log.json",
        corrupted_quality_report=quality / "corrupted_quality_report.json",
        repaired_metrics=results / "repaired_metrics.json",
        corrupted_metrics=results / "corrupted_metrics.json",
        baseline_metrics=results / "baseline_metrics.json",
        corrupted_answers=results / "corrupted_answers.json",
        repaired_answers=results / "repaired_answers.json",
        corrupted_embeddings_json=data / "embeddings" / "corrupted.json",
        repaired_embeddings_json=data / "embeddings" / "repaired.json",
        eval_testset=data / "eval_testset.json",
        comparison_report=reports / "corruption_report.md",
        quality_dir=quality,
    )
    return SimpleNamespace(paths=paths)


def _frame():
    return pd.DataFrame(
        {
            "paper_id": ["p1", "p2"],
            "title": ["Title 1", "Title 2"],
            "summary": ["A sufficiently long summary for test data."] * 2,
            "published": ["2026-01-02", "2026-01-01"],
            "authors_joined": ["A", "B"],
            "categories_joined": ["AI", "AI"],
            "text_for_embedding": ["text 1", "text 2"],
            "age_days": [1, 2],
            "summary_chars": [40, 40],
        }
    )


def test_main_runs_corruption_repair_and_comparison_flow(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    clean = _frame()
    clean.to_json(settings.paths.clean_json, orient="records")
    settings.paths.raw_records_json.write_text("[]", encoding="utf-8")
    settings.paths.baseline_metrics.write_text('{"retrieval_hit_rate": 1.0}', encoding="utf-8")
    settings.paths.eval_testset.write_text("[]", encoding="utf-8")

    calls = []

    class FakeIndex:
        @classmethod
        def build(cls, dataframe, current_settings, output_path):
            calls.append(("build", output_path.name, len(dataframe)))
            return cls()

    def fake_corrupt(dataframe, output_path):
        calls.append(("corrupt", output_path.name))
        dataframe.to_json(output_path, orient="records")
        return dataframe.copy()

    def fake_quality(dataframe, current_settings, name):
        calls.append(("quality", name, len(dataframe)))
        return {"success": name == "repaired"}

    def fake_freshness(dataframe, current_settings, path):
        calls.append(("freshness", path.name))
        return {"is_fresh": True}

    def fake_evaluate(current_settings, index, test_path, metrics_path, answers_path):
        calls.append(("evaluate", metrics_path.name))
        metrics_path.write_text('{"retrieval_hit_rate": 0.5}', encoding="utf-8")
        answers_path.write_text("[]", encoding="utf-8")

    def fake_report(path, baseline, corrupted, repaired, corrupted_quality, repaired_quality, corrupted_freshness, repaired_freshness):
        calls.append(("report", path.name))
        path.write_text("| Baseline | Corrupted | Repaired |", encoding="utf-8")

    monkeypatch.setattr(flow, "load_settings", lambda: settings, raising=False)
    monkeypatch.setattr(flow, "read_json", lambda path: __import__("json").loads(path.read_text(encoding="utf-8")), raising=False)
    monkeypatch.setattr(flow, "corrupt_clean_dataframe", fake_corrupt, raising=False)
    monkeypatch.setattr(flow, "load_raw_records", lambda path: [SimpleNamespace(**row) for row in clean.to_dict("records")], raising=False)
    monkeypatch.setattr(flow, "build_clean_dataframe", lambda records, run_date: clean.copy(), raising=False)
    monkeypatch.setattr(flow, "LocalEmbeddingIndex", FakeIndex, raising=False)
    monkeypatch.setattr(flow, "run_data_quality_checks", fake_quality, raising=False)
    monkeypatch.setattr(flow, "build_freshness_report", fake_freshness, raising=False)
    monkeypatch.setattr(flow, "evaluate_pipeline", fake_evaluate, raising=False)
    monkeypatch.setattr(flow, "generate_corruption_report", fake_report, raising=False)

    flow.main()

    assert (settings.paths.corrupted_clean_csv).exists()
    assert (settings.paths.repaired_clean_csv).exists()
    assert (settings.paths.corrupted_metrics).exists()
    assert (settings.paths.repaired_metrics).exists()
    assert (settings.paths.comparison_report).read_text(encoding="utf-8") == "| Baseline | Corrupted | Repaired |"
    assert [item[0] for item in calls] == [
        "corrupt", "quality", "freshness", "build", "evaluate",
        "quality", "freshness", "build", "evaluate", "report",
    ]
