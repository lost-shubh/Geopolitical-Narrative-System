"""
No-key RSS news ingestion for live fallback.

This keeps Stage 1 useful when paid/API-key sources are unavailable and a
free endpoint is temporarily rate-limited.
"""

from __future__ import annotations

import html
import json
import logging
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlparse
from xml.etree import ElementTree

import requests

logger = logging.getLogger(__name__)

TAG_RE = re.compile(r"<[^>]+>")


class RSSNewsIngestor:
    """Fetch and store article records from a no-key RSS search feed."""

    REQUEST_TIMEOUT_SECONDS = 12
    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    def __init__(self, data_dir: str = "data/raw/news", session: Any | None = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session = session or requests
        self.last_failure_reason = ""

    def fetch_news(
        self,
        query: str = "geopolitics OR international relations OR diplomacy",
        max_articles: int = 100,
        **_kwargs,
    ) -> List[Dict]:
        """Fetch RSS search results and normalize them."""
        self.last_failure_reason = ""
        max_articles = max(1, min(int(max_articles), 100))
        url = self.GOOGLE_NEWS_RSS.format(query=quote_plus(query))

        try:
            response = self.session.get(
                url,
                timeout=self.REQUEST_TIMEOUT_SECONDS,
                headers={"User-Agent": "gns-rss-ingestor/0.1"},
            )
            logger.info(
                "RSS response | query=%s | max_articles=%s | status_code=%s",
                query,
                max_articles,
                getattr(response, "status_code", ""),
            )
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
        except Exception as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code is None:
                status_code = getattr(locals().get("response", None), "status_code", None)
            self.last_failure_reason = f"RSS HTTP {status_code}" if status_code else f"RSS request failed: {exc}"
            logger.warning("RSS fetch failed | query=%s | reason=%s", query, self.last_failure_reason)
            return []

        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else root.findall(".//item")
        articles = [self._normalize_item(item) for item in items[:max_articles]]
        articles = [item for item in articles if item.get("title") or item.get("url")]
        if not articles:
            self.last_failure_reason = "RSS feed returned 0 usable articles."
        return articles

    def save_articles(self, articles: List[Dict], filename: Optional[str] = None) -> str:
        """Save normalized RSS articles to the shared raw-news format."""
        if not articles:
            logger.warning("No RSS articles to save")
            return ""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rss_news_{timestamp}.json"

        filepath = self.data_dir / filename
        with open(filepath, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "fetched_at": datetime.now().isoformat(),
                    "source_api": "rss_search",
                    "total_articles": len(articles),
                    "articles": articles,
                },
                handle,
                indent=2,
                ensure_ascii=False,
            )

        logger.info("Saved %s RSS articles to %s", len(articles), filepath)
        return str(filepath)

    def _normalize_item(self, item: ElementTree.Element) -> Dict:
        title = self._text(item, "title")
        link = self._text(item, "link")
        description = self._clean_html(self._text(item, "description"))
        published_at = self._normalize_pub_date(self._text(item, "pubDate"))
        source_name = self._source_name(item, link)

        return {
            "title": title,
            "description": description,
            "content": "",
            "url": link,
            "source": {"name": source_name},
            "author": "RSS",
            "publishedAt": published_at,
            "urlToImage": "",
            "source_api": "rss_search",
            "domain": urlparse(link).netloc,
        }

    def _text(self, item: ElementTree.Element, tag: str) -> str:
        node = item.find(tag)
        return html.unescape((node.text or "").strip()) if node is not None else ""

    def _clean_html(self, value: str) -> str:
        return TAG_RE.sub(" ", value).replace("\xa0", " ").strip()

    def _normalize_pub_date(self, value: str) -> str:
        if not value:
            return ""
        try:
            return parsedate_to_datetime(value).isoformat()
        except (TypeError, ValueError, IndexError, OverflowError):
            return value

    def _source_name(self, item: ElementTree.Element, link: str) -> str:
        for child in item:
            if child.tag.endswith("source") and child.text:
                return html.unescape(child.text.strip())
        domain = urlparse(link).netloc
        return domain or "RSS"
