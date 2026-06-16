"""
No-key global news ingestion through the GDELT DOC API.

GDELT gives the project a free live-news path when NewsAPI is unavailable,
rate-limited, or not configured. The records are normalized into the same
NewsAPI-like shape used by Stage 1.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class GDELTNewsIngestor:
    """Fetch and store live article lists from GDELT without an API key."""

    ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"
    REQUEST_TIMEOUT_SECONDS = 12

    def __init__(self, data_dir: str = "data/raw/news", session: Any | None = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session = session or requests
        self.last_failure_reason = ""

    def fetch_news(
        self,
        query: str = "geopolitics OR international relations OR diplomacy",
        days_back: int = 3,
        language: str = "en",
        max_articles: int = 100,
        **_kwargs,
    ) -> List[Dict]:
        """Fetch GDELT article-list results and normalize them."""
        self.last_failure_reason = ""
        max_articles = max(1, min(int(max_articles), 250))
        days_back = max(1, min(int(days_back or 1), 31))

        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": max_articles,
            "timespan": f"{days_back}d",
            "sort": "datedesc",
        }
        if language:
            params["sourcelang"] = language

        try:
            response = self.session.get(
                self.ENDPOINT,
                params=params,
                timeout=self.REQUEST_TIMEOUT_SECONDS,
                headers={"User-Agent": "gns-gdelt-ingestor/0.1"},
            )
            logger.info(
                "GDELT response | query=%s | days_back=%s | max_articles=%s | status_code=%s",
                query,
                days_back,
                max_articles,
                getattr(response, "status_code", ""),
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code is None:
                status_code = getattr(locals().get("response", None), "status_code", None)
            self.last_failure_reason = (
                f"GDELT HTTP {status_code}" if status_code else f"GDELT request failed: {exc}"
            )
            logger.warning("GDELT fetch failed | query=%s | reason=%s", query, self.last_failure_reason)
            return []

        articles = payload.get("articles", []) if isinstance(payload, dict) else []
        if not isinstance(articles, list):
            self.last_failure_reason = "GDELT response did not contain an article list."
            return []

        normalized = [self._normalize_article(item) for item in articles if isinstance(item, dict)]
        normalized = [item for item in normalized if item.get("title") or item.get("url")]
        if not normalized:
            self.last_failure_reason = "GDELT returned 0 usable articles."
        return normalized[:max_articles]

    def save_articles(self, articles: List[Dict], filename: Optional[str] = None) -> str:
        """Save normalized GDELT articles to the shared raw-news format."""
        if not articles:
            logger.warning("No GDELT articles to save")
            return ""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gdelt_news_{timestamp}.json"

        filepath = self.data_dir / filename
        with open(filepath, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "fetched_at": datetime.now().isoformat(),
                    "source_api": "gdelt_doc",
                    "total_articles": len(articles),
                    "articles": articles,
                },
                handle,
                indent=2,
                ensure_ascii=False,
            )

        logger.info("Saved %s GDELT articles to %s", len(articles), filepath)
        return str(filepath)

    def _normalize_article(self, item: Dict[str, Any]) -> Dict:
        domain = str(item.get("domain") or "").strip()
        source_name = domain or str(item.get("source") or "GDELT").strip() or "GDELT"
        seen_date = self._normalize_seen_date(item.get("seendate") or item.get("seenDate"))
        social_image = item.get("socialimage") or item.get("image") or ""
        source_country = item.get("sourcecountry") or item.get("sourceCountry") or ""
        source_language = item.get("language") or item.get("sourcelang") or ""

        return {
            "title": str(item.get("title") or "").strip(),
            "description": self._build_description(item, source_country=source_country, source_language=source_language),
            "content": "",
            "url": str(item.get("url") or "").strip(),
            "source": {"name": source_name},
            "author": "GDELT",
            "publishedAt": seen_date,
            "urlToImage": social_image,
            "source_api": "gdelt_doc",
            "domain": domain,
            "source_country": source_country,
            "source_language": source_language,
        }

    def _build_description(self, item: Dict[str, Any], *, source_country: Any, source_language: Any) -> str:
        title = str(item.get("title") or "").strip()
        descriptors = []
        if source_country:
            descriptors.append(f"source country: {source_country}")
        if source_language:
            descriptors.append(f"language: {source_language}")
        suffix = f" ({'; '.join(descriptors)})" if descriptors else ""
        return f"GDELT global coverage item{suffix}: {title}" if title else f"GDELT global coverage item{suffix}."

    def _normalize_seen_date(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        if raw.endswith("Z") or "T" in raw:
            return raw
        for fmt in ("%Y%m%d%H%M%S", "%Y%m%d%H%M"):
            try:
                return datetime.strptime(raw, fmt).isoformat() + "Z"
            except ValueError:
                continue
        return raw
