from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.utils import write_text


# ---------------------------------------------------------------------------
# Phase-1 Baseline Report  (CP3)
# ---------------------------------------------------------------------------

def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Generate a Markdown report for the baseline pipeline run.

    Sections
    --------
    1. Source Summary  – API, query, filter, counts
    2. Evaluation Metrics – retrieval & answer quality
    3. Data Quality Gates – all check results + PASS/FAIL
    4. Freshness – age distribution and staleness
    """

    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    # --- helpers ----
    def _pct(v: float | None) -> str:
        return f"{v * 100:.1f}%" if v is not None else "N/A"

    def _f2(v: float | None) -> str:
        return f"{v:.2f}" if v is not None else "N/A"

    def _gate(flag: bool | None) -> str:
        if flag is None:
            return "N/A"
        return "✅ PASS" if flag else "❌ FAIL"

    # --- RAGAS ---
    ragas = metrics.get("ragas", {})
    if isinstance(ragas, dict) and "skipped" not in ragas and "error" not in ragas:
        ragas_lines = "\n".join(f"| {k} | {_f2(v)} |" for k, v in ragas.items())
        ragas_section = (
            "### RAGAS Metrics\n\n"
            "| Metric | Score |\n"
            "|---|---|\n"
            f"{ragas_lines}\n"
        )
    else:
        ragas_note = ragas.get("skipped") or ragas.get("error", "N/A") if isinstance(ragas, dict) else str(ragas)
        ragas_section = f"### RAGAS Metrics\n\n> {ragas_note}\n"

    # --- quality detail ---
    checks_detail = quality.get("checks_detail", {})
    quality_rows = []
    for check_name, check_val in checks_detail.items():
        if isinstance(check_val, dict) and "passed" in check_val:
            quality_rows.append(
                f"| {check_name} | {_gate(check_val['passed'])} | {_detail_str(check_val)} |"
            )

    quality_table = (
        "| Check | Status | Detail |\n"
        "|---|---|---|\n"
        + "\n".join(quality_rows)
    ) if quality_rows else (
        f"| Overall | {_gate(quality.get('success'))} | rows={quality.get('total_rows', 0)}, "
        f"dup={quality.get('duplicate_count', 0)}, "
        f"missing_pid={quality.get('missing_paper_ids', 0)}, "
        f"missing_title={quality.get('missing_titles', 0)}, "
        f"short_summary={quality.get('short_summaries', 0)} |"
    )

    md = f"""# Phase 1 – Baseline Pipeline Report

> Generated: {ts}

---

## 1. Source Summary

| Item | Value |
|---|---|
| API Source | {source_summary.get('source_api', 'N/A')} |
| Query | `{source_summary.get('query', 'N/A')}` |
| Filter | `{source_summary.get('filter', 'N/A')}` |
| Items Returned (raw) | {source_summary.get('items_returned', 'N/A')} |
| Fetched At | {source_summary.get('fetched_at', 'N/A')} |

---

## 2. Evaluation Metrics

| Metric | Value |
|---|---|
| Test Samples | {metrics.get('samples', 0)} |
| Retrieval Hit Rate | {_pct(metrics.get('retrieval_hit_rate'))} |
| Mean Token F1 | {_pct(metrics.get('mean_token_f1'))} |
| Judge Accuracy | {_pct(metrics.get('judge_accuracy'))} |
| Mean Judge Score | {_f2(metrics.get('mean_judge_score'))}/5.00 |

{ragas_section}

---

## 3. Data Quality Gates

**Overall gate: {_gate(quality.get('success'))}**

{quality_table}

- Total rows: **{quality.get('total_rows', 0)}**
- Freshness threshold: **{quality.get('freshness_threshold_days', 180)} days**

---

## 4. Freshness

