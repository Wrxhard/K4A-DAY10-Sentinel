from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed."""
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame([vars(r) for r in records])
    
    df['title'] = df['title'].str.strip()
    df['summary'] = df['summary'].str.strip()
    
    published_dt = pd.to_datetime(df['published'], errors='coerce')
    run_date_ts = pd.to_datetime(run_date).tz_localize(None)
    
    df['age_days'] = (run_date_ts - published_dt.dt.tz_localize(None)).dt.days
    
    df['authors_joined'] = df['authors'].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
    df['categories_joined'] = df['categories'].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
    df['summary_chars'] = df['summary'].str.len()
    
    df['text_for_embedding'] = (
        "Title: " + df['title'] + "\n" +
        "Authors: " + df['authors_joined'] + "\n" +
        "Published: " + df['published'] + "\n" +
        "Categories: " + df['categories_joined'] + "\n" +
        "Summary: " + df['summary']
    )
    
    df = df.drop_duplicates(subset=['paper_id'], keep='first')
    df = df[df['paper_id'].notna() & (df['paper_id'] != "")]
    
    df = df.sort_values('published', ascending=False).reset_index(drop=True)
    return df
