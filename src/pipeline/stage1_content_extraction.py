"""
Stage 1: news ingestion plus basic content extraction.
"""

import argparse
import json
import logging
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from src.ingestion.news_ingestor import NewsIngestor
from src.preprocessing.clean_text import clean_article_fields
from src.preprocessing.entity_extraction import EntityExtractor
from src.preprocessing.language_detect import LanguageDetector
from src.utils.api_clients import get_news_api_key, load_api_config, load_model_config, load_pipeline_config

logger = logging.getLogger(__name__)

TOPIC_KEYWORDS = {
    "ukraine_russia": {"ukraine", "russia", "europe", "pipeline"},
    "china_taiwan": {"china", "taiwan", "starlink", "asia"},
    "middle_east": {"iran", "israel", "middle east", "gulf"},
    "nato": {"nato", "alliance"},
    "elections": {"election", "interference", "democracy"},
}


def infer_topics(article: Dict) -> List[str]:
    """Infer broad geopolitical topics from an article."""
    haystack = " ".join(
        [
            article.get("title", ""),
            article.get("description", ""),
            article.get("content", ""),
        ]
    ).lower()
    topics = [topic for topic, keywords in TOPIC_KEYWORDS.items() if any(keyword in haystack for keyword in keywords)]
    return topics or ["general_geopolitics"]


