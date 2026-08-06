from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pytest

from pipelines.phase1 import (
    PipelineContractError,
    validate_clean_dataframe,
    validate_embedding_manifest,
    validate_raw_records,
    validate_test_set,
)


@dataclass
class RawRecord:
    paper_id: str


def clean_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "paper_id": "paper-1",
                "title": "A paper",
                "summary": "Summary",
                "published": "2026-01-01",
                "authors_joined": "Author",
                "categories_joined": "AI",
                "age_days": 1,
                "text_for_embedding": "Title: A paper",
            }
        ]
    )


def test_cp1_contracts_accept_valid_raw_and_clean_data() -> None:
    validate_raw_records([RawRecord("paper-1")])
    validate_clean_dataframe(clean_dataframe())


def test_clean_gate_rejects_duplicate_ids() -> None:
    df = pd.concat([clean_dataframe(), clean_dataframe()], ignore_index=True)
    with pytest.raises(PipelineContractError, match="duplicate paper_id=1"):
        validate_clean_dataframe(df)


def test_test_set_gate_rejects_unknown_document_id() -> None:
    test_set = [
        {
            "id": "q-1",
            "question_type": "summary",
            "question": "What is it about?",
            "ground_truth": "Summary",
            "ground_truth_doc_ids": ["missing-paper"],
        }
    ]
    with pytest.raises(PipelineContractError, match="absent from clean data"):
        validate_test_set(test_set, {"paper-1"})


def test_manifest_gate_checks_collection_and_document_count() -> None:
    manifest = {"collection_name": "papers-baseline", "documents": [{"paper_id": "paper-1"}]}
    validate_embedding_manifest(manifest, "papers-baseline", 1)

    with pytest.raises(PipelineContractError, match="document count"):
        validate_embedding_manifest(manifest, "papers-baseline", 2)
