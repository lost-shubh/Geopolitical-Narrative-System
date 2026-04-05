"""
Live real-time news monitor for GNS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.analysis.emotion import EmotionAnalyzer
from src.analysis.sentiment import SentimentAnalyzer
from src.pipeline.stage1_content_extraction import run_stage as run_stage1
from src.utils.api_clients import load_model_config, load_pipeline_config
from src.verification.source_credibility import SourceCredibilityScorer

logger = logging.getLogger(__name__)
SEEN_REGISTRY_FILE = "live_seen_registry.json"
MAX_SEEN_FINGERPRINTS_PER_QUERY = 5000


def _truncate(text: str, limit: int = 96) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def _safe_source(article: Dict) -> str:
    source = article.get("source", "Unknown")
    if isinstance(source, dict):
        return source.get("name", "Unknown")
    return source or "Unknown"


def _dominant_emotion(scores: Dict[str, float]) -> str:
    if not scores:
        return "neutral"
    return max(scores.items(), key=lambda item: item[1])[0]


def _article_fingerprint(article: Dict) -> str:
    url = (article.get("url") or "").strip().lower()
    if url:
        return url
    title = (article.get("title") or "").strip().lower()
    source = _safe_source(article).strip().lower()
    return f"{source}|{title}" if title else ""


def _monitor_key(query: str, sources: str | None) -> str:
    raw_key = f"{query.strip().lower()}||{(sources or '').strip().lower()}"
    digest = hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:12]
    return f"{query.strip()}::{digest}"


def _write_json_atomic(payload: Dict, output_path: Path) -> None:
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    os.replace(temp_path, output_path)


def _load_seen_registry(output_dir: Path) -> Dict:
    registry_path = output_dir / SEEN_REGISTRY_FILE
    if not registry_path.exists():
        return {"queries": {}}

    try:
        with open(registry_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        logger.warning("Seen registry was unreadable; resetting | path=%s", registry_path)
        return {"queries": {}}

    if not isinstance(payload, dict):
        return {"queries": {}}

    queries = payload.get("queries")
    if not isinstance(queries, dict):
        payload["queries"] = {}
    return payload


def _persist_seen_registry(output_dir: Path, registry: Dict) -> None:
    _write_json_atomic(registry, output_dir / SEEN_REGISTRY_FILE)


def _get_seen_fingerprints(output_dir: Path, query_key: str) -> List[str]:
    registry = _load_seen_registry(output_dir)
    entry = registry.get("queries", {}).get(query_key, {})
    fingerprints = entry.get("seen_fingerprints", [])
    if not isinstance(fingerprints, list):
        return []
    return [item for item in fingerprints if isinstance(item, str) and item]


def _mark_articles_seen(
    *,
    output_dir: Path,
    query_key: str,
    query: str,
    sources: str | None,
    articles: List[Dict],
) -> None:
    new_fingerprints = [fingerprint for article in articles if (fingerprint := _article_fingerprint(article))]
    if not new_fingerprints:
        return

    registry = _load_seen_registry(output_dir)
    queries = registry.setdefault("queries", {})
    entry = queries.setdefault(query_key, {"query": query, "sources": sources or "", "seen_fingerprints": []})

    existing = entry.get("seen_fingerprints", [])
    if not isinstance(existing, list):
        existing = []
    existing_set = set(existing)

    merged = list(existing)
    for fingerprint in new_fingerprints:
        if fingerprint not in existing_set:
            merged.append(fingerprint)
            existing_set.add(fingerprint)

    entry["query"] = query
    entry["sources"] = sources or ""
    entry["seen_fingerprints"] = merged[-MAX_SEEN_FINGERPRINTS_PER_QUERY:]
    entry["last_updated"] = datetime.now().isoformat()
    _persist_seen_registry(output_dir, registry)


def _split_seen_articles(articles: List[Dict], seen_fingerprints: List[str]) -> tuple[List[Dict], int]:
    seen = set(seen_fingerprints)
    unseen_articles: List[Dict] = []
    seen_count = 0

    for article in articles:
        fingerprint = _article_fingerprint(article)
        if fingerprint and fingerprint in seen:
            seen_count += 1
            continue
        unseen_articles.append(article)

    return unseen_articles, seen_count


def _sentiment_detail(item: Dict) -> str:
    return (
        f"{item.get('deep_sentiment', item.get('sentiment', 'NEUTRAL'))} | "
        f"+{item.get('positive_percent', 0.0)}% "
        f"-{item.get('negative_percent', 0.0)}% "
        f"={item.get('neutral_percent', 0.0)}% | "
        f"intensity {item.get('sentiment_intensity', 0.0)}"
    )


def _score_articles(
    articles: List[Dict],
    sentiment_analyzer: SentimentAnalyzer,
    emotion_analyzer: EmotionAnalyzer,
    credibility_scorer: SourceCredibilityScorer,
) -> List[Dict]:
    scored: List[Dict] = []
    for article in articles:
        combined_text = " ".join(
            [article.get("title", ""), article.get("description", ""), article.get("content", "")]
        ).strip()
        sentiment = sentiment_analyzer.analyze_text(combined_text)
        emotions = emotion_analyzer.analyze_text(combined_text)
        source = _safe_source(article)
        trust_score = credibility_scorer.score(source, article.get("url", ""))
        scored.append(
            {
                "title": article.get("title", ""),
                "source": source,
                "published_at": article.get("published_at", ""),
                "url": article.get("url", ""),
                "sentiment": sentiment.get("label", "NEUTRAL"),
                "sentiment_score": sentiment.get("score", 0.0),
                "deep_sentiment": sentiment.get("deep_label", "measured_neutral"),
                "sentiment_profile": {
                    "positive_percent": sentiment.get("positive_percent", 0.0),
                    "negative_percent": sentiment.get("negative_percent", 0.0),
                    "neutral_percent": sentiment.get("neutral_percent", 0.0),
                    "intensity": sentiment.get("intensity", 0.0),
                    "valence": sentiment.get("valence", 0.0),
                },
                "positive_percent": sentiment.get("positive_percent", 0.0),
                "negative_percent": sentiment.get("negative_percent", 0.0),
                "neutral_percent": sentiment.get("neutral_percent", 0.0),
                "sentiment_intensity": sentiment.get("intensity", 0.0),
                "sentiment_valence": sentiment.get("valence", 0.0),
                "dominant_emotion": _dominant_emotion(emotions),
                "emotion_scores": emotions,
                "trust_score": round(trust_score, 4),
                "trust_percent": round(trust_score * 100, 2),
            }
        )
        scored[-1]["sentiment_detail"] = _sentiment_detail(scored[-1])
    return scored


def _build_snapshot(
    *,
    cycle: int,
    query: str,
    stage1_result: Dict,
    sentiment_analyzer: SentimentAnalyzer,
    emotion_analyzer: EmotionAnalyzer,
    credibility_scorer: SourceCredibilityScorer,
    max_headlines: int,
    fetched_articles_count: int | None = None,
    seen_articles_skipped: int = 0,
    message: str = "",
) -> Dict:
    articles = stage1_result.get("articles", [])
    scored = _score_articles(
        articles,
        sentiment_analyzer=sentiment_analyzer,
        emotion_analyzer=emotion_analyzer,
        credibility_scorer=credibility_scorer,
    )

    sentiment_counts = Counter(item["sentiment"] for item in scored)
    deep_sentiment_counts = Counter(item["deep_sentiment"] for item in scored)
    emotion_counts = Counter(item["dominant_emotion"] for item in scored)
    source_counts = Counter(item["source"] for item in scored)
    average_trust = round(sum(item["trust_percent"] for item in scored) / len(scored), 2) if scored else 0.0
    average_positive_signal = round(sum(item["sentiment_profile"]["positive_percent"] for item in scored) / len(scored), 2) if scored else 0.0
    average_negative_signal = round(sum(item["sentiment_profile"]["negative_percent"] for item in scored) / len(scored), 2) if scored else 0.0
    average_neutral_signal = round(sum(item["sentiment_profile"]["neutral_percent"] for item in scored) / len(scored), 2) if scored else 0.0
    average_intensity = round(sum(item["sentiment_intensity"] for item in scored) / len(scored), 4) if scored else 0.0
    average_valence = round(sum(item["sentiment_valence"] for item in scored) / len(scored), 4) if scored else 0.0

    top_headlines = scored[:max_headlines]
    generated_at = datetime.now().isoformat()

    return {
        "status": "ok" if len(scored) > 0 else "degraded",
        "generated_at": generated_at,
        "last_updated": generated_at,
        "cycle": cycle,
        "query": query,
        "articles_count": len(scored),
        "article_count": len(scored),
        "fetched_articles_count": fetched_articles_count if fetched_articles_count is not None else len(scored),
        "new_articles_count": len(top_headlines),
        "seen_articles_skipped": seen_articles_skipped,
        "message": message,
        "sentiment_distribution": dict(sentiment_counts),
        "deep_sentiment_distribution": dict(deep_sentiment_counts),
        "deep_sentiment_summary": {
            "average_positive_signal": average_positive_signal,
            "average_negative_signal": average_negative_signal,
            "average_neutral_signal": average_neutral_signal,
            "average_intensity": average_intensity,
            "average_valence": average_valence,
        },
        "emotion_distribution": dict(emotion_counts),
        "average_trust_percent": average_trust,
        "top_sources": dict(source_counts.most_common(5)),
        "headlines": top_headlines,
        "stage1_processed_file": stage1_result.get("processed_file", ""),
        "stage1_raw_file": stage1_result.get("raw_news_file", ""),
    }


def _persist_snapshot(snapshot: Dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_file = output_dir / "live_snapshot.json"
    history_file = output_dir / "live_history.jsonl"
    _write_json_atomic(snapshot, snapshot_file)

    with open(history_file, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(snapshot, ensure_ascii=False) + "\n")


def _render_snapshot(console: Console, snapshot: Dict, interval_seconds: int) -> None:
    console.clear()
    console.rule(f"GNS Live Monitor | Cycle {snapshot['cycle']} | {snapshot['generated_at']}")

    sentiment = snapshot.get("sentiment_distribution", {})
    deep_sentiment = snapshot.get("deep_sentiment_distribution", {})
    emotions = snapshot.get("emotion_distribution", {})
    top_sources = snapshot.get("top_sources", {})
    average_trust = snapshot.get("average_trust_percent", 0.0)
    fetched_count = snapshot.get("fetched_articles_count", snapshot.get("articles_count", 0))
    new_count = snapshot.get("new_articles_count", snapshot.get("article_count", 0))
    skipped_count = snapshot.get("seen_articles_skipped", 0)
    sentiment_summary = snapshot.get("deep_sentiment_summary", {})
    source_line = ", ".join(f"{name} ({count})" for name, count in top_sources.items()) or "N/A"

    summary = (
        f"Query: {snapshot['query']}\n"
        f"Status: {snapshot.get('status', 'unknown')}\n"
        f"Fetched this cycle: {fetched_count}\n"
        f"New headlines displayed: {new_count}\n"
        f"Previously seen skipped: {skipped_count}\n"
        f"Sentiment: {sentiment}\n"
        f"Deep sentiment: {deep_sentiment}\n"
        f"Average sentiment signals: +{sentiment_summary.get('average_positive_signal', 0.0)}% / "
        f"-{sentiment_summary.get('average_negative_signal', 0.0)}% / "
        f"={sentiment_summary.get('average_neutral_signal', 0.0)}%\n"
        f"Average intensity: {sentiment_summary.get('average_intensity', 0.0)} | "
        f"Average valence: {sentiment_summary.get('average_valence', 0.0)}\n"
        f"Dominant emotions: {emotions}\n"
        f"Average trust: {average_trust}%\n"
        f"Top sources: {source_line}"
    )
    if snapshot.get("message"):
        summary += f"\nMessage: {snapshot['message']}"
    console.print(Panel(summary, title="Live Summary"))

    table = Table(title="Latest Headlines")
    table.add_column("Source", no_wrap=True)
    table.add_column("Sentiment", no_wrap=True)
    table.add_column("+%", no_wrap=True)
    table.add_column("-%", no_wrap=True)
    table.add_column("=%", no_wrap=True)
    table.add_column("Intensity", no_wrap=True)
    table.add_column("Trust%", no_wrap=True)
    table.add_column("Emotion", no_wrap=True)
    table.add_column("Published", no_wrap=True)
    table.add_column("Headline")

    for row in snapshot.get("headlines", []):
        published = (row.get("published_at") or "")[:16].replace("T", " ")
        table.add_row(
            _truncate(row.get("source", ""), 18),
            row.get("deep_sentiment", row.get("sentiment", "NEUTRAL")),
            str(row.get("positive_percent", 0.0)),
            str(row.get("negative_percent", 0.0)),
            str(row.get("neutral_percent", 0.0)),
            str(row.get("sentiment_intensity", 0.0)),
            str(row.get("trust_percent", 0.0)),
            row.get("dominant_emotion", "neutral"),
            published or "-",
            _truncate(row.get("title", ""), 120),
        )

    console.print(table)
    console.print(f"\nNext refresh in {interval_seconds}s. Press Ctrl+C to stop.")


def run_live_monitor(
    *,
    query: str | None = None,
    sources: str | None = None,
    days_back: int | None = None,
    max_articles: int | None = None,
    interval_seconds: int | None = None,
    max_cycles: int = 0,
    prefer_transformers: bool | None = None,
    output_dir: str | Path | None = None,
) -> Dict:
    """Run a continuous live-news monitoring loop."""
    load_dotenv()
    pipeline_config = load_pipeline_config()
    model_config = load_model_config()

    query = query or pipeline_config["topic"]
    days_back = days_back if days_back is not None else pipeline_config["days_back"]
    max_articles = max_articles if max_articles is not None else pipeline_config["max_articles"]
    interval_seconds = interval_seconds or pipeline_config.get("poll_interval_seconds", 60)
    max_headlines = pipeline_config.get("realtime_max_headlines", 12)

    logger.info(
        "Starting live monitor | query=%s | sources=%s | days_back=%s | max_articles=%s | interval_seconds=%s",
        query,
        sources or "",
        days_back,
        max_articles,
        interval_seconds,
    )

    sentiment_analyzer = SentimentAnalyzer(
        model_name=model_config["sentiment_model"],
        prefer_transformers=prefer_transformers
        if prefer_transformers is not None
        else model_config["prefer_transformers"],
    )
    emotion_analyzer = EmotionAnalyzer(
        model_name=model_config["emotion_model"],
        prefer_transformers=prefer_transformers
        if prefer_transformers is not None
        else model_config["prefer_transformers"],
    )
    credibility_scorer = SourceCredibilityScorer()

    console = Console()
    output_dir = Path(output_dir) if output_dir is not None else Path("data/processed/realtime")
    output_dir.mkdir(parents=True, exist_ok=True)
    query_key = _monitor_key(query, sources)
    cycle = 0
    last_snapshot: Dict = {}

    while True:
        cycle += 1
        cycle_started = time.perf_counter()
        logger.info("Live cycle started | cycle=%s | query=%s", cycle, query)
        try:
            fetch_budget = min(max(max_articles, max_headlines * 4, 25), 100)
            stage1_result = run_stage1(
                query=query,
                sources=sources,
                days_back=days_back,
                max_articles=fetch_budget,
                use_existing_data=False,
                offline_mode=False,
                strict_live=True,
            )
            fetched_articles = stage1_result.get("articles", [])
            seen_fingerprints = _get_seen_fingerprints(output_dir, query_key)
            unseen_articles, seen_count = _split_seen_articles(fetched_articles, seen_fingerprints)
            display_limit = min(max_articles, max_headlines)
            selected_articles = unseen_articles[:display_limit]
            snapshot_message = ""

            if not selected_articles:
                snapshot_message = "No unseen articles available in this refresh window."
                logger.warning(
                    "Live cycle found no unseen articles | cycle=%s | query=%s | fetched=%s | seen_skipped=%s",
                    cycle,
                    query,
                    len(fetched_articles),
                    seen_count,
                )

            filtered_stage1_result = dict(stage1_result)
            filtered_stage1_result["articles"] = selected_articles
            snapshot = _build_snapshot(
                cycle=cycle,
                query=query,
                stage1_result=filtered_stage1_result,
                sentiment_analyzer=sentiment_analyzer,
                emotion_analyzer=emotion_analyzer,
                credibility_scorer=credibility_scorer,
                max_headlines=max_headlines,
                fetched_articles_count=len(fetched_articles),
                seen_articles_skipped=seen_count,
                message=snapshot_message,
            )
            if selected_articles:
                _mark_articles_seen(
                    output_dir=output_dir,
                    query_key=query_key,
                    query=query,
                    sources=sources,
                    articles=selected_articles,
                )
            _persist_snapshot(snapshot, output_dir=output_dir)
            _render_snapshot(console, snapshot=snapshot, interval_seconds=interval_seconds)
            last_snapshot = snapshot
            logger.info(
                "Live cycle completed | cycle=%s | status=%s | fetched=%s | new_displayed=%s | seen_skipped=%s | duration=%.2fs",
                cycle,
                snapshot.get("status"),
                snapshot.get("fetched_articles_count", 0),
                snapshot.get("new_articles_count", 0),
                snapshot.get("seen_articles_skipped", 0),
                time.perf_counter() - cycle_started,
            )
        except Exception as exc:
            error_text = str(exc)
            is_zero_article_error = "Strict live mode failed: 0 articles fetched" in error_text
            status = "degraded" if is_zero_article_error else "failed"
            now_iso = datetime.now().isoformat()
            error_snapshot = {
                "status": status,
                "generated_at": datetime.now().isoformat(),
                "last_updated": now_iso,
                "cycle": cycle,
                "query": query,
                "articles_count": 0,
                "article_count": 0,
                "fetched_articles_count": 0,
                "new_articles_count": 0,
                "seen_articles_skipped": 0,
                "error": error_text,
                "headlines": last_snapshot.get("headlines", []) if status == "degraded" else [],
                "sentiment_distribution": last_snapshot.get("sentiment_distribution", {}) if status == "degraded" else {},
                "deep_sentiment_distribution": last_snapshot.get("deep_sentiment_distribution", {}) if status == "degraded" else {},
                "deep_sentiment_summary": last_snapshot.get("deep_sentiment_summary", {}) if status == "degraded" else {},
                "emotion_distribution": last_snapshot.get("emotion_distribution", {}) if status == "degraded" else {},
                "average_trust_percent": last_snapshot.get("average_trust_percent", 0.0) if status == "degraded" else 0.0,
                "top_sources": last_snapshot.get("top_sources", {}) if status == "degraded" else {},
            }
            _persist_snapshot(error_snapshot, output_dir=output_dir)
            if status == "degraded":
                logger.warning(
                    "Live cycle degraded | cycle=%s | reason=%s | duration=%.2fs",
                    cycle,
                    error_text,
                    time.perf_counter() - cycle_started,
                )
                console.print(Panel(error_text, title="Live degraded", style="yellow"))
            else:
                logger.error(
                    "Live cycle failed | cycle=%s | error=%s | duration=%.2fs",
                    cycle,
                    error_text,
                    time.perf_counter() - cycle_started,
                )
                console.print(Panel(error_text, title="Live fetch error", style="bold red"))
            last_snapshot = error_snapshot

        if max_cycles > 0 and cycle >= max_cycles:
            break

        for _ in range(interval_seconds):
            time.sleep(1)

    return last_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the live real-time GNS monitor.")
    parser.add_argument("--topic", help="Live query override (legacy flag)")
    parser.add_argument("--query", help="Live query override")
    parser.add_argument("--sources", help="Optional comma-separated NewsAPI source IDs")
    parser.add_argument("--days", type=int, help="Days back to fetch")
    parser.add_argument("--max-articles", type=int, help="Maximum live articles per cycle")
    parser.add_argument(
        "--interval",
        type=int,
        nargs="?",
        const=60,
        help="Refresh interval in seconds. If provided without a value, defaults to 60.",
    )
    parser.add_argument("--max-cycles", type=int, default=0, help="Stop after N cycles (0 means run forever)")
    parser.add_argument("--transformers", action="store_true", help="Use transformer models for sentiment/emotion")
    return parser


def cli_main() -> Dict:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    args = build_parser().parse_args()
    query = args.query or args.topic
    return run_live_monitor(
        query=query,
        sources=args.sources,
        days_back=args.days,
        max_articles=args.max_articles,
        interval_seconds=args.interval,
        max_cycles=args.max_cycles,
        prefer_transformers=True if args.transformers else None,
    )


if __name__ == "__main__":
    cli_main()
