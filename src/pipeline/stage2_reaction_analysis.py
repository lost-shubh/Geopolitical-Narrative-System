"""
Stage 2: reaction collection from the bundled social dataset.
"""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict

from src.ingestion.comment_collector import CommentCollector
from src.ingestion.social_ingestor import SocialIngestor
from src.utils.api_clients import load_pipeline_config


def run_stage(*, stage1_result: Dict | None = None, max_comments: int | None = None) -> Dict:
    """Collect reactions relevant to the Stage 1 article set."""
    pipeline_config = load_pipeline_config()
    max_comments = max_comments or pipeline_config["max_social_comments"]

    if stage1_result is None:
        stage1_file = Path("data/processed/stage1_content_extraction/articles_with_context.json")
        if not stage1_file.exists():
            raise RuntimeError("Stage 1 output not found. Run Stage 1 first.")
        with open(stage1_file, "r", encoding="utf-8") as handle:
            stage1_result = json.load(handle)

    articles = stage1_result.get("articles", [])
    ingestor = SocialIngestor()
    social_file = ingestor.load_or_generate()
    comments = ingestor.load_comments(social_file)

    collector = CommentCollector()
    relevant_comments = collector.collect_relevant_comments(
        articles,
        comments,
        max_comments=max_comments,
    )

    topic_counts = Counter(comment.get("topic", "unknown") for comment in relevant_comments)
    platform_counts = Counter(comment.get("platform", "unknown") for comment in relevant_comments)

    output_dir = Path("data/processed/stage2_reaction_collection")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "relevant_comments.json"

    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump({
            "source_file": social_file,
            "total_comments": len(relevant_comments),
            "topic_distribution": dict(topic_counts),
            "platform_distribution": dict(platform_counts),
            "comments": relevant_comments,
        }, handle, indent=2, ensure_ascii=False)

    return {
        "source_file": social_file,
        "processed_file": str(output_file),
        "comment_count": len(relevant_comments),
        "topic_distribution": dict(topic_counts),
        "platform_distribution": dict(platform_counts),
        "comments": relevant_comments,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage 2 reaction collection.")
    parser.add_argument("--max-comments", type=int, help="Limit collected comments")
    return parser


def cli_main() -> Dict:
    parser = build_parser()
    args = parser.parse_args()
    result = run_stage(max_comments=args.max_comments)
    print(f"Stage 2 complete. Collected {result['comment_count']} relevant comments.")
    print(f"Saved to: {result['processed_file']}")
    return result


if __name__ == "__main__":
    cli_main()