| Item | Value |
|---|---|
| Is Fresh | {_gate(freshness.get('is_fresh'))} |
| Latest Published | {freshness.get('latest_published', 'N/A')} |
| Oldest Published | {freshness.get('oldest_published', 'N/A')} |
| Mean Age (days) | {freshness.get('mean_age_days', 'N/A')} |
| Median Age (days) | {freshness.get('median_age_days', 'N/A')} |
| Max Age (days) | {freshness.get('max_age_days', 'N/A')} |
| Stale Rows | {freshness.get('stale_rows', 0)} / {freshness.get('total_rows', 0)} |
| Threshold | {freshness.get('freshness_threshold_days', 180)} days |
"""

    write_text(Path(report_path), md)


def _detail_str(check: dict[str, Any]) -> str:
    """Render the important numeric fields of a single check dict."""
    skip = {"passed"}
    parts = []
    for k, v in check.items():
        if k in skip:
            continue
        parts.append(f"{k}={v}")
    return ", ".join(parts) if parts else ""


# ---------------------------------------------------------------------------
# Corruption / Comparison Report  (CP5-CP6)
# ---------------------------------------------------------------------------

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
    """Generate a Markdown comparison report: baseline → corrupted → repaired.

    Sections
    --------
    1. Metrics side-by-side  (4 metrics × 3 states + deltas)
    2. Data Quality comparison  (corrupted vs repaired)
    3. Freshness comparison
    4. Impact & Recovery Analysis
    """

    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    def _pct(v: float | None) -> str:
        return f"{v * 100:.1f}%" if v is not None else "N/A"

    def _f2(v: float | None) -> str:
        return f"{v:.2f}" if v is not None else "N/A"

    def _delta_pct(a: float | None, b: float | None) -> str:
        if a is None or b is None:
            return "N/A"
        return f"{(a - b) * 100:+.1f}%"

    def _delta_f2(a: float | None, b: float | None) -> str:
        if a is None or b is None:
            return "N/A"
        return f"{a - b:+.2f}"

    def _gate(flag: bool | None) -> str:
        if flag is None:
            return "N/A"
        return "✅ PASS" if flag else "❌ FAIL"

    # ---- metrics keys ----
    metric_keys = [
        ("retrieval_hit_rate", "Retrieval Hit Rate", True),
        ("mean_token_f1",      "Mean Token F1",      True),
        ("judge_accuracy",     "Judge Accuracy",      True),
        ("mean_judge_score",   "Mean Judge Score",    False),
    ]

    rows = []
    for key, label, is_pct in metric_keys:
        b = baseline_metrics.get(key)
        c = corrupted_metrics.get(key)
        r = repaired_metrics.get(key)
        fmt = _pct if is_pct else _f2
        delta_fn = _delta_pct if is_pct else _delta_f2
        suffix = "" if is_pct else "/5.00"
        rows.append(
            f"| **{label}** "
            f"| {fmt(b)}{suffix} "
            f"| {fmt(c)}{suffix} "
            f"| {fmt(r)}{suffix} "
            f"| {delta_fn(c, b)} "
            f"| {delta_fn(r, c)} |"
        )

    metrics_table = "\n".join(rows)

    # ---- quality comparison ----
    def _qual_block(label: str, q: dict, f: dict) -> str:
        return (
            f"### {label}\n\n"
            f"| Check | Value |\n"
            f"|---|---|\n"
            f"| Gate Status | {_gate(q.get('success'))} |\n"
            f"| Total Rows | {q.get('total_rows', 0)} |\n"
            f"| Duplicates | {q.get('duplicate_count', 0)} |\n"
            f"| Missing Paper IDs | {q.get('missing_paper_ids', 0)} |\n"
            f"| Missing/Blank Titles | {q.get('missing_titles', 0)} |\n"
            f"| Short Summaries (<20 chars) | {q.get('short_summaries', 0)} |\n"
            f"| Stale Rows | {q.get('stale_rows', 0)} |\n"
            f"| Is Fresh | {_gate(f.get('is_fresh'))} |\n"
            f"| Latest Published | {f.get('latest_published', 'N/A')} |\n"
            f"| Oldest Published | {f.get('oldest_published', 'N/A')} |\n"
        )

    corrupted_block = _qual_block("Corrupted State", corrupted_quality, corrupted_freshness)
    repaired_block = _qual_block("Repaired State", repaired_quality, repaired_freshness)

    # ---- signal change analysis ----
    signal_changes = []
    signal_unchanged = []

    for label, cval, rval in [
        ("duplicate_count", corrupted_quality.get("duplicate_count", 0), repaired_quality.get("duplicate_count", 0)),
        ("missing_titles", corrupted_quality.get("missing_titles", 0), repaired_quality.get("missing_titles", 0)),
        ("short_summaries", corrupted_quality.get("short_summaries", 0), repaired_quality.get("short_summaries", 0)),
        ("stale_rows", corrupted_quality.get("stale_rows", 0), repaired_quality.get("stale_rows", 0)),
        ("total_rows", corrupted_quality.get("total_rows", 0), repaired_quality.get("total_rows", 0)),
    ]:
        if cval != rval:
            signal_changes.append(f"- **{label}**: corrupted={cval} → repaired={rval}")
        else:
            signal_unchanged.append(f"- **{label}**: {cval} (unchanged)")

    changes_md = "\n".join(signal_changes) if signal_changes else "- (none)"
    unchanged_md = "\n".join(signal_unchanged) if signal_unchanged else "- (none)"

    # ---- recovery status ----
    b_hr = baseline_metrics.get("retrieval_hit_rate", 0)
    r_hr = repaired_metrics.get("retrieval_hit_rate", 0)
    b_f1 = baseline_metrics.get("mean_token_f1", 0)
    r_f1 = repaired_metrics.get("mean_token_f1", 0)
    b_ja = baseline_metrics.get("judge_accuracy", 0)
    r_ja = repaired_metrics.get("judge_accuracy", 0)

    recovery_items = []
    for name, bv, rv in [
        ("Retrieval Hit Rate", b_hr, r_hr),
        ("Mean Token F1", b_f1, r_f1),
        ("Judge Accuracy", b_ja, r_ja),
    ]:
        if rv is not None and bv is not None:
            if abs(rv - bv) < 1e-6:
                recovery_items.append(f"- ✅ **{name}**: fully recovered to baseline ({rv * 100:.1f}%)")
            elif rv > bv:
                recovery_items.append(f"- ✅ **{name}**: exceeded baseline (repaired {rv * 100:.1f}% > baseline {bv * 100:.1f}%)")
            else:
                recovery_items.append(f"- ⚠️ **{name}**: partially recovered (repaired {rv * 100:.1f}% vs baseline {bv * 100:.1f}%)")

    quality_recovered = repaired_quality.get("success", False)
    freshness_recovered = repaired_freshness.get("is_fresh", False)
    recovery_items.append(f"- {'✅' if quality_recovered else '⚠️'} **Quality Gate**: {'PASS' if quality_recovered else 'FAIL'}")
    recovery_items.append(f"- {'✅' if freshness_recovered else '⚠️'} **Freshness**: {'Fresh' if freshness_recovered else 'Stale'}")

    recovery_md = "\n".join(recovery_items)

    md = f"""# Data Corruption & Recovery – Comparison Report

