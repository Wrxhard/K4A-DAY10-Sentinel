from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def _format_metrics(metrics: dict[str, Any]) -> str:
    rows = []
    for key, value in metrics.items():
        if key == "ragas" and isinstance(value, dict):
            detail = value.get("skipped") or value.get("error")
            rendered = detail if detail else ", ".join(
                f"{name}={score}" for name, score in value.items()
            )
        elif isinstance(value, float):
            rendered = f"{value:.4f}"
        else:
            rendered = str(value)
        rows.append(f"| `{key}` | {rendered} |")
    return "\n".join(rows) or "| _(none)_ | |"

def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a readable baseline summary of source, metrics, and data health."""
    source_rows = "\n".join(
        f"| `{key}` | {value} |" for key, value in source_summary.items()
    )
    freshness_rows = "\n".join(
        f"| `{key}` | {value} |" for key, value in freshness.items()
    ) or "| _(no freshness data)_ | |"
    quality_status = "PASS" if quality.get("success") else "FAIL"
    content = f"""# Phase 1 Baseline Report

## Source and corpus

| Item | Value |
| --- | --- |
{source_rows}

## Baseline evaluation

| Metric | Value |
| --- | --- |
{_format_metrics(metrics)}

## Data quality

Status: **{quality_status}**

## Freshness

| Check | Value |
| --- | --- |
{freshness_rows}
"""
    write_text(Path(report_path), content)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write the three-state corruption and repair comparison report."""
    states = (
        ("Baseline", baseline_metrics, None, None),
        ("Corrupted", corrupted_metrics, corrupted_quality, corrupted_freshness),
        ("Repaired", repaired_metrics, None, repaired_freshness),
    )
    keys = list(dict.fromkeys(key for _, metrics, _, _ in states for key in metrics))
    metric_rows = "\n".join(
        f"| `{key}` | " + " | ".join(str(metrics.get(key, "—")) for _, metrics, _, _ in states) + " |"
        for key in keys
    )
    content = f"""# Data Corruption and Repair Report

## Evaluation comparison

| Metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
{metric_rows}

## Quality and freshness observations

- Corrupted quality checks passed: **{corrupted_quality.get('success', False)}**
- Corrupted freshness: **{corrupted_freshness.get('is_fresh', 'unknown')}**
- Repaired freshness: **{repaired_freshness.get('is_fresh', 'unknown')}**
"""
    write_text(Path(report_path), content)
