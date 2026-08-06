from __future__ import annotations


def main() -> None:
    """Xay dung baseline pipeline end-to-end.

    Pseudo-code:
    1. Load settings.
    2. Load hoac fetch raw records.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Build Chroma index.
    6. Tao hoac load evaluation set.
    7. Evaluate.
    8. Run quality checks va freshness report.
    9. Tao markdown report.
    10. Co the demo agent tren vai sample question.
    """
    from datetime import datetime, UTC
    from core.config import load_settings
    from core.utils import write_json, read_json
    from ingestion.crossref import fetch_source_records
    from ingestion.cleaning import build_clean_dataframe
    from retrieval.index import LocalEmbeddingIndex
    from evaluation.testset import build_test_set
    from evaluation.metrics import evaluate_pipeline
    from observability.quality import run_data_quality_checks, build_freshness_report
    from observability.reporting import generate_phase1_report
    import pandas as pd
    import json
    
    settings = load_settings()
    run_date = datetime.now(UTC)
    
    print("[INFO] Phase 1: Fetching raw records...")
    records = fetch_source_records(settings)
    
    print(f"[INFO] Phase 1: Loaded {len(records)} raw records. Cleaning...")
    df_clean = build_clean_dataframe(records, run_date)
    
    # Save clean CSV/JSON
    print(f"[INFO] Saving cleaned papers to {settings.paths.clean_csv}...")
    df_clean.to_csv(settings.paths.clean_csv, index=False)
    # Convert list fields to lists for JSON serialization
    df_clean_json = df_clean.copy()
    write_json(settings.paths.clean_json, df_clean_json.to_dict(orient="records"))
    
    print("[INFO] Phase 1: Building local embedding index...")
    index = LocalEmbeddingIndex.build(df_clean, settings, settings.paths.embeddings_json)
    
    print("[INFO] Phase 1: Building test set...")
    build_test_set(df_clean, settings.paths.eval_testset)
    
    print("[INFO] Phase 1: Evaluating baseline pipeline...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers
    )
    
    print("[INFO] Phase 1: Running data quality checks & freshness...")
    quality = run_data_quality_checks(df_clean, settings, "baseline")
    freshness = build_freshness_report(df_clean, settings, settings.paths.freshness_report)
    
    print("[INFO] Phase 1: Generating final Markdown report...")
    # Load metadata from crossref_response
    raw_response = read_json(settings.paths.raw_api_response)
    source_summary = raw_response.get("_fetch_metadata", {})
    
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness
    )
    
    print("[SUCCESS] Phase 1 pipeline completed successfully.")

