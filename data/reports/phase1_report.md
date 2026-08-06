# Phase 1 – Baseline Pipeline Report

> Generated: 2026-08-06 04:25 UTC

---

## 1. Source Summary

| Item | Value |
|---|---|
| API Source | Crossref REST API |
| Query | `N/A` |
| Filter | `N/A` |
| Items Returned (raw) | N/A |
| Fetched At | N/A |

---

## 2. Evaluation Metrics

| Metric | Value |
|---|---|
| Test Samples | 15 |
| Retrieval Hit Rate | 100.0% |
| Mean Token F1 | 41.8% |
| Judge Accuracy | 33.3% |
| Mean Judge Score | 2.33/5.00 |

### RAGAS Metrics

> Set RUN_RAGAS=1 to enable the slower Ragas pass.


---

## 3. Data Quality Gates

**Overall gate: ✅ PASS**

| Check | Status | Detail |
|---|---|---|
| row_count | ✅ PASS | value=24 |
| paper_id_not_null | ✅ PASS | null_count=0 |
| paper_id_unique | ✅ PASS | unique_count=24, duplicate_count=0 |
| title_not_null | ✅ PASS | null_count=0, blank_count=0 |
| summary_length | ✅ PASS | short_count=0, threshold_chars=20 |
| duplicate_rows | ✅ PASS | count=0 |
| freshness | ✅ PASS | stale_rows=0, mean_age_days=78.2, max_age_days=175, threshold_days=180 |

- Total rows: **24**
- Freshness threshold: **180 days**

---

## 4. Freshness

| Item | Value |
|---|---|
| Is Fresh | ✅ PASS |
| Latest Published | 2026-08-01 |
| Oldest Published | 2026-02-12 |
| Mean Age (days) | 78.2 |
| Median Age (days) | 66.0 |
| Max Age (days) | 175 |
| Stale Rows | 0 / 24 |
| Threshold | 180 days |