def _load_existing_articles(raw_file: Path) -> List[Dict]:
    with open(raw_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("articles", data if isinstance(data, list) else [])


def run_stage(
    *,
    query: str | None = None,
    sources: str | None = None,
    days_back: int | None = None,
    max_articles: int | None = None,
    use_existing_data: bool | None = None,
    offline_mode: bool | None = None,
    strict_live: bool | None = None,
) -> Dict:
    """Run Stage 1 and return processed article artifacts."""
    started_at = time.perf_counter()
    load_dotenv()
    pipeline_config = load_pipeline_config()
    model_config = load_model_config()
    api_config = load_api_config()

    query = query or pipeline_config["topic"]
    days_back = days_back if days_back is not None else pipeline_config["days_back"]
    max_articles = max_articles if max_articles is not None else pipeline_config["max_articles"]
    use_existing_data = pipeline_config["use_existing_data"] if use_existing_data is None else use_existing_data
    offline_mode = pipeline_config["offline_mode"] if offline_mode is None else offline_mode
    strict_live = pipeline_config.get("realtime_only", False) if strict_live is None else strict_live

    logger.info(
        "Stage 1 starting | query=%s | strict_live=%s | use_existing_data=%s | offline_mode=%s | max_articles=%s",
        query,
        strict_live,
        use_existing_data,
        offline_mode,
        max_articles,
    )

    raw_dir = Path("data/raw/news")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / "pipeline_news.json"
    fallback_file = raw_dir / "test_articles.json"

    articles: List[Dict] = []

    if strict_live:
        if offline_mode:
            raise RuntimeError("Stage 1 strict live mode cannot run with offline_mode=True.")
        api_key = get_news_api_key(api_config)
        if not api_key:
            raise RuntimeError("Stage 1 strict live mode requires NEWS_API_KEY.")

        ingestor = NewsIngestor(api_key=api_key, data_dir=str(raw_dir))
        fetched = ingestor.fetch_news(
            query=query,
            sources=sources,
            days_back=days_back,
            max_articles=max_articles,
        )
        if not fetched:
            failure_reason = getattr(ingestor, "last_failure_reason", "")
            logger.error(
                "Strict live mode fetched 0 articles | query=%s | reason=%s",
                query,
                failure_reason or "no matching live articles returned",
            )
            detail = f" ({failure_reason})" if failure_reason else ""
            raise RuntimeError(
                "Strict live mode failed: 0 articles fetched"
                f"{detail}. Retry later, use --no-strict-live for local fallback, or use --offline for local-only mode."
            )

        logger.info("Strict live fetch returned %s articles | query=%s", len(fetched), query)
        raw_path = ingestor.save_articles(fetched, raw_file.name)
        raw_file = Path(raw_path)
        articles = _load_existing_articles(raw_file)
    else:
        if use_existing_data and raw_file.exists():
            articles = _load_existing_articles(raw_file)
        elif use_existing_data and fallback_file.exists():
            raw_file = fallback_file
            articles = _load_existing_articles(raw_file)
        elif not offline_mode:
            api_key = get_news_api_key(api_config)
            if api_key:
                ingestor = NewsIngestor(api_key=api_key, data_dir=str(raw_dir))
                fetched = ingestor.fetch_news(
                    query=query,
                    sources=sources,
                    days_back=days_back,
                    max_articles=max_articles,
                )
                if fetched:
                    raw_path = ingestor.save_articles(fetched, raw_file.name)
                    raw_file = Path(raw_path)
                    articles = _load_existing_articles(raw_file)
                    logger.info("Fetched %s live articles for Stage 1 | query=%s", len(fetched), query)
                else:
                    logger.warning("Live fetch returned 0 articles in non-strict mode | query=%s", query)
        if not articles and fallback_file.exists():
            raw_file = fallback_file
            articles = _load_existing_articles(raw_file)

    if not articles:
        logger.error("Stage 1 ended with 0 articles | query=%s", query)
        raise RuntimeError("Stage 1 could not load any news articles.")

    entity_extractor = EntityExtractor(model_name=model_config["spacy_model"])
    language_detector = LanguageDetector()
    processed_articles = []
    language_counts = Counter()
    topic_counts = Counter()

    for article in articles:
        cleaned = clean_article_fields(article)
        language = language_detector.detect_language(
            " ".join([cleaned.get("title", ""), cleaned.get("description", "")]).strip()
        )
        topics = infer_topics(cleaned)
        entities = entity_extractor.extract_from_fields(cleaned, ["title", "description", "content"])

        enriched = dict(cleaned)
        enriched["language"] = language
        enriched["topics"] = topics
        enriched["entities"] = entities

        processed_articles.append(enriched)
        language_counts[language] += 1
        topic_counts.update(topics)

    output_dir = Path("data/processed/stage1_content_extraction")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "articles_with_context.json"

    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump({
            "source_file": str(raw_file),
            "total_articles": len(processed_articles),
            "language_distribution": dict(language_counts),
            "topic_distribution": dict(topic_counts),
            "articles": processed_articles,
        }, handle, indent=2, ensure_ascii=False)

    duration_seconds = time.perf_counter() - started_at
    logger.info(
        "Stage 1 completed | query=%s | articles=%s | output=%s | duration=%.2fs",
        query,
        len(processed_articles),
        output_file,
        duration_seconds,
    )

    return {
        "raw_news_file": str(raw_file),
        "processed_file": str(output_file),
        "article_count": len(processed_articles),
        "language_distribution": dict(language_counts),
        "topic_distribution": dict(topic_counts),
        "articles": processed_articles,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage 1 content extraction.")
    parser.add_argument("--query", help="News query override")
    parser.add_argument("--sources", help="Comma-separated NewsAPI source IDs")
    parser.add_argument("--days", type=int, help="Days back to search")
    parser.add_argument("--max-articles", type=int, help="Maximum article count")
    parser.add_argument("--offline", action="store_true", help="Skip API calls and use local data only")
    parser.add_argument(
        "--use-existing-data",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Use cached news data when available; defaults to config value when omitted",
    )
    parser.add_argument(
        "--strict-live",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Require live NewsAPI data and disable local fallbacks",
    )
    return parser


def cli_main() -> Dict:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    parser = build_parser()
    args = parser.parse_args()
    result = run_stage(
        query=args.query,
        sources=args.sources,
        days_back=args.days,
        max_articles=args.max_articles,
        use_existing_data=args.use_existing_data,
        offline_mode=args.offline,
        strict_live=args.strict_live,
    )
    logger.info("Stage 1 complete. Processed %s articles.", result["article_count"])
    logger.info("Saved to: %s", result["processed_file"])
    return result


if __name__ == "__main__":
    cli_main()
