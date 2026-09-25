from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import requests
from core.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    records = []
    items = payload.get("message", {}).get("items", [])
    for item in items:
        doi = item.get("DOI", "").strip()
        if not doi:
            continue

        title_list = item.get("title", [])
        title = title_list[0] if title_list else ""
        title = " ".join(title.split())

        abstract = item.get("abstract", "")
        summary = re.sub(r'<[^>]+>', '', abstract).strip()

        authors = []
        for a in item.get("author", []):
            given = a.get("given", "").strip()
            family = a.get("family", "").strip()
            name = f"{given} {family}".strip()
            if name:
                authors.append(name)

        categories = item.get("subject", [])
        primary_category = categories[0] if categories else ""

        pub_date = "1970-01-01"
        if "published" in item and "date-parts" in item["published"]:
            dp = item["published"]["date-parts"][0]
            if len(dp) >= 3:
                pub_date = date(dp[0], dp[1], dp[2]).isoformat()
            elif len(dp) == 2:
                pub_date = date(dp[0], dp[1], 1).isoformat()
            elif len(dp) == 1:
                pub_date = date(dp[0], 1, 1).isoformat()

        updated = item.get("created", {}).get("date-time", pub_date)

        abs_url = item.get("URL", f"https://doi.org/{doi}")
        pdf_url = ""
        links = item.get("link", [])
        for link in links:
            if link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", "")
                break

        records.append(PaperRecord(
            paper_id=doi,
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=primary_category,
            published=pub_date,
            updated=updated,
            abs_url=abs_url,
            pdf_url=pdf_url,
            comment=""
        ))
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi source API, luu raw response, parse thanh records voi Dual-Mode."""
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results
    }

    payload = None
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()

        settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
        with open(settings.paths.raw_api_response, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    except (requests.RequestException, ValueError) as e:
        logger.warning(f"Crossref API error ({e}). Falling back to offline snapshot.")
        if settings.paths.raw_api_response.exists():
            with open(settings.paths.raw_api_response, "r", encoding="utf-8") as f:
                payload = json.load(f)
        else:
            raise RuntimeError(f"API failed and offline snapshot not found at {settings.paths.raw_api_response}")

    records = parse_crossref_payload(payload)

    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.paths.raw_records_json, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh PaperRecord."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [PaperRecord(**r) for r in data]
