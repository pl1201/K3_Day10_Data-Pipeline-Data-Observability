from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import re
import time

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _parse_date_parts(date_parts: list) -> str:
    """Luôn trả về YYYY-MM-DD dù date-parts chỉ có [year] hoặc [year, month]."""
    if not date_parts:
        return ""
    parts = date_parts[0]          # [[2024]] → [2024]
    year  = str(parts[0]) if len(parts) > 0 else "1970"
    month = str(parts[1]).zfill(2) if len(parts) > 1 else "01"
    day   = str(parts[2]).zfill(2) if len(parts) > 2 else "01"
    return f"{year}-{month}-{day}"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    records = []
    items = payload.get("message", {}).get("items", [])
    
    for item in items:
        paper_id = item.get("DOI", "").strip().lower()
        if not paper_id:
            continue
            
        raw_title = item.get("title", [])
        title = normalize_whitespace(raw_title[0]) if raw_title else ""
        if not title:
            continue
            
        raw_abstract = item.get("abstract", "") or ""
        summary = normalize_whitespace(re.sub(r"<[^>]+>", " ", raw_abstract))
        
        authors = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in item.get("author", [])
            if a.get("given") or a.get("family")
        ]
        
        categories = item.get("subject", [])
        primary_category = categories[0] if categories else ""
        
        published = _parse_date_parts(item.get("published", {}).get("date-parts", []))
        updated = _parse_date_parts(item.get("indexed", item.get("deposited", {})).get("date-parts", []))
        
        abs_url = item.get("URL", "")
        
        links = item.get("link", [])
        pdf_url = next(
            (l["URL"] for l in links if l.get("content-type") == "application/pdf"),
            links[0]["URL"] if links else ""
        )
        
        try:
            comment = item.get("license", [])[0].get("URL", "")
        except (IndexError, AttributeError):
            comment = ""
            
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )
        
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    if not settings.refresh_source and settings.paths.raw_records_json.exists():
        return load_raw_records(settings.paths.raw_records_json)

    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "mailto": "student@lab.local",
    }
    
    response = None
    for attempt in range(3):
        response = requests.get(url, params=params, timeout=30)
        if response.status_code in (429, 503):
            time.sleep(5 * (attempt + 1))
            continue
        response.raise_for_status()
        break
        
    if not response:
        raise RuntimeError("Failed to fetch from Crossref after retries.")

    payload = response.json()
    
    payload["_fetch_metadata"] = {
        "fetched_at": datetime.now(UTC).isoformat(),
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows_requested": settings.max_results,
        "items_returned": len(payload.get("message", {}).get("items", [])),
        "source_api": settings.source_api,
    }
    
    write_json(settings.paths.raw_api_response, payload)

    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [dataclasses.asdict(r) for r in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    items = read_json(path)
    records = []
    for item in items:
        try:
            records.append(PaperRecord(**item))
        except TypeError as e:
            print(f"[WARN] load_raw_records: skip malformed record - {e}")
    return records
