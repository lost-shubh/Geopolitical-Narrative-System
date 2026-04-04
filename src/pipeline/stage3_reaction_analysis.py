"""
Stage 3: analyze news and social reactions.
"""

import argparse
import json
from pathlib import Path
from typing import Dict

from src.analysis.emotion import EmotionAnalyzer
from src.analysis.engagement_metrics import EngagementMetricsAnalyzer
from src.analysis.polarization import PolarizationAnalyzer
from src.analysis.sentiment import SentimentAnalyzer
from src.utils.api_clients import load_model_config, load_pipeline_config


def _load_stage_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_legacy_outputs(news_payload: Dict, social_payload: Dict) -> None:
    combined_dir = Path("data/processed/combined_analysis")
    combined_dir.mkdir(parents=True, exist_ok=True)
    with open(combined_dir / "sentiment_emotion_analysis.json", "w", encoding="utf-8") as handle:
        json.dump(news_payload, handle, indent=2, ensure_ascii=False)

    summary_file = combined_dir / "analysis_summary.txt"
    with open(summary_file, "w", encoding="utf-8") as handle:
        sent_stats = news_payload["sentiment_statistics"]
        emo_stats = news_payload["emotion_statistics"]
        handle.write("GEOPOLITICAL NARRATIVE ANALYSIS - SUMMARY REPORT\n")
        handle.write("=" * 60 + "\n\n")
        handle.write(f"Total articles: {sent_stats['total_analyzed']}\n")
        handle.write(f"Negative coverage: {sent_stats['negative_percent']}%\n")
        handle.write(f"Dominant emotion: {emo_stats['most_common_emotion']}\n")

    social_dir = Path("data/processed/social_analysis")
    social_dir.mkdir(parents=True, exist_ok=True)
    with open(social_dir / "analyzed_comments.json", "w", encoding="utf-8") as handle:
        json.dump(social_payload, handle, indent=2, ensure_ascii=False)

    social_summary = social_dir / "social_media_summary.txt"
    with open(social_summary, "w", encoding="utf-8") as handle:
        handle.write("SOCIAL MEDIA REACTION ANALYSIS - SUMMARY\n")
        handle.write("=" * 60 + "\n\n")
        handle.write(f"Total Comments Analyzed: {len(social_payload['comments'])}\n")
        handle.write(f"Polarization Level: {social_payload['polarization']['level']}\n")
        handle.write(f"Virality Score: {social_payload['engagement']['virality_score']}\n")


def run_stage(*, stage1_result: Dict | None = None, stage2_result: Dict | None = None) -> Dict:
    """Analyze news content and social reactions."""
    load_pipeline_config()
    model_config = load_model_config()

    if stage1_result is None:
        stage1_result = _load_stage_json("data/processed/stage1_content_extraction/articles_with_context.json")
    if stage2_result is None:
        stage2_result = _load_stage_json("data/processed/stage2_reaction_collection/relevant_comments.json")

    articles = stage1_result.get("articles", [])
    comments = stage2_result.get("comments", [])

    sentiment_analyzer = SentimentAnalyzer(
        model_name=model_config["sentiment_model"],
        prefer_transformers=model_config["prefer_transformers"],
    )
    emotion_analyzer = EmotionAnalyzer(
        model_name=model_config["emotion_model"],
        prefer_transformers=model_config["prefer_transformers"],
    )
    polarization_analyzer = PolarizationAnalyzer()
    engagement_analyzer = EngagementMetricsAnalyzer()

    news_sentiment = sentiment_analyzer.analyze_articles(articles, fields=["title", "description"])
    news_emotions = emotion_analyzer.analyze_articles(articles, fields=["title", "description"])

    merged_articles = []
    for sent_item, emo_item in zip(news_sentiment, news_emotions):
        merged = dict(sent_item)
        merged["emotion_analysis"] = emo_item.get("emotion_analysis", {})
        merged_articles.append(merged)

    news_payload = {
        "total_articles": len(merged_articles),
        "sentiment_statistics": sentiment_analyzer.get_sentiment_statistics(news_sentiment),
        "emotion_statistics": emotion_analyzer.get_emotion_statistics(news_emotions),
        "articles": merged_articles,
    }

    texts = [comment.get("text", "") for comment in comments]
    sentiments = sentiment_analyzer.analyze_batch(texts, batch_size=16)
    analyzed_comments = []
    for comment, sentiment in zip(comments, sentiments):
        enriched = dict(comment)
        emotions = emotion_analyzer.analyze_text(comment.get("text", ""))
        dominant = max(emotions.items(), key=lambda item: item[1]) if emotions else ("neutral", 0.0)
        enriched["sentiment"] = sentiment
        enriched["emotions"] = emotions
        enriched["dominant_emotion"] = {"emotion": dominant[0], "score": dominant[1]}
        analyzed_comments.append(enriched)

    social_payload = {
        "total_comments": len(analyzed_comments),
        "sentiment_counts": {
            "POSITIVE": sum(1 for comment in analyzed_comments if comment["sentiment"]["label"] == "POSITIVE"),
            "NEGATIVE": sum(1 for comment in analyzed_comments if comment["sentiment"]["label"] == "NEGATIVE"),
            "NEUTRAL": sum(1 for comment in analyzed_comments if comment["sentiment"]["label"] == "NEUTRAL"),
        },
        "emotion_counts": {
            emotion: sum(1 for comment in analyzed_comments if comment["dominant_emotion"]["emotion"] == emotion)
            for emotion in emotion_analyzer.EMOTIONS
        },
        "polarization": polarization_analyzer.analyze_comments(analyzed_comments),
        "engagement": engagement_analyzer.analyze_comments(analyzed_comments),
        "comments": analyzed_comments,
    }
    social_payload["emotion_counts"] = {key: value for key, value in social_payload["emotion_counts"].items() if value}

    output_dir = Path("data/processed/stage3_reaction_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    news_file = output_dir / "news_analysis.json"
    social_file = output_dir / "social_analysis.json"

    with open(news_file, "w", encoding="utf-8") as handle:
        json.dump(news_payload, handle, indent=2, ensure_ascii=False)
    with open(social_file, "w", encoding="utf-8") as handle:
        json.dump(social_payload, handle, indent=2, ensure_ascii=False)

    _save_legacy_outputs(news_payload, social_payload)

    return {
        "news_file": str(news_file),
        "social_file": str(social_file),
        "news_results": news_payload,
        "social_results": social_payload,
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description="Run Stage 3 analysis.")


def cli_main() -> Dict:
    build_parser().parse_args()
    result = run_stage()
    print("Stage 3 complete.")
    print(f"News analysis: {result['news_file']}")
    print(f"Social analysis: {result['social_file']}")
    return result


if __name__ == "__main__":
    cli_main()
