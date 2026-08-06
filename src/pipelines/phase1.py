from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from core.config import load_settings
from core.utils import write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Baseline pipeline end-to-end:
    raw → clean → index → test set → evaluate → quality/freshness → report → (demo agent).
    """

    # ── Bước 1: Load settings (đọc .env, cấu hình paths) ────────────────────
    print("[1/10] Loading settings...")
    settings = load_settings()

    # ── Bước 2: Fetch hoặc load raw records từ Crossref ─────────────────────
    # Nếu đã có file raw và không cần refresh → đọc từ file (tiết kiệm API call)
    print("[2/10] Fetching / loading raw records...")
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        # Gọi Crossref API, lưu raw response, parse thành list[PaperRecord]
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(settings.paths.raw_records_json)
    print(f"       -> {len(records)} raw records")

    # ── Bước 3 & 4: Clean data và lưu CSV/JSON ──────────────────────────────
    print("[3/10] Cleaning data...")
    run_date = datetime.now(UTC)
    df = build_clean_dataframe(records, run_date=run_date)
    print(f"       -> {len(df)} clean records (dropped {len(records) - len(df)})")

    print("[4/10] Saving clean artifacts...")
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.paths.clean_csv, index=False)
    write_json(settings.paths.clean_json, json.loads(df.to_json(orient="records", force_ascii=False)))
    print(f"       -> {settings.paths.clean_csv}")

    # ── Bước 5: Build Chroma index (MiniLM embeddings) ──────────────────────
    # LocalEmbeddingIndex.build() sẽ:
    #   - Tạo collection "papers-baseline" trong ChromaDB
    #   - Lưu manifest tại data/embeddings/papers_embeddings.json
    print("[5/10] Building embedding index (papers-baseline)...")
    index = LocalEmbeddingIndex.build(
        df=df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(f"       -> Collection: {index.collection_name}, docs: {len(index.documents)}")

    # ── Bước 6: Tạo hoặc load evaluation test set ───────────────────────────
    print("[6/10] Building / loading test set...")
    settings.paths.eval_testset.parent.mkdir(parents=True, exist_ok=True)
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        test_cases = build_test_set(df, output_path=settings.paths.eval_testset)
        print(f"       -> Created {len(test_cases)} test questions")
    else:
        with open(settings.paths.eval_testset, encoding="utf-8") as f:
            test_cases = json.load(f)
        print(f"       -> Loaded {len(test_cases)} existing test questions")

    # ── Bước 7: Evaluate (retrieval hit-rate, token F1, judge score) ─────────
    print("[7/10] Evaluating pipeline...")
    settings.paths.baseline_metrics.parent.mkdir(parents=True, exist_ok=True)
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    m = bundle.summary
    print(f"       -> retrieval_hit_rate={m['retrieval_hit_rate']:.2f}, "
          f"mean_token_f1={m['mean_token_f1']:.2f}, "
          f"judge_accuracy={m['judge_accuracy']:.2f}")

    # ── Bước 8: Data quality checks + freshness report ──────────────────────
    print("[8/10] Running quality checks & freshness report...")
    settings.paths.quality_dir.mkdir(parents=True, exist_ok=True)
    quality = run_data_quality_checks(df, settings, report_name="baseline")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    print(f"       -> is_fresh={freshness.get('is_fresh')}, stale_rows={freshness.get('stale_rows')}")

    # ── Bước 9: Tạo markdown report tổng kết ────────────────────────────────
    print("[9/10] Generating phase 1 report...")
    settings.paths.baseline_report.parent.mkdir(parents=True, exist_ok=True)
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "raw_count": len(records),
        "clean_count": len(df),
        "dropped_count": len(records) - len(df),
        "run_date": run_date.isoformat(),
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )
    print(f"       -> {settings.paths.baseline_report}")

    # ── Bước 10 (bonus): Demo agent trên vài câu hỏi mẫu ───────────────────
    print("[10/10] Running agent demo (optional)...")
    try:
        agent = build_agent(settings=settings, index=index)
        sample_questions = [
            "What is agentic retrieval augmented generation?",
            "List the authors of the most recent paper in the corpus.",
            "What categories does the paper about large language models belong to?",
        ]
        demo_answers = []
        for q in sample_questions:
            ans = run_agent_question(agent, q)
            demo_answers.append({"question": q, "answer": ans})
            print(f"       Q: {q}\n       A: {ans[:120]}...")

        settings.paths.demo_answers.parent.mkdir(parents=True, exist_ok=True)
        write_json(settings.paths.demo_answers, demo_answers)
    except Exception as exc:
        print(f"       [WARN] Agent demo skipped: {exc}")

    print("\n[SUCCESS] Phase 1 baseline complete!")
    print(f"   Metrics : {settings.paths.baseline_metrics}")
    print(f"   Answers : {settings.paths.baseline_answers}")
    print(f"   Report  : {settings.paths.baseline_report}")


