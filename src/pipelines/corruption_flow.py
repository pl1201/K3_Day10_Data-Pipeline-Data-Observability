from __future__ import annotations


def main() -> None:
    """Xay dung corruption -> evaluate -> repair -> compare flow.

    Pseudo-code:
    1. Load baseline metrics va clean dataset.
    2. Tao corrupted dataframe.
    3. Save corrupted artifacts.
    4. Rebuild index va evaluate.
    5. Run quality checks/freshness tren corrupted data.
    6. Repair lai tu raw records.
    7. Evaluate repaired dataset.
    8. Tao comparison report.
    """
    from datetime import datetime, UTC
    import pandas as pd
    from core.config import load_settings
    from core.utils import read_json, write_json
    from ingestion.corruption import corrupt_clean_dataframe
    from ingestion.cleaning import build_clean_dataframe
    from ingestion.crossref import load_raw_records
    from retrieval.index import LocalEmbeddingIndex
    from evaluation.metrics import evaluate_pipeline
    from observability.quality import run_data_quality_checks, build_freshness_report
    from observability.reporting import generate_corruption_report
    
    settings = load_settings()
    run_date = datetime.now(UTC)
    
    print("[INFO] Corruption Flow: Loading baseline clean data...")
    # Load baseline clean data
    df_baseline = pd.read_csv(settings.paths.clean_csv)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    
    # 1. Corrupt data
    print("[INFO] Corruption Flow: Simulating data corruption...")
    df_corrupted = corrupt_clean_dataframe(df_baseline, settings.paths.corruption_log)
    
    # 2. Save corrupted artifacts
    print(f"[INFO] Saving corrupted data to {settings.paths.corrupted_clean_csv}...")
    df_corrupted.to_csv(settings.paths.corrupted_clean_csv, index=False)
    df_corrupted_json = df_corrupted.copy()
    write_json(settings.paths.corrupted_clean_json, df_corrupted_json.to_dict(orient="records"))
    
    # 3. Rebuild index and evaluate corrupted
    print("[INFO] Corruption Flow: Rebuilding corrupted embedding index...")
    corrupted_index = LocalEmbeddingIndex.build(df_corrupted, settings, settings.paths.corrupted_embeddings_json)
    
    print("[INFO] Corruption Flow: Evaluating corrupted pipeline...")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers
    )
    
    # Run quality/freshness checks on corrupted
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, "corrupted")
    corrupted_freshness = build_freshness_report(df_corrupted, settings, settings.paths.quality_dir / "corrupted_freshness.json")
    
    # 4. Repair: rebuild from raw snapshot
    print("[INFO] Corruption Flow: Rebuilding / Repairing from trusted raw snapshot...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(raw_records, run_date)
    
    # Save repaired artifacts
    print(f"[INFO] Saving repaired data to {settings.paths.repaired_clean_csv}...")
    df_repaired.to_csv(settings.paths.repaired_clean_csv, index=False)
    df_repaired_json = df_repaired.copy()
    write_json(settings.paths.repaired_clean_json, df_repaired_json.to_dict(orient="records"))
    
    # Rebuild repaired index and evaluate
    print("[INFO] Corruption Flow: Rebuilding repaired embedding index...")
    repaired_index = LocalEmbeddingIndex.build(df_repaired, settings, settings.paths.repaired_embeddings_json)
    
    print("[INFO] Corruption Flow: Evaluating repaired pipeline...")
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers
    )
    
    # Run quality/freshness checks on repaired
    repaired_quality = run_data_quality_checks(df_repaired, settings, "repaired")
    repaired_freshness = build_freshness_report(df_repaired, settings, settings.paths.quality_dir / "repaired_freshness.json")
    
    # 5. Generate Comparison Report
    print("[INFO] Corruption Flow: Generating comparison report...")
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness
    )
    
    print("[SUCCESS] Corruption and recovery flow completed successfully.")

