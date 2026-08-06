# Data Corruption & Recovery – Comparison Report

> Generated: 2026-08-06 04:25 UTC

---

## 1. Metrics Comparison (Baseline → Corrupted → Repaired)

| Metric | Baseline | Corrupted | Repaired | Δ Corrupt vs Base | Δ Repair vs Corrupt |
|---|---|---|---|---|---|
| **Retrieval Hit Rate** | 100.0% | 80.0% | 100.0% | -20.0% | +20.0% |
| **Mean Token F1** | 41.8% | 27.1% | 41.8% | -14.7% | +14.7% |
| **Judge Accuracy** | 33.3% | 20.0% | 33.3% | -13.3% | +13.3% |
| **Mean Judge Score** | 2.33/5.00 | 1.80/5.00 | 2.33/5.00 | -0.53 | +0.53 |

---

## 2. Data Quality & Freshness Comparison

### Corrupted State

| Check | Value |
|---|---|
| Gate Status | ❌ FAIL |
| Total Rows | 22 |
| Duplicates | 1 |
| Missing Paper IDs | 0 |
| Missing/Blank Titles | 0 |
| Short Summaries (<20 chars) | 1 |
| Stale Rows | 1 |
| Is Fresh | ❌ FAIL |
| Latest Published | 2026-07-03 |
| Oldest Published | 2000-01-01 |


### Repaired State

| Check | Value |
|---|---|
| Gate Status | ✅ PASS |
| Total Rows | 24 |
| Duplicates | 0 |
| Missing Paper IDs | 0 |
| Missing/Blank Titles | 0 |
| Short Summaries (<20 chars) | 0 |
| Stale Rows | 0 |
| Is Fresh | ✅ PASS |
| Latest Published | 2026-08-01 |
| Oldest Published | 2026-02-12 |


---

## 3. Signal Change Analysis

**Signals that changed between corrupted → repaired:**

- **duplicate_count**: corrupted=1 → repaired=0
- **short_summaries**: corrupted=1 → repaired=0
- **stale_rows**: corrupted=1 → repaired=0
- **total_rows**: corrupted=22 → repaired=24

**Signals unchanged:**

- **missing_titles**: 0 (unchanged)

---

## 4. Recovery Status

- ✅ **Retrieval Hit Rate**: fully recovered to baseline (100.0%)
- ✅ **Mean Token F1**: fully recovered to baseline (41.8%)
- ✅ **Judge Accuracy**: fully recovered to baseline (33.3%)
- ✅ **Quality Gate**: PASS
- ✅ **Freshness**: Fresh

---

## 5. Key Takeaways

- **Data corruption** directly degrades RAG agent performance: retrieval hit rate dropped from 100.0% to 80.0%, mean token F1 from 41.8% to 27.1%.
- **Observability tools** successfully detected corruption through quality gate failures (duplicates=1, short summaries=1, stale rows=1).
- **Repair from trusted raw snapshot** restored metrics to baseline levels, proving the pipeline can self-heal when given clean source data.
