from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings


def _duplicate_safe_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a comparable view when object columns contain lists or dicts."""
    comparable = df.copy()
    for column in comparable.columns:
        if comparable[column].map(lambda value: isinstance(value, (list, dict))).any():
            comparable[column] = comparable[column].map(
                lambda value: json.dumps(value, sort_keys=True, ensure_ascii=True)
                if isinstance(value, (list, dict))
                else value
            )
    return comparable


# ---------------------------------------------------------------------------
# Data Quality Checks  (CP0-CP4)
# ---------------------------------------------------------------------------

def run_data_quality_checks(
    df: pd.DataFrame,
    settings: Settings,
    report_name: str,
) -> dict[str, Any]:
    """Run a suite of data-quality checks on a cleaned DataFrame.

    Checks performed
    ----------------
    1. **row_count**        – total rows > 0
    2. **paper_id_not_null** – ``paper_id`` has zero nulls
    3. **paper_id_unique**  – ``paper_id`` has zero duplicates
    4. **title_not_null**   – ``title`` has zero nulls or blank strings
    5. **summary_length**   – every ``summary`` has >= 20 characters
    6. **missing_fields**   – per-column null counts (informational)
    7. **duplicate_rows**   – fully duplicated rows
    8. **freshness**        – ``age_days`` within threshold

    Returns a dict with all check results and an overall ``passed`` flag.
    The dict is also persisted as ``data/quality/{report_name}_quality.json``.
    """

    total_rows = len(df)
    checks: dict[str, Any] = {}

    # --- 1. Row count ---
    checks["row_count"] = {
        "value": total_rows,
        "passed": total_rows > 0,
    }

    if total_rows == 0:
        # Short-circuit: nothing else to check
        result = _build_result(report_name, checks, settings)
        _persist(result, settings.paths.quality_dir, report_name)
        return result

    # --- 2. paper_id not null ---
    missing_paper_ids = int(df["paper_id"].isna().sum())
    checks["paper_id_not_null"] = {
        "null_count": missing_paper_ids,
        "passed": missing_paper_ids == 0,
    }

    # --- 3. paper_id unique ---
    unique_ids = int(df["paper_id"].nunique())
    duplicate_ids = total_rows - unique_ids
    checks["paper_id_unique"] = {
        "unique_count": unique_ids,
        "duplicate_count": duplicate_ids,
        "passed": duplicate_ids == 0,
    }

    # --- 4. title not null / blank ---
    missing_titles = int(df["title"].isna().sum())
    blank_titles = int((df["title"].astype(str).str.strip() == "").sum()) - missing_titles
    blank_titles = max(blank_titles, 0)
    checks["title_not_null"] = {
        "null_count": missing_titles,
        "blank_count": blank_titles,
        "passed": (missing_titles + blank_titles) == 0,
    }

    # --- 5. summary length ---
    if "summary_chars" in df.columns:
        short = int((df["summary_chars"] < 20).sum())
    else:
        short = int((df["summary"].astype(str).str.len() < 20).sum())
    checks["summary_length"] = {
        "short_count": short,
        "threshold_chars": 20,
        "passed": short == 0,
    }

    # --- 6. missing fields (informational) ---
    key_cols = [
        "paper_id", "title", "summary", "published",
        "authors_joined", "categories_joined", "text_for_embedding",
    ]
    missing_map: dict[str, int] = {}
    for col in key_cols:
        if col in df.columns:
            missing_map[col] = int(df[col].isna().sum())
    checks["missing_fields"] = missing_map

    # --- 7. duplicate rows ---
    full_dup = int(_duplicate_safe_dataframe(df).duplicated().sum())
    checks["duplicate_rows"] = {
        "count": full_dup,
        "passed": full_dup == 0,
    }


    # --- 8. freshness ---
    if "age_days" in df.columns:
        age = df["age_days"].dropna()
        stale = int((age > settings.freshness_threshold_days).sum())
        mean_age = round(float(age.mean()), 1) if len(age) else 0.0
        max_age = int(age.max()) if len(age) else 0
    else:
        stale, mean_age, max_age = 0, 0.0, 0
    checks["freshness"] = {
        "stale_rows": stale,
        "mean_age_days": mean_age,
        "max_age_days": max_age,
        "threshold_days": settings.freshness_threshold_days,
        "passed": stale == 0,
    }

    result = _build_result(report_name, checks, settings)
    _persist(result, settings.paths.quality_dir, report_name)
    return result


def _build_result(
    report_name: str,
    checks: dict[str, Any],
    settings: Settings,
) -> dict[str, Any]:
    """Aggregate individual check outcomes into a single result dict."""
    passed_flags = [
        v.get("passed", True)
        for v in checks.values()
        if isinstance(v, dict) and "passed" in v
    ]
    overall = all(passed_flags) if passed_flags else False

    total_rows = checks.get("row_count", {}).get("value", 0)
    dup_count = checks.get("paper_id_unique", {}).get("duplicate_count", 0)
    missing_pids = checks.get("paper_id_not_null", {}).get("null_count", 0)
    title_null = checks.get("title_not_null", {}).get("null_count", 0)
    title_blank = checks.get("title_not_null", {}).get("blank_count", 0)
    short_summ = checks.get("summary_length", {}).get("short_count", 0)
    stale = checks.get("freshness", {}).get("stale_rows", 0)

    return {
        "report_name": report_name,
        "success": bool(overall),
        "total_rows": int(total_rows),
        "duplicate_count": int(dup_count),
        "missing_paper_ids": int(missing_pids),
        "missing_titles": int(title_null + title_blank),
        "short_summaries": int(short_summ),
        "stale_rows": int(stale),
        "freshness_threshold_days": int(settings.freshness_threshold_days),
        "checked_at": datetime.now(UTC).isoformat(),
        "checks_detail": checks,
    }


def _persist(result: dict[str, Any], quality_dir: Path, report_name: str) -> None:
    quality_dir.mkdir(parents=True, exist_ok=True)
    out = quality_dir / f"{report_name}_quality.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Freshness Report  (CP0-CP4)
# ---------------------------------------------------------------------------

def build_freshness_report(
    df: pd.DataFrame,
    settings: Settings,
    report_path,
) -> dict[str, Any]:
    """Build a freshness report from the ``published`` / ``age_days`` columns.

    Output payload
    --------------
    - latest_published, oldest_published
    - mean_age_days, median_age_days, max_age_days
    - stale_rows, total_rows
    - freshness_threshold_days
    - is_fresh  (True when stale_rows == 0)
    """

    total_rows = len(df)

    if total_rows == 0:
        report: dict[str, Any] = {
            "latest_published": None,
            "oldest_published": None,
            "mean_age_days": None,
            "median_age_days": None,
            "max_age_days": None,
            "stale_rows": 0,
            "total_rows": 0,
            "freshness_threshold_days": settings.freshness_threshold_days,
            "is_fresh": False,
            "checked_at": datetime.now(UTC).isoformat(),
        }
    else:
        latest = str(df["published"].max()) if "published" in df.columns else None
        oldest = str(df["published"].min()) if "published" in df.columns else None

        if "age_days" in df.columns:
            age = df["age_days"].dropna()
            stale = int((age > settings.freshness_threshold_days).sum())
            mean_age = round(float(age.mean()), 1) if len(age) else None
            median_age = round(float(age.median()), 1) if len(age) else None
            max_age = int(age.max()) if len(age) else None
        else:
            stale, mean_age, median_age, max_age = 0, None, None, None

        report = {
            "latest_published": latest,
            "oldest_published": oldest,
            "mean_age_days": mean_age,
            "median_age_days": median_age,
            "max_age_days": max_age,
            "stale_rows": stale,
            "total_rows": total_rows,
            "freshness_threshold_days": settings.freshness_threshold_days,
            "is_fresh": bool(stale == 0),
            "checked_at": datetime.now(UTC).isoformat(),
        }

    out_p = Path(report_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    return report