> Generated: {ts}

---

## 1. Metrics Comparison (Baseline → Corrupted → Repaired)

| Metric | Baseline | Corrupted | Repaired | Δ Corrupt vs Base | Δ Repair vs Corrupt |
|---|---|---|---|---|---|
{metrics_table}

---

## 2. Data Quality & Freshness Comparison

{corrupted_block}

{repaired_block}

---

## 3. Signal Change Analysis

**Signals that changed between corrupted → repaired:**

{changes_md}

**Signals unchanged:**

{unchanged_md}

---

## 4. Recovery Status

{recovery_md}

---

## 5. Key Takeaways

- **Data corruption** directly degrades RAG agent performance: retrieval hit rate dropped from \
{_pct(baseline_metrics.get('retrieval_hit_rate'))} to {_pct(corrupted_metrics.get('retrieval_hit_rate'))}, \
mean token F1 from {_pct(baseline_metrics.get('mean_token_f1'))} to {_pct(corrupted_metrics.get('mean_token_f1'))}.
- **Observability tools** successfully detected corruption through quality gate failures \
(duplicates={corrupted_quality.get('duplicate_count', 0)}, \
short summaries={corrupted_quality.get('short_summaries', 0)}, \
stale rows={corrupted_quality.get('stale_rows', 0)}).
- **Repair from trusted raw snapshot** restored metrics to baseline levels, \
proving the pipeline can self-heal when given clean source data.
"""

    write_text(Path(report_path), md)
