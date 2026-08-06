from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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


REQUIRED_CLEAN_COLUMNS = {
    "paper_id",
    "title",
    "summary",
    "published",
    "authors_joined",
    "categories_joined",
    "age_days",
    "text_for_embedding",
}
REQUIRED_TEST_CASE_FIELDS = {
    "id",
    "question_type",
    "question",
    "ground_truth",
    "ground_truth_doc_ids",
}


class PipelineContractError(RuntimeError):
    """Raised when a checkpoint artifact violates the integration contract."""


def validate_raw_records(records: list[Any]) -> None:
    if not records:
        raise PipelineContractError("CP1 raw gate failed: no source records were loaded.")
    missing_ids = [index for index, record in enumerate(records) if not getattr(record, "paper_id", "")]
    if missing_ids:
        raise PipelineContractError(
            f"CP1 raw gate failed: {len(missing_ids)} records have no paper_id; "
            f"first indexes={missing_ids[:5]}."
        )


def validate_clean_dataframe(df: Any) -> None:
    if df is None or df.empty:
        raise PipelineContractError("CP1 clean gate failed: cleaned dataframe is empty.")
    missing_columns = sorted(REQUIRED_CLEAN_COLUMNS.difference(df.columns))
    if missing_columns:
        raise PipelineContractError(f"CP1 clean gate failed: missing columns {missing_columns}.")

    paper_ids = df["paper_id"].fillna("").astype(str).str.strip()
    problems = []
    blank_count = int((paper_ids == "").sum())
    duplicate_count = int(paper_ids.duplicated().sum())
    empty_text_count = int(df["text_for_embedding"].fillna("").astype(str).str.strip().eq("").sum())
    if blank_count:
        problems.append(f"blank paper_id={blank_count}")
    if duplicate_count:
        problems.append(f"duplicate paper_id={duplicate_count}")
    if empty_text_count:
        problems.append(f"blank text_for_embedding={empty_text_count}")
    if problems:
        raise PipelineContractError(f"CP1 clean gate failed: {', '.join(problems)}.")


def validate_test_set(test_set: Any, clean_paper_ids: set[str]) -> None:
    if not isinstance(test_set, list) or not test_set:
        raise PipelineContractError("CP2 test-set gate failed: test set is empty or is not a list.")

    seen_ids: set[str] = set()
    unknown_doc_ids: set[str] = set()
    for index, item in enumerate(test_set):
        if not isinstance(item, dict):
            raise PipelineContractError(f"CP2 test-set gate failed: item {index} is not an object.")
        missing_fields = sorted(REQUIRED_TEST_CASE_FIELDS.difference(item))
        if missing_fields:
            raise PipelineContractError(
                f"CP2 test-set gate failed: item {index} is missing {missing_fields}."
            )
        case_id = str(item["id"]).strip()
        if not case_id or case_id in seen_ids:
            detail = "blank" if not case_id else f"duplicate {case_id!r}"
            raise PipelineContractError(f"CP2 test-set gate failed: {detail} id at item {index}.")
        seen_ids.add(case_id)

        doc_ids = item["ground_truth_doc_ids"]
        if not isinstance(doc_ids, list) or not doc_ids:
            raise PipelineContractError(
                f"CP2 test-set gate failed: {case_id!r} has no ground_truth_doc_ids."
            )
        unknown_doc_ids.update(str(doc_id) for doc_id in doc_ids if str(doc_id) not in clean_paper_ids)

    if unknown_doc_ids:
        raise PipelineContractError(
            f"CP2 test-set gate failed: {len(unknown_doc_ids)} document IDs are absent from clean data; "
            f"first IDs={sorted(unknown_doc_ids)[:5]}."
        )


def validate_embedding_manifest(
    manifest: Any,
    expected_collection: str,
    expected_document_count: int,
) -> None:
    if not isinstance(manifest, dict):
        raise PipelineContractError("CP2 index gate failed: embedding manifest is not an object.")
    if manifest.get("collection_name") != expected_collection:
        raise PipelineContractError(
            f"CP2 index gate failed: expected collection {expected_collection!r}, "
            f"got {manifest.get('collection_name')!r}."
        )
    documents = manifest.get("documents")
    if not isinstance(documents, list) or len(documents) != expected_document_count:
        actual_count = len(documents) if isinstance(documents, list) else "invalid"
        raise PipelineContractError(
            "CP2 index gate failed: manifest document count does not match clean data "
            f"(expected={expected_document_count}, actual={actual_count})."
        )


def smoke_test_index(index: Any, df: Any, top_k: int) -> None:
    sample = df.iloc[0]
    paper_id = str(sample["paper_id"])
    if index.lookup(paper_id) is None:
        raise PipelineContractError(f"CP2 index gate failed: exact lookup missed {paper_id!r}.")
    results = index.search(str(sample["title"]), top_k=min(top_k, len(df)))
    if not results:
        raise PipelineContractError("CP2 index gate failed: semantic search returned no results.")


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
    validate_raw_records(records)
    print(f"       -> {len(records)} raw records")

    # ── Bước 3 & 4: Clean data và lưu CSV/JSON ──────────────────────────────
    print("[3/10] Cleaning data...")
    run_date = datetime.now(UTC)
    df = build_clean_dataframe(records, run_date=run_date)
    validate_clean_dataframe(df)
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
    with open(settings.paths.embeddings_json, encoding="utf-8") as f:
        embedding_manifest = json.load(f)
    validate_embedding_manifest(embedding_manifest, settings.baseline_collection_name, len(df))
    smoke_test_index(index, df, settings.top_k)
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
    validate_test_set(test_cases, set(df["paper_id"].astype(str)))

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


