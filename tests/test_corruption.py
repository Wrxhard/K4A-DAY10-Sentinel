import json

import pandas as pd

from ingestion.corruption import corrupt_clean_dataframe


def _sample_dataframe(rows: int = 24) -> pd.DataFrame:
    published = pd.date_range("2026-01-01", periods=rows, freq="D")[::-1]
    return pd.DataFrame(
        {
            "paper_id": [f"paper-{index}" for index in range(rows)],
            "title": [f"A sufficiently long title {index}" for index in range(rows)],
            "summary": [f"Summary for paper {index}" for index in range(rows)],
            "authors_joined": [f"Author {index}" for index in range(rows)],
            "categories_joined": ["computer science" for _ in range(rows)],
            "published": published.strftime("%Y-%m-%d"),
            "age_days": [10 for _ in range(rows)],
            "summary_chars": [20 for _ in range(rows)],
            "text_for_embedding": [f"original text {index}" for index in range(rows)],
        }
    )


def test_corruption_applies_all_six_scenarios_and_preserves_24_rows(tmp_path):
    source = _sample_dataframe()
    log_path = tmp_path / "corruption_log.json"

    corrupted = corrupt_clean_dataframe(source, log_path)

    assert len(corrupted) == 24
    assert len(corrupted) > corrupted["paper_id"].nunique()
    assert (corrupted["title"].str.len() < 10).any()
    assert (corrupted["summary"] == "").any()
    assert (corrupted["text_for_embedding"].str.contains("NOISE")).any()
    assert (pd.to_datetime(corrupted["published"]) < pd.Timestamp("2026-01-01")).any()
    assert set(corrupted.columns) >= {"age_days", "summary_chars", "text_for_embedding"}

    log = json.loads(log_path.read_text(encoding="utf-8"))
    assert log["input_rows"] == 24
    assert log["output_rows"] == 24
    assert {item["name"] for item in log["scenarios"]} == {
        "drop_latest_records",
        "blank_summary",
        "inject_text_noise",
        "truncate_title",
        "stale_date",
        "duplicate_rows",
    }
