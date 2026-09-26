from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def _require_file(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {description}: {path}")


def _write_dataframe_artifacts(dataframe: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    write_csv(dataframe, csv_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_json(json_path, orient="records", indent=2, force_ascii=False)


def _run_state_observability(dataframe: pd.DataFrame, settings, state: str) -> tuple[dict, dict]:
    quality = run_data_quality_checks(dataframe, settings, state)
    quality_path = settings.paths.quality_dir / f"{state}_quality_report.json"
    write_json(quality_path, quality)
    freshness_path = settings.paths.quality_dir / f"{state}_freshness_report.json"
    freshness = build_freshness_report(dataframe, settings, freshness_path)
    return quality, freshness


def main() -> None:
    """Run corruption, raw-data repair, evaluation, and comparison reporting."""
    settings = load_settings()
    paths = settings.paths

    _require_file(paths.clean_json, "clean dataset")
    _require_file(paths.baseline_metrics, "baseline metrics")
    _require_file(paths.eval_testset, "evaluation test set")
    _require_file(paths.raw_records_json, "raw records")

    clean = pd.read_json(paths.clean_json)
    baseline_metrics = read_json(paths.baseline_metrics)

    corrupted = corrupt_clean_dataframe(clean, paths.corruption_log)
    _write_dataframe_artifacts(corrupted, paths.corrupted_clean_csv, paths.corrupted_clean_json)
    corrupted_quality, corrupted_freshness = _run_state_observability(corrupted, settings, "corrupted")
    corrupted_index = LocalEmbeddingIndex.build(corrupted, settings, paths.corrupted_embeddings_json)
    evaluate_pipeline(
        settings,
        corrupted_index,
        paths.eval_testset,
        paths.corrupted_metrics,
        paths.corrupted_answers,
    )

    raw_records = load_raw_records(paths.raw_records_json)
    if not raw_records:
        raise RuntimeError("Raw records are empty; repaired dataset cannot be rebuilt.")
    repaired = build_clean_dataframe(raw_records, now_utc())
    if repaired.empty:
        raise RuntimeError("Repair produced an empty clean dataset.")
    _write_dataframe_artifacts(repaired, paths.repaired_clean_csv, paths.repaired_clean_json)
    repaired_quality, repaired_freshness = _run_state_observability(repaired, settings, "repaired")
    repaired_index = LocalEmbeddingIndex.build(repaired, settings, paths.repaired_embeddings_json)
    evaluate_pipeline(
        settings,
        repaired_index,
        paths.eval_testset,
        paths.repaired_metrics,
        paths.repaired_answers,
    )

    # Load baseline quality and freshness for full three-state comparison
    baseline_quality = read_json(paths.baseline_quality_report) if paths.baseline_quality_report.exists() else None
    baseline_freshness = read_json(paths.freshness_report) if paths.freshness_report.exists() else None

    generate_corruption_report(
        paths.comparison_report,
        baseline_metrics,
        read_json(paths.corrupted_metrics),
        read_json(paths.repaired_metrics),
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
        baseline_quality=baseline_quality,
        baseline_freshness=baseline_freshness,
    )

    print(f"Corruption flow complete: {len(corrupted)} corrupted rows")
    print(f"Repair flow complete: {len(repaired)} repaired rows")
    print(f"Comparison report: {paths.comparison_report}")
