from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import load_or_create_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Build and evaluate the clean baseline corpus end to end."""
    settings = load_settings()
    paths = settings.paths

    if settings.refresh_source or not paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(paths.raw_records_json)
    if not records:
        raise RuntimeError("The source returned no paper records; baseline pipeline cannot continue.")

    dataframe = build_clean_dataframe(records, now_utc())
    if dataframe.empty:
        raise RuntimeError("Cleaning produced no paper rows; baseline pipeline cannot continue.")
    write_csv(dataframe, paths.clean_csv)
    dataframe.to_json(paths.clean_json, orient="records", indent=2, force_ascii=False)

    quality = run_data_quality_checks(dataframe, settings, "baseline")
    write_json(paths.baseline_quality_report, quality)
    if not quality["success"]:
        raise RuntimeError(f"Baseline data quality checks failed: {paths.baseline_quality_report}")

    freshness = build_freshness_report(dataframe, settings, paths.freshness_report)
    index = LocalEmbeddingIndex.build(dataframe, settings, paths.embeddings_json)
    test_set = load_or_create_test_set(
        dataframe,
        paths.eval_testset,
        refresh=settings.refresh_test_set,
    )
    evaluation = evaluate_pipeline(
        settings,
        index,
        paths.eval_testset,
        paths.baseline_metrics,
        paths.baseline_answers,
    )

    source_summary = {
        "source": settings.source_api,
        "records_loaded": len(records),
        "clean_records": len(dataframe),
        "test_samples": len(test_set.samples),
        "collection": index.collection_name,
    }
    generate_phase1_report(
        paths.baseline_report,
        source_summary,
        evaluation.summary,
        quality,
        freshness,
    )
    print(f"Baseline pipeline complete: {len(dataframe)} clean papers")
    print(f"Retrieval hit rate: {evaluation.summary['retrieval_hit_rate']:.3f}")
    print(f"Report: {paths.baseline_report}")
