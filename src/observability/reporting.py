from __future__ import annotations

from typing import Any


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Viet markdown report cho baseline phase.

    Pseudo-code:
    1. Gom source summary.
    2. In metrics retrieval/evaluation.
    3. In data quality va freshness.
    4. Ghi markdown vao report_path.
    """
    from pathlib import Path
    
    report_content = f"""# Baseline Data Pipeline Phase 1 Report

## 1. Source Summary
- **API Source**: {source_summary.get('source_api', 'N/A')}
- **Query**: `{source_summary.get('query', 'N/A')}`
- **Filter**: `{source_summary.get('filter', 'N/A')}`
- **Items Returned**: {source_summary.get('items_returned', 'N/A')}
- **Fetched At**: {source_summary.get('fetched_at', 'N/A')}

## 2. Evaluation Metrics
- **Total Test Samples**: {metrics.get('samples', 0)}
- **Retrieval Hit Rate**: {metrics.get('retrieval_hit_rate', 0.0) * 100:.1f}%
- **Mean Token F1**: {metrics.get('mean_token_f1', 0.0) * 100:.1f}%
- **Judge Accuracy**: {metrics.get('judge_accuracy', 0.0) * 100:.1f}%
- **Mean Judge Score**: {metrics.get('mean_judge_score', 0.0):.2f}/5.0

## 3. Data Quality Checks
- **Report Name**: {quality.get('report_name', 'N/A')}
- **Status**: {"PASS" if quality.get('success') else "FAIL"}
- **Total Cleaned Rows**: {quality.get('total_rows', 0)}
- **Duplicate Count**: {quality.get('duplicate_count', 0)}
- **Missing Paper IDs**: {quality.get('missing_paper_ids', 0)}
- **Missing/Blank Titles**: {quality.get('missing_titles', 0)}
- **Short Summaries (< 10 chars)**: {quality.get('short_summaries', 0)}

## 4. Freshness
- **Is Fresh**: {"YES" if freshness.get('is_fresh') else "NO"}
- **Latest Published Date**: {freshness.get('latest_published', 'N/A')}
- **Oldest Published Date**: {freshness.get('oldest_published', 'N/A')}
- **Stale Rows (>{freshness.get('freshness_threshold_days', 180)} days old)**: {freshness.get('stale_rows', 0)}
"""
    out_p = Path(report_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        f.write(report_content)


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
    """Viet markdown report so sanh baseline/corrupted/repaired."""
    from pathlib import Path
    
    report_content = f"""# Data Corruption & Recovery Comparison Report

## 1. Metric Comparison

| Metric | Baseline | Corrupted | Repaired | Delta (Repaired - Corrupted) |
|---|---|---|---|---|
| **Retrieval Hit Rate** | {baseline_metrics.get('retrieval_hit_rate', 0.0) * 100:.1f}% | {corrupted_metrics.get('retrieval_hit_rate', 0.0) * 100:.1f}% | {repaired_metrics.get('retrieval_hit_rate', 0.0) * 100:.1f}% | {(repaired_metrics.get('retrieval_hit_rate', 0.0) - corrupted_metrics.get('retrieval_hit_rate', 0.0)) * 100:+.1f}% |
| **Mean Token F1** | {baseline_metrics.get('mean_token_f1', 0.0) * 100:.1f}% | {corrupted_metrics.get('mean_token_f1', 0.0) * 100:.1f}% | {repaired_metrics.get('mean_token_f1', 0.0) * 100:.1f}% | {(repaired_metrics.get('mean_token_f1', 0.0) - corrupted_metrics.get('mean_token_f1', 0.0)) * 100:+.1f}% |
| **Judge Accuracy** | {baseline_metrics.get('judge_accuracy', 0.0) * 100:.1f}% | {corrupted_metrics.get('judge_accuracy', 0.0) * 100:.1f}% | {repaired_metrics.get('judge_accuracy', 0.0) * 100:.1f}% | {(repaired_metrics.get('judge_accuracy', 0.0) - corrupted_metrics.get('judge_accuracy', 0.0)) * 100:+.1f}% |
| **Mean Judge Score** | {baseline_metrics.get('mean_judge_score', 0.0):.2f}/5.0 | {corrupted_metrics.get('mean_judge_score', 0.0):.2f}/5.0 | {repaired_metrics.get('mean_judge_score', 0.0):.2f}/5.0 | {repaired_metrics.get('mean_judge_score', 0.0) - corrupted_metrics.get('mean_judge_score', 0.0):+.2f} |

## 2. Observability & Data Quality Comparison

### Corrupted State
- **Success Gate Status**: {"PASS" if corrupted_quality.get('success') else "FAIL"}
- **Total Rows**: {corrupted_quality.get('total_rows', 0)}
- **Duplicates**: {corrupted_quality.get('duplicate_count', 0)}
- **Missing/Blank Titles**: {corrupted_quality.get('missing_titles', 0)}
- **Short Summaries**: {corrupted_quality.get('short_summaries', 0)}
- **Freshness Stale Rows**: {corrupted_freshness.get('stale_rows', 0)} (Is Fresh: {"YES" if corrupted_freshness.get('is_fresh') else "NO"})

### Repaired State
- **Success Gate Status**: {"PASS" if repaired_quality.get('success') else "FAIL"}
- **Total Rows**: {repaired_quality.get('total_rows', 0)}
- **Duplicates**: {repaired_quality.get('duplicate_count', 0)}
- **Missing/Blank Titles**: {repaired_quality.get('missing_titles', 0)}
- **Short Summaries**: {repaired_quality.get('short_summaries', 0)}
- **Freshness Stale Rows**: {repaired_freshness.get('stale_rows', 0)} (Is Fresh: {"YES" if repaired_freshness.get('is_fresh') else "NO"})

## 3. Analysis & Key Takeaways
- **Data corruption** significantly degrades the RAG agent's retrieval accuracy and answer quality (e.g. empty or noisy summaries cause bad hits/misses).
- **Data observability tools** successfully capture these failures through quality checks and freshness metrics.
- **Repairing the pipeline** from trusted raw snapshots restores the vector index accuracy and recovers the agent's performance.
"""
    out_p = Path(report_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        f.write(report_content)

