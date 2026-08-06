from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Tao bo data quality checks.

    Pseudo-code:
    1. Check row count.
    2. Check `paper_id` not null va unique.
    3. Check `title` not null.
    4. Check do dai `summary`.
    5. Check freshness bang `age_days`.
    6. Ghi ket qua vao `data/quality/`.
    """
    import json
    from pathlib import Path
    
    total_rows = len(df)
    
    # Uniqueness
    unique_ids = df["paper_id"].nunique() if total_rows > 0 else 0
    duplicate_count = total_rows - unique_ids
    
    # Missing / Null values
    missing_paper_ids = df["paper_id"].isna().sum() if total_rows > 0 else 0
    missing_titles = df["title"].isna().sum() if total_rows > 0 else 0
    blank_titles = (df["title"] == "").sum() if total_rows > 0 else 0
    
    # Summary length check
    short_summaries = (df["summary_chars"] < 10).sum() if total_rows > 0 else 0
    
    # Freshness
    freshness_threshold = settings.freshness_threshold_days
    stale_rows = (df["age_days"] > freshness_threshold).sum() if (total_rows > 0 and "age_days" in df.columns) else 0
    
    success = (
        total_rows > 0
        and duplicate_count == 0
        and missing_paper_ids == 0
        and missing_titles == 0
        and blank_titles == 0
        and short_summaries == 0
        and stale_rows == 0
    )
    
    report = {
        "report_name": report_name,
        "success": bool(success),
        "total_rows": int(total_rows),
        "duplicate_count": int(duplicate_count),
        "missing_paper_ids": int(missing_paper_ids),
        "missing_titles": int(missing_titles + blank_titles),
        "short_summaries": int(short_summaries),
        "stale_rows": int(stale_rows),
        "freshness_threshold_days": int(freshness_threshold)
    }
    
    quality_dir = settings.paths.quality_dir
    quality_dir.mkdir(parents=True, exist_ok=True)
    report_file = quality_dir / f"{report_name}_quality.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Tong hop freshness report.

    Pseudo-code:
    1. Tim latest va oldest published date.
    2. Dem so dong stale.
    3. Tao payload:
       - latest_published
       - oldest_published
       - stale_rows
       - total_rows
       - is_fresh
    4. Ghi JSON report.
    """
    import json
    from pathlib import Path
    
    total_rows = len(df)
    
    if total_rows == 0:
        report = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": 0,
            "is_fresh": False
        }
    else:
        latest_published = df["published"].max() if "published" in df.columns else None
        oldest_published = df["published"].min() if "published" in df.columns else None
        freshness_threshold = settings.freshness_threshold_days
        stale_rows = (df["age_days"] > freshness_threshold).sum() if "age_days" in df.columns else 0
        is_fresh = bool(stale_rows == 0)
        
        report = {
            "latest_published": latest_published,
            "oldest_published": oldest_published,
            "stale_rows": int(stale_rows),
            "total_rows": int(total_rows),
            "is_fresh": is_fresh
        }
        
    out_p = Path(report_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    return report

