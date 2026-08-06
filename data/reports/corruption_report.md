# Data Corruption & Recovery Comparison Report

## 1. Metric Comparison

| Metric | Baseline | Corrupted | Repaired | Delta (Repaired - Corrupted) |
|---|---|---|---|---|
| **Retrieval Hit Rate** | 100.0% | 80.0% | 100.0% | +20.0% |
| **Mean Token F1** | 41.8% | 27.1% | 41.8% | +14.7% |
| **Judge Accuracy** | 33.3% | 20.0% | 33.3% | +13.3% |
| **Mean Judge Score** | 2.33/5.0 | 1.80/5.0 | 2.33/5.0 | +0.53 |

## 2. Observability & Data Quality Comparison

### Corrupted State
- **Success Gate Status**: FAIL
- **Total Rows**: 22
- **Duplicates**: 1
- **Missing/Blank Titles**: 0
- **Short Summaries**: 1
- **Freshness Stale Rows**: 1 (Is Fresh: NO)

### Repaired State
- **Success Gate Status**: PASS
- **Total Rows**: 24
- **Duplicates**: 0
- **Missing/Blank Titles**: 0
- **Short Summaries**: 0
- **Freshness Stale Rows**: 0 (Is Fresh: YES)

## 3. Analysis & Key Takeaways
- **Data corruption** significantly degrades the RAG agent's retrieval accuracy and answer quality (e.g. empty or noisy summaries cause bad hits/misses).
- **Data observability tools** successfully capture these failures through quality checks and freshness metrics.
- **Repairing the pipeline** from trusted raw snapshots restores the vector index accuracy and recovers the agent's performance.
