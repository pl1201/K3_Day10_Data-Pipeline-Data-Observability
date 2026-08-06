from __future__ import annotations

from typing import Any

import pandas as pd


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Tao bo evaluation set tu cleaned dataframe.

    Pseudo-code:
    1. Kiem tra so luong document toi thieu.
    2. Chon mot so paper dai dien.
    3. Tao nhieu loai cau hoi:
       - summary
       - authors
       - date
       - categories
    4. Moi row can co:
       - id
       - question_type
       - question
       - ground_truth
       - ground_truth_doc_ids
    5. Ghi file JSON vao output_path.
    """
    import json
    from pathlib import Path
    
    if len(df) < 5:
        print(f"[WARN] build_test_set: df size ({len(df)}) is small, using all available records.")
        sample_df = df
    else:
        # Choose 5 representative papers (e.g. head, tail, and middle rows)
        indices = [0, len(df)//4, len(df)//2, (3*len(df))//4, len(df)-1]
        sample_df = df.iloc[list(set(indices))]
        
    test_set = []
    q_counter = 1
    
    for _, row in sample_df.iterrows():
        title = row["title"]
        paper_id = row["paper_id"]
        
        # 1. Summary Question
        if row["summary"]:
            test_set.append({
                "id": f"q_{q_counter}",
                "question_type": "summary",
                "question": f"What is the main finding or summary of the paper titled '{title}'?",
                "ground_truth": row["summary"],
                "ground_truth_doc_ids": [paper_id]
            })
            q_counter += 1
            
        # 2. Authors Question
        if row["authors_joined"]:
            test_set.append({
                "id": f"q_{q_counter}",
                "question_type": "authors",
                "question": f"Who wrote the paper '{title}'?",
                "ground_truth": row["authors_joined"],
                "ground_truth_doc_ids": [paper_id]
            })
            q_counter += 1
            
        # 3. Date Question
        if row["published"]:
            test_set.append({
                "id": f"q_{q_counter}",
                "question_type": "date",
                "question": f"When was the paper '{title}' published?",
                "ground_truth": row["published"],
                "ground_truth_doc_ids": [paper_id]
            })
            q_counter += 1
            
        # 4. Categories Question
        if row["categories_joined"]:
            test_set.append({
                "id": f"q_{q_counter}",
                "question_type": "categories",
                "question": f"What subjects or categories does the paper '{title}' belong to?",
                "ground_truth": row["categories_joined"],
                "ground_truth_doc_ids": [paper_id]
            })
            q_counter += 1
            
    # Save JSON
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2, ensure_ascii=False)
        
    return test_set

