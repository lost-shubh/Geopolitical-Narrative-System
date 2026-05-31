"""
Stage 2: derive reaction-like text units from live news articles.

This keeps the pipeline news-only and real-time friendly when external social
API credentials are unavailable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Dict, List

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.api_clients import load_pipeline_config

POSITIVE_HINTS = ("progress", "agreement", "ceasefire", "stability", "cooperation", "diplomatic breakthrough")
NEGATIVE_HINTS = ("war", "attack", "conflict", "crisis", "escalation", "sanctions", "casualties")
NEUTRAL_PREFIXES = [
    "Latest update:",
    "Field report:",
    "Analyst note:",
]
POSITIVE_PREFIXES = [
    "Constructive signal:",
    "De-escalation update:",
    "Diplomatic progress:",
]
NEGATIVE_PREFIXES = [
    "Escalation alert:",
    "Risk update:",
    "Security warning:",
]


def _infer_sentiment_hint(text: str) -> str:
    lowered = text.lower()
    pos_hits = sum(1 for token in POSITIVE_HINTS if token in lowered)
    neg_hits = sum(1 for token in NEGATIVE_HINTS if token in lowered)
    if neg_hits > pos_hits:
        return "NEGATIVE"
    if pos_hits > neg_hits:
        return "POSITIVE"
    return "NEUTRAL"


def _compose_weighted_text(title: str, description: str) -> str:
    title = title.strip()
    description = description.strip()
    if title and description:
        # Heavier weight on description while preserving headline context.
        return f"{title}. {description} {description}"
    return description or title


def _prefixed_reaction_body(body: str, sentiment_hint: str) -> str:
    if sentiment_hint == "NEGATIVE":
        options = NEGATIVE_PREFIXES
    elif sentiment_hint == "POSITIVE":
        options = POSITIVE_PREFIXES
    else:
        options = NEUTRAL_PREFIXES
    digest = hashlib.sha1(f"{sentiment_hint}|{body}".encode("utf-8")).hexdigest()
    prefix = options[int(digest[:8], 16) % len(options)]
    return f"{prefix} {body}"


def _build_news_reactions(articles: List[Dict], max_comments: int) -> List[Dict]:
    """
    Build lightweight reaction records from article text.

    Each record uses live article content (title/description) and keeps the
    shape expected by Stage 3 social analyzers.
    """
    reactions: List[Dict] = []

    for index, article in enumerate(articles, start=1):
        title = (article.get("title") or "").strip()
        description = (article.get("description") or "").strip()
        body = _compose_weighted_text(title, description)
        if not body:
            continue

        topics = article.get("topics") or ["general_geopolitics"]
        source = article.get("source", "Unknown")
        published = article.get("published_at") or article.get("publishedAt") or ""
        sentiment_hint = _infer_sentiment_hint(body)
        reaction_body = _prefixed_reaction_body(body, sentiment_hint)

        reactions.append(
            {
                "comment_id": f"news_reaction_{index}",
                "text": reaction_body,
                "platform": "news",
                "topic": topics[0],
                "language": article.get("language", "en"),
                "timestamp": published,
                "source": source,
                "sentiment_hint": sentiment_hint,
                "engagement": {"likes": 0, "retweets": 0, "replies": 0, "shares": 0},
            }
        )

        if len(reactions) >= max_comments:
            break

    return reactions


def run_stage(*, stage1_result: Dict | None = None, max_comments: int | None = None) -> Dict:
    """Collect reaction-like rows from Stage 1 article output."""
    pipeline_config = load_pipeline_config()
    max_comments = max_comments or pipeline_config["max_social_comments"]

    if stage1_result is None:
        stage1_file = Path("data/processed/stage1_content_extraction/articles_with_context.json")
        if not stage1_file.exists():
            raise RuntimeError("Stage 1 output not found. Run Stage 1 first.")
        with open(stage1_file, "r", encoding="utf-8") as handle:
            stage1_result = json.load(handle)

    articles = stage1_result.get("articles", [])
    reactions = _build_news_reactions(articles, max_comments=max_comments)

    topic_counts = Counter(item.get("topic", "unknown") for item in reactions)
    platform_counts = Counter(item.get("platform", "unknown") for item in reactions)

    output_dir = Path("data/processed/stage2_reaction_collection")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "relevant_comments.json"

    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "source_file": stage1_result.get("raw_news_file", ""),
                "total_comments": len(reactions),
                "topic_distribution": dict(topic_counts),
                "platform_distribution": dict(platform_counts),
                "comments": reactions,
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )

    return {
        "source_file": stage1_result.get("raw_news_file", ""),
        "processed_file": str(output_file),
        "comment_count": len(reactions),
        "topic_distribution": dict(topic_counts),
        "platform_distribution": dict(platform_counts),
        "comments": reactions,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage 2 reaction collection.")
    parser.add_argument("--max-comments", type=int, help="Limit collected reaction rows")
    return parser


def cli_main() -> Dict:
    parser = build_parser()
    args = parser.parse_args()
    result = run_stage(max_comments=args.max_comments)
    print(f"Stage 2 complete. Collected {result['comment_count']} reaction rows.")
    print(f"Saved to: {result['processed_file']}")
    return result


if __name__ == "__main__":
    cli_main()
