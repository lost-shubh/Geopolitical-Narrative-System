"""
Stage 1: news ingestion plus basic content extraction.
"""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from src.ingestion.news_ingestor import NewsIngestor
from src.preprocessing.clean_text import clean_article_fields
from src.preprocessing.entity_extraction import EntityExtractor
from src.preprocessing.language_detect import LanguageDetector
from src.utils.api_clients import get_news_api_key, load_api_config, load_model_config, load_pipeline_config

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
    days_back: int | None = None,
    max_articles: int | None = None,
    use_existing_data: bool | None = None,
    offline_mode: bool | None = None,
) -> Dict:
    """Run Stage 1 and return processed article artifacts."""
    load_dotenv()
    pipeline_config = load_pipeline_config()
    model_config = load_model_config()
    api_config = load_api_config()

    query = query or pipeline_config["topic"]
    days_back = days_back if days_back is not None else pipeline_config["days_back"]
    max_articles = max_articles if max_articles is not None else pipeline_config["max_articles"]
    use_existing_data = pipeline_config["use_existing_data"] if use_existing_data is None else use_existing_data
    offline_mode = pipeline_config["offline_mode"] if offline_mode is None else offline_mode

    raw_dir = Path("data/raw/news")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / "pipeline_news.json"
    fallback_file = raw_dir / "test_articles.json"

    articles: List[Dict] = []

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
                days_back=days_back,
                max_articles=max_articles,
            )
            if fetched:
                raw_path = ingestor.save_articles(fetched, raw_file.name)
                raw_file = Path(raw_path)
                articles = _load_existing_articles(raw_file)
    if not articles and fallback_file.exists():
        raw_file = fallback_file
        articles = _load_existing_articles(raw_file)

    if not articles:
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
    parser.add_argument("--days", type=int, help="Days back to search")
    parser.add_argument("--max-articles", type=int, help="Maximum article count")
    parser.add_argument("--offline", action="store_true", help="Skip API calls and use local data only")
    parser.add_argument("--no-existing-data", action="store_true", help="Prefer fresh ingestion over local files")
    return parser


def cli_main() -> Dict:
    parser = build_parser()
    args = parser.parse_args()
    result = run_stage(
        query=args.query,
        days_back=args.days,
        max_articles=args.max_articles,
        use_existing_data=not args.no_existing_data,
        offline_mode=args.offline,
    )
    print(f"Stage 1 complete. Processed {result['article_count']} articles.")
    print(f"Saved to: {result['processed_file']}")
    return result


if __name__ == "__main__":
    cli_main()
