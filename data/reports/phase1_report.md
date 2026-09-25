# Phase 1 Baseline Report

## Source and corpus

| Item | Value |
| --- | --- |
| `source` | Crossref REST API |
| `records_loaded` | 24 |
| `clean_records` | 24 |
| `test_samples` | 5 |
| `collection` | papers-baseline |

## Baseline evaluation

| Metric | Value |
| --- | --- |
| `samples` | 5 |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 0.7073 |
| `judge_accuracy` | 0.6000 |
| `mean_judge_score` | 3.4000 |
| `ragas` | Set RUN_RAGAS=1 to enable the slower Ragas pass. |

## Data quality

Status: **PASS**

## Freshness

| Check | Value |
| --- | --- |
| `latest_published` | 2026-09-15 |
| `oldest_published` | 2026-04-01 |
| `stale_rows` | 0 |
| `total_rows` | 24 |
| `is_fresh` | True |
