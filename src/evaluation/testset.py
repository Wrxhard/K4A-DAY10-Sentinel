from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, infer_research_category, read_json, write_json


REQUIRED_COLUMNS = {
    "paper_id", "title", "summary", "authors_joined",
    "categories_joined", "published",
}
REQUIRED_QUESTION_TYPES = {"summary", "authors", "date", "category", "multi_hop"}


@dataclass(frozen=True)
class TestSet:
    samples: list[dict[str, Any]]


def _sample(
    sample_id: str,
    question_type: str,
    question: str,
    ground_truth: str,
    document_ids: list[str],
) -> dict[str, Any]:
    """Create one sample while supporting both lab schema conventions."""
    return {
        "id": sample_id,
        "type": question_type,
        "question_type": "categories" if question_type == "category" else question_type,
        "question": question,
        "ground_truth": ground_truth,
        "ground_truth_doc_ids": document_ids,
    }


def build_test_set(df: pd.DataFrame, output_path: Path) -> list[dict[str, Any]]:
    """Build a deterministic five-question benchmark from cleaned papers."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required clean-data columns: {sorted(missing)}")
    if len(df) < 5:
        raise ValueError("At least five cleaned papers are required to build the benchmark.")

    papers = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)

    def choose(column: str, fraction: float) -> pd.Series:
        eligible = papers[papers[column].fillna("").astype(str).str.strip().ne("")]
        if eligible.empty:
            raise ValueError(f"No cleaned paper has a usable value for {column!r}.")
        position = min(int(len(eligible) * fraction), len(eligible) - 1)
        return eligible.iloc[position]

    summary_paper = choose("summary", 0.0)
    author_paper = choose("authors_joined", 0.25)
    date_paper = choose("published", 0.5)
    category_paper = choose("summary", 0.75)
    second_hop = choose("summary", 0.99)

    samples = [
        _sample(
            "eval_001", "summary",
            f"What is the summary of the paper '{summary_paper['title']}'?",
            str(summary_paper["summary"]), [str(summary_paper["paper_id"])],
        ),
        _sample(
            "eval_002", "authors",
            f"Who authored the paper '{author_paper['title']}'?",
            str(author_paper["authors_joined"]), [str(author_paper["paper_id"])],
        ),
        _sample(
            "eval_003", "date",
            f"When was the paper '{date_paper['title']}' published?",
            str(date_paper["published"]), [str(date_paper["paper_id"])],
        ),
        _sample(
            "eval_004", "category",
            f"What categories does the paper '{category_paper['title']}' belong to?",
            (
                str(category_paper["categories_joined"]).strip()
                or infer_research_category(str(category_paper["title"]), str(category_paper["summary"]))
            ),
            [str(category_paper["paper_id"])],
        ),
        _sample(
            "eval_005", "multi_hop",
            (
                f"How do the research focuses of '{summary_paper['title']}' and "
                f"'{second_hop['title']}' complement each other?"
            ),
            (
                f"{summary_paper['title']}: {first_sentence(str(summary_paper['summary']))} "
                f"{second_hop['title']}: {first_sentence(str(second_hop['summary']))}"
            ),
            [str(summary_paper["paper_id"]), str(second_hop["paper_id"])],
        ),
    ]
    write_json(output_path, samples)
    return samples


def _is_current_benchmark(samples: Any) -> bool:
    if not isinstance(samples, list) or len(samples) != 5:
        return False
    if not all(isinstance(item, dict) for item in samples):
        return False
    required_fields = {"id", "type", "question", "ground_truth", "ground_truth_doc_ids"}
    return (
        all(required_fields <= set(item) for item in samples)
        and {item["type"] for item in samples} == REQUIRED_QUESTION_TYPES
    )


def load_or_create_test_set(
    df: pd.DataFrame,
    output_path: Path,
    refresh: bool = False,
) -> TestSet:
    """Load a valid benchmark or rebuild stale/legacy benchmark artifacts."""
    if output_path.exists() and not refresh:
        existing = read_json(output_path)
        if _is_current_benchmark(existing):
            return TestSet(samples=existing)
    return TestSet(samples=build_test_set(df, output_path))

