from __future__ import annotations

import pandas as pd


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate nhieu dang data corruption.

    Pseudo-code:
    1. Drop mot so latest records.
    2. Blank summary o mot so dong.
    3. Inject noise vao text.
    4. Lam title bi truncate.
    5. Lam published date cu di.
    6. Add duplicate rows.
    7. Rebuild `text_for_embedding`.
    8. Ghi corruption log vao output_log_path.
    """
    import json
    from pathlib import Path
    
    # Do not mutate input dataframe
    corrupted_df = df.copy()
    corruption_log = []
    
    # 1. Drop a few latest records (e.g. top 3 oldest/newest depending on sort)
    # The dataframe is sorted by published descending, so the first 3 are the latest records.
    dropped_records = corrupted_df.head(3).to_dict(orient="records")
    corrupted_df = corrupted_df.iloc[3:].reset_index(drop=True)
    
    for r in dropped_records:
        corruption_log.append({
            "paper_id": r["paper_id"],
            "type": "drop_record",
            "parameter": "latest_records",
            "before": r["title"],
            "after": None
        })
        
    # 2. Blank summary for some rows
    if len(corrupted_df) > 0:
        idx_to_blank = 0
        paper_id = corrupted_df.loc[idx_to_blank, "paper_id"]
        before_summary = corrupted_df.loc[idx_to_blank, "summary"]
        corrupted_df.loc[idx_to_blank, "summary"] = ""
        corrupted_df.loc[idx_to_blank, "summary_chars"] = 0
        corruption_log.append({
            "paper_id": paper_id,
            "type": "blank_summary",
            "parameter": "",
            "before": before_summary,
            "after": ""
        })
        
    # 3. Inject noise into text (summary)
    if len(corrupted_df) > 1:
        idx_to_noise = 1
        paper_id = corrupted_df.loc[idx_to_noise, "paper_id"]
        before_summary = corrupted_df.loc[idx_to_noise, "summary"]
        noise_text = " [NOISE SYSTEM MALFUNCTION DATA CORRUPTED] " + before_summary
        corrupted_df.loc[idx_to_noise, "summary"] = noise_text
        corrupted_df.loc[idx_to_noise, "summary_chars"] = len(noise_text)
        corruption_log.append({
            "paper_id": paper_id,
            "type": "noise_summary",
            "parameter": "malfunction",
            "before": before_summary,
            "after": noise_text
        })
        
    # 4. Truncate title
    if len(corrupted_df) > 2:
        idx_to_truncate = 2
        paper_id = corrupted_df.loc[idx_to_truncate, "paper_id"]
        before_title = corrupted_df.loc[idx_to_truncate, "title"]
        truncated_title = before_title[:5] + "..." if len(before_title) > 5 else before_title
        corrupted_df.loc[idx_to_truncate, "title"] = truncated_title
        corruption_log.append({
            "paper_id": paper_id,
            "type": "truncate_title",
            "parameter": "len_5",
            "before": before_title,
            "after": truncated_title
        })
        
    # 5. Make published date stale (old date)
    if len(corrupted_df) > 3:
        idx_to_stale = 3
        paper_id = corrupted_df.loc[idx_to_stale, "paper_id"]
        before_pub = corrupted_df.loc[idx_to_stale, "published"]
        stale_date = "2000-01-01"
        corrupted_df.loc[idx_to_stale, "published"] = stale_date
        # Recalculate age_days for this row
        if "age_days" in corrupted_df.columns:
            corrupted_df.loc[idx_to_stale, "age_days"] = 9999
        corruption_log.append({
            "paper_id": paper_id,
            "type": "stale_date",
            "parameter": stale_date,
            "before": before_pub,
            "after": stale_date
        })
        
    # 6. Add duplicate rows
    if len(corrupted_df) > 4:
        idx_to_dup = 4
        dup_row = corrupted_df.iloc[[idx_to_dup]]
        corrupted_df = pd.concat([corrupted_df, dup_row], ignore_index=True)
        corruption_log.append({
            "paper_id": dup_row.iloc[0]["paper_id"],
            "type": "add_duplicate",
            "parameter": "row_4",
            "before": "single_row",
            "after": "duplicate_row"
        })
        
    # 7. Rebuild text_for_embedding
    corrupted_df["text_for_embedding"] = (
        "Title: " + corrupted_df["title"] + "\n" +
        "Authors: " + corrupted_df["authors_joined"] + "\n" +
        "Summary: " + corrupted_df["summary"]
    )
    
    # 8. Save corruption log
    out_p = Path(output_log_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(corruption_log, f, indent=2, ensure_ascii=False)
        
    return corrupted_df

