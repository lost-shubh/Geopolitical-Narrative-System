"""
News ingestion module for live NewsAPI retrieval.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class NewsIngestor:
    """Fetch and store news articles about geopolitical topics."""

    MAX_RETRIES = 3
    REQUEST_TIMEOUT_SECONDS = 10
    BASE_BACKOFF_SECONDS = 1.0
    TOP_HEADLINE_COUNTRIES = ["us", "gb", "in", "au", "ca"]
    GLOBAL_NEWS_DOMAINS = [
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "aljazeera.com",
        "ft.com",
        "theguardian.com",
        "nytimes.com",
        "washingtonpost.com",
        "wsj.com",
        "foreignpolicy.com",
        "france24.com",
        "dw.com",
        "channelnewsasia.com",
        "economictimes.indiatimes.com",
        "thehindu.com",
        "hindustantimes.com",
        "scmp.com",
        "nikkei.com",
        "npr.org",
        "politico.com",
    ]
    DOMAIN_BATCH_SIZE = 5
    GEOPOLITICAL_TERMS = {
        "geopolitics",
        "geopolitical",
        "diplomacy",
        "diplomatic",
        "conflict",
        "war",
        "ceasefire",
        "sanctions",
        "military",
        "missile",
        "defence",
        "defense",
        "security",
        "nato",
        "iran",
        "israel",
        "ukraine",
        "russia",
        "china",
        "taiwan",
        "india",
        "pakistan",
        "election interference",
        "foreign policy",
        "middle east",
        "strait of hormuz",
    }
    DEFAULT_QUERY_PROFILES = [
        "geopolitics OR diplomacy OR foreign policy OR global security",
        "iran OR israel OR middle east OR sanctions OR ceasefire",
        "ukraine OR russia OR nato OR military OR security",
        "china OR taiwan OR indo-pacific OR military OR foreign policy",
    ]

    def __init__(self, api_key: str, data_dir: str = "data/raw/news"):
        self.api_key = api_key
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://newsapi.org/v2/everything"
        self.top_headlines_url = "https://newsapi.org/v2/top-headlines"
        self.last_failure_reason = ""

    def fetch_news(
        self,
        query: str = "geopolitics OR international relations OR diplomacy",
        sources: str | None = None,
        domains: str | None = None,
        days_back: int = 7,
        language: str = "en",
        sort_by: str = "publishedAt",
        max_articles: int = 100,
    ) -> List[Dict]:
        """
        Fetch news articles from NewsAPI.

        NewsAPI returns at most 100 items per page. This method paginates until
        max_articles is reached (or API data is exhausted), then deduplicates.
        """
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)

        logger.info(
            "Fetching news | query=%s | sources=%s | days_back=%s | max_articles=%s | from=%s | to=%s",
            query,
            sources or "",
            days_back,
            max_articles,
            from_date.date(),
            to_date.date(),
        )

        max_articles = max(1, int(max_articles))
        self.last_failure_reason = ""

        if sources:
            aggregated = self._fetch_single_profile(
                query=query,
                days_back=days_back,
                language=language,
                sort_by=sort_by,
                max_articles=max_articles,
                sources=sources,
                domains=domains,
            )
        else:
            aggregated = self._fetch_top_headlines(
                query=query,
                language=language,
                max_articles=max_articles,
            )
            unique_articles = self._finalize_articles(aggregated, query=query, max_articles=max_articles)
            if unique_articles:
                logger.info(
                    "Fetched %s unique articles from top-headlines path | query=%s",
                    len(unique_articles),
                    query,
                )
                return unique_articles

            domain_batches = self._build_domain_batches(domains)
            query_profiles = self._build_query_profiles(query)
            aggregated = self._fetch_across_global_profiles(
                root_query=query,
                query_profiles=query_profiles,
                domain_batches=domain_batches,
                days_back=days_back,
                language=language,
                sort_by=sort_by,
                max_articles=max_articles,
            )

        unique_articles = self._finalize_articles(aggregated, query=query, max_articles=max_articles)
        if not unique_articles and self.last_failure_reason:
            logger.error("News fetch produced 0 articles | query=%s | reason=%s", query, self.last_failure_reason)
        logger.info("Fetched %s unique articles after dedup | query=%s", len(unique_articles), query)
        return unique_articles

    def clean_article(self, article: Dict) -> Dict:
        """Normalize article structure before persisting."""
        return {
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "content": article.get("content", ""),
            "url": article.get("url", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
            "author": article.get("author", "Unknown"),
            "published_at": article.get("publishedAt", ""),
            "fetched_at": datetime.now().isoformat(),
            "url_to_image": article.get("urlToImage", ""),
        }

    def save_articles(self, articles: List[Dict], filename: Optional[str] = None) -> str:
        """Save fetched articles to JSON."""
        if not articles:
            logger.warning("No articles to save")
            return ""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_{timestamp}.json"

        filepath = self.data_dir / filename
        cleaned_articles = [self.clean_article(article) for article in articles]

        with open(filepath, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "fetched_at": datetime.now().isoformat(),
                    "total_articles": len(cleaned_articles),
                    "articles": cleaned_articles,
                },
                handle,
                indent=2,
                ensure_ascii=False,
            )

        logger.info("Saved %s articles to %s", len(cleaned_articles), filepath)
        return str(filepath)

    def fetch_multiple_topics(
        self,
        topics: List[str],
        days_back: int = 7,
        max_per_topic: int = 50,
    ) -> Dict[str, List[Dict]]:
        """Fetch articles for multiple topic queries."""
        results = {}
        for index, topic in enumerate(topics, 1):
            logger.info("Fetching topic %s/%s | topic=%s", index, len(topics), topic)
            results[topic] = self.fetch_news(
                query=topic,
                days_back=days_back,
                max_articles=max_per_topic,
            )
            if index < len(topics):
                time.sleep(2)
        return results

    def get_statistics(self, articles: List[Dict]) -> Dict:
        """Generate basic statistics for a fetched article set."""
        if not articles:
            return {"total": 0}

        sources: Dict[str, int] = {}
        for article in articles:
            source_value = article.get("source", "Unknown")
            if isinstance(source_value, dict):
                source = source_value.get("name", "Unknown")
            else:
                source = source_value or "Unknown"
            sources[source] = sources.get(source, 0) + 1

        published_values = []
        for article in articles:
            published = article.get("publishedAt") or article.get("published_at")
            if published:
                published_values.append(published)

        return {
            "total": len(articles),
            "sources": len(sources),
            "top_sources": dict(sorted(sources.items(), key=lambda item: item[1], reverse=True)[:5]),
            "date_range": {
                "earliest": min(published_values) if published_values else "",
                "latest": max(published_values) if published_values else "",
            },
        }

    def _dedupe_articles(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicates using URL first, then title fallback."""
        unique: List[Dict] = []
        seen = set()

        for article in articles:
            url = (article.get("url") or "").strip().lower()
            title = (article.get("title") or "").strip().lower()
            fingerprint = url or title
            if not fingerprint or fingerprint in seen:
                continue
            seen.add(fingerprint)
            unique.append(article)

        def sort_key(item: Dict) -> str:
            return (item.get("publishedAt") or item.get("published_at") or "")

        unique.sort(key=sort_key, reverse=True)
        return unique

    def _finalize_articles(self, articles: List[Dict], *, query: str, max_articles: int) -> List[Dict]:
        deduped = self._dedupe_articles(articles)
        filtered = self._filter_relevant_articles(deduped, query=query)
        return filtered[:max_articles]

    def _build_query_profiles(self, query: str) -> List[str]:
        """Expand broad geopolitical queries into multiple topical profiles."""
        lowered = query.lower().strip()
        broad_tokens = {"geopolitics", "diplomacy", "international", "foreign policy", "global security"}
        if any(token in lowered for token in broad_tokens):
            return [query, *self.DEFAULT_QUERY_PROFILES]
        return [query]

    def _build_domain_batches(self, domains: str | None) -> List[str | None]:
        """Split domain lists into smaller batches for broader, higher-quality coverage."""
        if domains:
            domain_list = [item.strip() for item in domains.split(",") if item.strip()]
        else:
            domain_list = self.GLOBAL_NEWS_DOMAINS

        if not domain_list:
            return [None]

        return [
            ",".join(domain_list[index:index + self.DOMAIN_BATCH_SIZE])
            for index in range(0, len(domain_list), self.DOMAIN_BATCH_SIZE)
        ]

    def _fetch_across_global_profiles(
        self,
        *,
        root_query: str,
        query_profiles: List[str],
        domain_batches: List[str | None],
        days_back: int,
        language: str,
        sort_by: str,
        max_articles: int,
    ) -> List[Dict]:
        """Fan out across query profiles and domain batches to widen global coverage."""
        aggregated: List[Dict] = []
        per_profile_limit = max(10, min(20, (max_articles // max(1, len(domain_batches))) + 5))

        for query_profile in query_profiles:
            for domain_batch in domain_batches:
                batch_articles = self._fetch_single_profile(
                    query=query_profile,
                    days_back=days_back,
                    language=language,
                    sort_by=sort_by,
                    max_articles=per_profile_limit,
                    domains=domain_batch,
                )
                aggregated.extend(batch_articles)

                current_candidates = self._filter_relevant_articles(self._dedupe_articles(aggregated), query=root_query)
                if len(current_candidates) >= max_articles:
                    logger.info(
                        "Early stop for global profile fetch | query=%s | accumulated_relevant_articles=%s",
                        root_query,
                        len(current_candidates),
                    )
                    return aggregated

        return aggregated

    def _fetch_top_headlines(
        self,
        *,
        query: str,
        language: str,
        max_articles: int,
    ) -> List[Dict]:
        """Fetch live top headlines across several countries with low request volume."""
        aggregated: List[Dict] = []
        page_size = min(max(max_articles, 20), 100)
        query_term = self._normalize_top_headlines_query(query)

        logger.info(
            "Fetching top-headlines fallback | query=%s | normalized_query=%s | max_articles=%s",
            query,
            query_term or "",
            max_articles,
        )

        for country in self.TOP_HEADLINE_COUNTRIES:
            params = {
                "country": country,
                "pageSize": page_size,
                "page": 1,
                "apiKey": self.api_key,
            }
            if query_term:
                params["q"] = query_term

            payload = self._request_json_with_retries(
                url=self.top_headlines_url,
                params=params,
                request_name="top-headlines",
                query=query,
                page=1,
                context=country,
            )
            if payload is None:
                continue

            if payload.get("status") != "ok":
                self.last_failure_reason = payload.get("message", "NewsAPI top-headlines returned non-ok status")
                logger.error(
                    "Top-headlines logical error | query=%s | country=%s | message=%s",
                    query,
                    country,
                    self.last_failure_reason,
                )
                continue

            page_articles = payload.get("articles", [])
            if not page_articles:
                logger.warning("Top-headlines returned 0 articles | query=%s | country=%s", query, country)
                continue

            aggregated.extend(page_articles)
            current_candidates = self._finalize_articles(aggregated, query=query, max_articles=max_articles)
            logger.info(
                "Top-headlines received | query=%s | country=%s | page_articles=%s | relevant_accumulated=%s",
                query,
                country,
                len(page_articles),
                len(current_candidates),
            )
            if len(current_candidates) >= max_articles:
                break

        return aggregated

    def _fetch_single_profile(
        self,
        *,
        query: str,
        days_back: int,
        language: str,
        sort_by: str,
        max_articles: int,
        sources: str | None = None,
        domains: str | None = None,
    ) -> List[Dict]:
        """Fetch one query/source/domain profile with pagination and retries."""
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        page = 1
        page_size = min(max_articles, 100)
        aggregated: List[Dict] = []

        logger.info(
            "Fetching profile | query=%s | sources=%s | domains=%s | max_articles=%s",
            query,
            sources or "",
            domains or "",
            max_articles,
        )

        while len(aggregated) < max_articles:
            params = {
                "q": query,
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d"),
                "language": language,
                "sortBy": sort_by,
                "pageSize": page_size,
                "page": page,
                "apiKey": self.api_key,
            }
            if sources:
                params["sources"] = sources
            if domains:
                params["domains"] = domains

            try:
                payload = self._fetch_page_with_retries(params=params, query=query, page=page)
                if payload is None:
                    logger.error("News page fetch failed after retries | query=%s | page=%s", query, page)
                    break

                if payload.get("status") != "ok":
                    self.last_failure_reason = payload.get("message", "NewsAPI everything returned non-ok status")
                    logger.error(
                        "NewsAPI logical error | query=%s | page=%s | message=%s",
                        query,
                        page,
                        self.last_failure_reason,
                    )
                    break

                page_articles = payload.get("articles", [])
                if not page_articles:
                    break

                aggregated.extend(page_articles)
                total_results = int(payload.get("totalResults", 0))
                logger.info(
                    "News page received | query=%s | page=%s | page_articles=%s | aggregated=%s | total_results=%s",
                    query,
                    page,
                    len(page_articles),
                    len(aggregated),
                    total_results,
                )

                if total_results > 0 and len(aggregated) >= total_results:
                    break

                page += 1
            except requests.exceptions.RequestException as exc:
                logger.error(
                    "Unexpected request exception outside retry loop | query=%s | error=%s",
                    query,
                    self._sanitize_error_message(exc),
                )
                break

        return aggregated[:max_articles]

    def _filter_relevant_articles(self, articles: List[Dict], query: str) -> List[Dict]:
        """Drop obvious non-geopolitical matches from broad NewsAPI queries."""
        if not articles:
            return []

        query_terms = {token.strip().lower() for token in re.split(r"\bor\b|\s+", query) if token.strip()}
        query_terms = {token for token in query_terms if len(token) > 2}
        relevance_terms = self.GEOPOLITICAL_TERMS | query_terms

        filtered = [article for article in articles if self._is_relevant_article(article, relevance_terms)]
        if filtered:
            logger.info(
                "Relevance filter kept %s/%s articles | query=%s",
                len(filtered),
                len(articles),
                query,
            )
            return filtered

        logger.warning(
            "Relevance filter rejected all fetched articles; returning deduped set unchanged | query=%s",
            query,
        )
        return articles

    def _is_relevant_article(self, article: Dict, relevance_terms: set[str]) -> bool:
        text = " ".join(
            [
                str(article.get("title") or ""),
                str(article.get("description") or ""),
                str(article.get("content") or ""),
            ]
        ).lower()
        if not text.strip():
            return False
        return any(re.search(r"\b" + re.escape(term) + r"\b", text) for term in relevance_terms)

    def _fetch_page_with_retries(self, *, params: Dict, query: str, page: int) -> Optional[Dict]:
        """Fetch one NewsAPI page with retries and exponential backoff."""
        return self._request_json_with_retries(
            url=self.base_url,
            params=params,
            request_name="everything",
            query=query,
            page=page,
        )

    def _request_json_with_retries(
        self,
        *,
        url: str,
        params: Dict,
        request_name: str,
        query: str,
        page: int,
        context: str = "",
    ) -> Optional[Dict]:
        """Fetch one NewsAPI JSON payload with retries and exponential backoff."""
        backoff = self.BASE_BACKOFF_SECONDS

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = requests.get(url, params=params, timeout=self.REQUEST_TIMEOUT_SECONDS)
                logger.info(
                    "NewsAPI response | request=%s | query=%s | context=%s | page=%s | attempt=%s | status_code=%s",
                    request_name,
                    query,
                    context,
                    page,
                    attempt,
                    response.status_code,
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout as exc:
                self.last_failure_reason = f"{request_name} timeout"
                logger.warning(
                    "NewsAPI timeout | request=%s | query=%s | context=%s | page=%s | attempt=%s/%s | error=%s",
                    request_name,
                    query,
                    context,
                    page,
                    attempt,
                    self.MAX_RETRIES,
                    self._sanitize_error_message(exc),
                )
            except requests.exceptions.ConnectionError as exc:
                self.last_failure_reason = f"{request_name} connection error"
                logger.warning(
                    "NewsAPI connection error | request=%s | query=%s | context=%s | page=%s | attempt=%s/%s | error=%s",
                    request_name,
                    query,
                    context,
                    page,
                    attempt,
                    self.MAX_RETRIES,
                    self._sanitize_error_message(exc),
                )
            except requests.exceptions.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                self.last_failure_reason = f"{request_name} HTTP {status_code}" if status_code else f"{request_name} HTTP error"
                if status_code and status_code >= 500:
                    logger.warning(
                        "NewsAPI HTTP server error | request=%s | query=%s | context=%s | page=%s | attempt=%s/%s | status_code=%s",
                        request_name,
                        query,
                        context,
                        page,
                        attempt,
                        self.MAX_RETRIES,
                        status_code,
                    )
                else:
                    logger.error(
                        "NewsAPI HTTP client error | request=%s | query=%s | context=%s | page=%s | attempt=%s | status_code=%s",
                        request_name,
                        query,
                        context,
                        page,
                        attempt,
                        status_code,
                    )
                    return None
            except requests.exceptions.RequestException as exc:
                self.last_failure_reason = f"{request_name} request exception"
                logger.error(
                    "NewsAPI request exception | request=%s | query=%s | context=%s | page=%s | attempt=%s/%s | error=%s",
                    request_name,
                    query,
                    context,
                    page,
                    attempt,
                    self.MAX_RETRIES,
                    self._sanitize_error_message(exc),
                )

            if attempt < self.MAX_RETRIES:
                logger.warning(
                    "Retrying NewsAPI request | request=%s | query=%s | context=%s | page=%s | next_attempt=%s | backoff=%.1fs",
                    request_name,
                    query,
                    context,
                    page,
                    attempt + 1,
                    backoff,
                )
                time.sleep(backoff)
                backoff *= 2

        return None

    def _normalize_top_headlines_query(self, query: str) -> str:
        """Map broad live-monitor queries to concrete top-headline keywords."""
        lowered = (query or "").strip().lower()
        if not lowered:
            return ""

        broad_markers = {"geopolitics", "international", "foreign policy", "global security", "diplomacy"}
        if any(marker in lowered for marker in broad_markers):
            return ""

        tokens = [token.strip() for token in re.split(r"\bor\b|\band\b|[,\s]+", lowered) if token.strip()]
        filtered_tokens = [token for token in tokens if len(token) > 2 and token not in {"the", "and", "for"}]
        return " OR ".join(filtered_tokens[:4])

    def _sanitize_error_message(self, error: Exception | str) -> str:
        """Redact secrets from request/response error text before logging."""
        message = str(error)
        if self.api_key:
            message = message.replace(self.api_key, "[REDACTED]")
        message = re.sub(r"(apiKey=)([^&\s)\"']+)", r"\1[REDACTED]", message)
        return message


def main():
    """Example usage."""
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        logger.error("NEWS_API_KEY not found in environment variables")
        logger.error("Please create a .env file with: NEWS_API_KEY=your_key_here")
        return

    ingestor = NewsIngestor(api_key=api_key)
    articles = ingestor.fetch_news(query="geopolitics OR international conflict", days_back=1, max_articles=25)
    if not articles:
        logger.warning("No articles returned.")
        return

    output_file = ingestor.save_articles(articles, "pipeline_news.json")
    stats = ingestor.get_statistics(articles)
    logger.info("Saved: %s", output_file)
    logger.info("Total=%s | Unique sources=%s", stats["total"], stats["sources"])


if __name__ == "__main__":
    main()
