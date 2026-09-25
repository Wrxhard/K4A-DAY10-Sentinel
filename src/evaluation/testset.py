from __future__ import annotations

import json
from typing import Any

import pandas as pd


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Tao bo evaluation set tu cleaned dataframe."""
    if df.empty:
        return []
        
    questions = []
    
    samples = df.head(3).to_dict('records')
    idx = 1
    
    for row in samples:
        # summary
        questions.append({
            "id": f"eval_{idx:03d}",
            "question_type": "summary",
            "question": f"What is the summary of the paper '{row['title']}'?",
            "ground_truth": row['summary'],
            "ground_truth_doc_ids": [row['paper_id']]
        })
        idx += 1
        
        # authors
        questions.append({
            "id": f"eval_{idx:03d}",
            "question_type": "authors",
            "question": f"Who are the authors of the paper '{row['title']}'?",
            "ground_truth": row['authors_joined'],
            "ground_truth_doc_ids": [row['paper_id']]
        })
        idx += 1
        
        # date
        questions.append({
            "id": f"eval_{idx:03d}",
            "question_type": "date",
            "question": f"When was the paper '{row['title']}' published?",
            "ground_truth": str(row['published']),
            "ground_truth_doc_ids": [row['paper_id']]
        })
        idx += 1
        
        # categories
        questions.append({
            "id": f"eval_{idx:03d}",
            "question_type": "categories",
            "question": f"What are the categories of the paper '{row['title']}'?",
            "ground_truth": row['categories_joined'],
            "ground_truth_doc_ids": [row['paper_id']]
        })
        idx += 1
        
    questions = questions[:10]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
        
    return questions

