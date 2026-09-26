from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Apply deterministic corruption scenarios to a clean paper dataframe.

    The returned dataframe keeps the original row count so downstream RAG
    comparisons remain apples-to-apples.  The dropped rows are replaced by
    duplicated rows, and every mutation is recorded in ``output_log_path``.
    """
    if df.empty:
        raise ValueError("Cannot corrupt an empty dataframe.")

    corrupted = df.copy(deep=True)
    input_rows = len(corrupted)
    corrupted["published"] = corrupted["published"].astype(str)
    published_dates = pd.to_datetime(corrupted["published"], errors="coerce")
    corrupted = (
        corrupted.assign(_published_sort=published_dates)
        .sort_values("_published_sort", ascending=False, na_position="last")
        .drop(columns="_published_sort")
        .reset_index(drop=True)
    )

    drop_count = min(max(1, math.ceil(input_rows * 0.2)), max(input_rows - 1, 0))
    dropped_ids = corrupted.iloc[:drop_count]["paper_id"].astype(str).tolist()
    corrupted = corrupted.iloc[drop_count:].reset_index(drop=True)

    def selected_ids(start: int, count: int) -> list[str]:
        ids = corrupted.iloc[start : start + count]["paper_id"]
        return ids.astype(str).tolist()

    scenario_count = max(1, min(4, len(corrupted)))
    # Stale date needs to affect >25% of total rows so freshness check fails
    stale_count = max(scenario_count, math.ceil(input_rows * 0.35))
    blank_ids = selected_ids(0, scenario_count)
    noise_ids = selected_ids(scenario_count, scenario_count)
    truncate_ids = selected_ids(scenario_count * 2, scenario_count)
    stale_ids = selected_ids(0, min(stale_count, len(corrupted)))

    corrupted.loc[: scenario_count - 1, "summary"] = ""
    noise_start = scenario_count
    noise_end = min(noise_start + scenario_count, len(corrupted))
    corrupted.loc[noise_start : noise_end - 1, "text_for_embedding"] = (
        corrupted.loc[noise_start : noise_end - 1, "text_for_embedding"].astype(str)
        + " [NOISE::###@@@%%%]"
    )

    truncate_start = scenario_count * 2
    truncate_end = min(truncate_start + scenario_count, len(corrupted))
    corrupted.loc[truncate_start : truncate_end - 1, "title"] = (
        corrupted.loc[truncate_start : truncate_end - 1, "title"].astype(str).str.slice(0, 8)
    )

    stale_end_idx = min(stale_count, len(corrupted))
    stale_dates = pd.to_datetime(
        corrupted.loc[: stale_end_idx - 1, "published"], errors="coerce"
    ) - pd.DateOffset(years=5)
    corrupted.loc[: stale_end_idx - 1, "published"] = stale_dates.dt.strftime("%Y-%m-%d")

    # Rebuild derived fields after the field-level mutations.
    corrupted["title"] = corrupted["title"].fillna("").astype(str)
    corrupted["summary"] = corrupted["summary"].fillna("").astype(str)
    corrupted["summary_chars"] = corrupted["summary"].str.len()
    corrupted["authors_joined"] = corrupted.get("authors_joined", "").fillna("").astype(str)
    corrupted["categories_joined"] = corrupted.get("categories_joined", "").fillna("").astype(str)
    corrupted["text_for_embedding"] = (
        "Title: "
        + corrupted["title"]
        + "\nAuthors: "
        + corrupted["authors_joined"]
        + "\nPublished: "
        + corrupted["published"].fillna("").astype(str)
        + "\nCategories: "
        + corrupted["categories_joined"]
        + "\nSummary: "
        + corrupted["summary"]
    )

    # Re-apply noise after rebuilding the embedding text.
    corrupted.loc[noise_start : noise_end - 1, "text_for_embedding"] += " [NOISE::###@@@%%%]"

    now = pd.Timestamp(datetime.now(UTC).replace(tzinfo=None))
    published_dates = pd.to_datetime(corrupted["published"], errors="coerce")
    corrupted["age_days"] = (now - published_dates).dt.days

    duplicate_count = min(drop_count, len(corrupted))
    duplicate_source = corrupted.iloc[:duplicate_count].copy()
    duplicate_ids = duplicate_source["paper_id"].astype(str).tolist()
    corrupted = pd.concat([corrupted, duplicate_source], ignore_index=True)

    log = {
        "created_at": datetime.now(UTC).isoformat(),
        "input_rows": input_rows,
        "output_rows": len(corrupted),
        "scenarios": [
            {
                "name": "drop_latest_records",
                "description": "Dropped the newest records to simulate lost fresh data.",
                "count": len(dropped_ids),
                "record_ids": dropped_ids,
                "parameters": {"fraction": 0.2},
            },
            {
                "name": "blank_summary",
                "description": "Cleared summaries to simulate missing information.",
                "count": len(blank_ids),
                "record_ids": blank_ids,
            },
            {
                "name": "inject_text_noise",
                "description": "Added meaningless characters to embedding text.",
                "count": len(noise_ids),
                "record_ids": noise_ids,
                "parameters": {"noise": "[NOISE::###@@@%%%]"},
            },
            {
                "name": "truncate_title",
                "description": "Truncated titles below ten characters.",
                "count": len(truncate_ids),
                "record_ids": truncate_ids,
                "parameters": {"max_characters": 8},
            },
            {
                "name": "stale_date",
                "description": "Moved publication dates five years into the past.",
                "count": len(stale_ids),
                "record_ids": stale_ids,
                "parameters": {"years_back": 5},
            },
            {
                "name": "duplicate_rows",
                "description": "Duplicated rows to simulate duplicate records.",
                "count": len(duplicate_ids),
                "record_ids": duplicate_ids,
            },
        ],
    }

    log_path = Path(output_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    return corrupted
