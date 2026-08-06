from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed.

    Pseudo-code:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days.
    4. Tao cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Drop duplicates va filter row xau.
    6. Sort dataframe va return.
    """
    cleaned_records = []
    
    for r in records:
        # Normalize fields
        title = r.title.strip() if r.title else ""
        summary = r.summary.strip() if r.summary else ""
        
        # Check constraints (must have valid paper_id and non-blank title)
        if not r.paper_id or not title:
            continue
            
        authors_joined = ", ".join([a.strip() for a in r.authors if a.strip()])
        categories_joined = ", ".join([c.strip() for c in r.categories if c.strip()])
        summary_chars = len(summary)
        
        # Parse published/updated dates
        published_dt = None
        if r.published:
            try:
                published_dt = datetime.strptime(r.published, "%Y-%m-%d")
            except ValueError:
                pass
                
        updated_dt = None
        if r.updated:
            try:
                updated_dt = datetime.strptime(r.updated, "%Y-%m-%d")
            except ValueError:
                pass
                
        # Calculate age_days
        age_days = None
        if published_dt:
            # Normalize run_date and published_dt to offset-naive comparison
            rd = run_date.replace(tzinfo=None)
            pd_naive = published_dt.replace(tzinfo=None)
            age_days = (rd - pd_naive).days
            
        text_for_embedding = f"Title: {title}\nAuthors: {authors_joined}\nSummary: {summary}"
        
        cleaned_records.append({
            "paper_id": r.paper_id,
            "title": title,
            "summary": summary,
            "authors": r.authors,
            "categories": r.categories,
            "primary_category": r.primary_category,
            "published": r.published,
            "updated": r.updated,
            "abs_url": r.abs_url,
            "pdf_url": r.pdf_url,
            "comment": r.comment,
            "authors_joined": authors_joined,
            "categories_joined": categories_joined,
            "summary_chars": summary_chars,
            "age_days": age_days,
            "text_for_embedding": text_for_embedding,
        })
        
    df = pd.DataFrame(cleaned_records)
    if df.empty:
        return df
        
    # Drop duplicates by paper_id
    df = df.drop_duplicates(subset=["paper_id"])
    
    # Sort dataframe by published date descending (if exists) or paper_id
    if "published" in df.columns:
        df = df.sort_values(by="published", ascending=False)
        
    return df

