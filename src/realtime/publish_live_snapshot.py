"""
One-shot live snapshot publisher for the Vercel dashboard.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

try:
    from vercel.blob import AsyncBlobClient
except Exception:  # pragma: no cover - optional dependency failure
    AsyncBlobClient = None

from src.analysis.emotion import EmotionAnalyzer
from src.analysis.sentiment import SentimentAnalyzer
from src.pipeline.stage1_content_extraction import run_stage as run_stage1
from src.realtime.live_news_monitor import _build_snapshot, _persist_snapshot, _write_json_atomic
from src.utils.api_clients import load_model_config, load_pipeline_config
from src.verification.source_credibility import SourceCredibilityScorer

logger = logging.getLogger(__name__)

DEFAULT_BLOB_PATH = "dashboard/live/latest.json"


def _degraded_snapshot(*, query: str, message: str) -> Dict[str, Any]:
    now_iso = datetime.now().isoformat()
    return {
        "schema_version": 1,
        "status": "degraded",
        "generated_at": now_iso,
        "published_at": now_iso,
        "last_updated": now_iso,
        "cycle": 1,
        "query": query,
        "articles_count": 0,
        "article_count": 0,
        "fetched_articles_count": 0,
        "new_articles_count": 0,
        "seen_articles_skipped": 0,
        "message": message,
        "error": message,
        "sentiment_distribution": {},
        "deep_sentiment_distribution": {},
        "deep_sentiment_summary": {},
        "emotion_distribution": {},
        "average_trust_percent": 0.0,
        "top_sources": {},
        "headlines": [],
    }


def generate_live_snapshot(
    *,
    query: str | None = None,
    sources: str | None = None,
    days_back: int | None = None,
    max_articles: int | None = None,
    max_headlines: int | None = None,
    prefer_transformers: bool | None = None,
) -> Dict[str, Any]:
    """Generate a single dashboard snapshot suitable for storage and web display."""
    load_dotenv()
    pipeline_config = load_pipeline_config()
    model_config = load_model_config()

    query = query or pipeline_config["topic"]
    days_back = days_back if days_back is not None else pipeline_config["days_back"]
    max_articles = max_articles if max_articles is not None else pipeline_config["max_articles"]
    max_headlines = max_headlines if max_headlines is not None else pipeline_config.get("realtime_max_headlines", 12)

    logger.info(
        "Generating live dashboard snapshot | query=%s | sources=%s | days_back=%s | max_articles=%s | max_headlines=%s",
        query,
        sources or "",
        days_back,
        max_articles,
        max_headlines,
    )

    try:
        stage1_result = run_stage1(
            query=query,
            sources=sources,
            days_back=days_back,
            max_articles=max_articles,
            use_existing_data=False,
            offline_mode=False,
            strict_live=True,
        )
        fetched_articles = stage1_result.get("articles", [])
        selected_articles = fetched_articles[:max_headlines]
        message = ""
        if not selected_articles:
            message = "No live headlines were available for this refresh window."

        filtered_stage1_result = dict(stage1_result)
        filtered_stage1_result["articles"] = selected_articles

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

        snapshot = _build_snapshot(
            cycle=1,
            query=query,
            stage1_result=filtered_stage1_result,
            sentiment_analyzer=sentiment_analyzer,
            emotion_analyzer=emotion_analyzer,
            credibility_scorer=credibility_scorer,
            max_headlines=max_headlines,
            fetched_articles_count=len(fetched_articles),
            seen_articles_skipped=0,
            message=message,
        )
        snapshot["schema_version"] = 1
        snapshot["published_at"] = datetime.now().isoformat()
        return snapshot
    except Exception as exc:  # pragma: no cover - exercised via integration path
        logger.warning("Snapshot generation degraded | query=%s | error=%s", query, exc)
        return _degraded_snapshot(query=query, message=str(exc))


def persist_snapshot_locally(
    snapshot: Dict[str, Any],
    output_dir: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """Write the latest snapshot to the local realtime output directory."""
    if output_path is not None:
        output_path = Path(output_path)
        output_dir = output_dir or output_path.parent

    output_dir = output_dir or Path("data/processed/realtime")
    _persist_snapshot(snapshot, output_dir=output_dir)
    default_path = output_dir / "live_snapshot.json"

    if output_path is None:
        return default_path

    if output_path.resolve() != default_path.resolve():
        _write_json_atomic(snapshot, output_path)
    return output_path


async def upload_snapshot_to_blob(
    snapshot: Dict[str, Any],
    *,
    blob_path: str = DEFAULT_BLOB_PATH,
    cache_control_max_age: int = 60,
    token: str | None = None,
) -> Dict[str, Any]:
    """Upload the latest snapshot JSON to Vercel Blob."""
    if AsyncBlobClient is None:
        raise RuntimeError("Vercel Blob SDK is not installed. Install the `vercel` package first.")

    client = AsyncBlobClient(token=token)
    payload = json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8")
    uploaded = await client.put(
        blob_path,
        payload,
        access="public",
        add_random_suffix=False,
        overwrite=True,
        cache_control_max_age=cache_control_max_age,
        content_type="application/json",
    )
    if isinstance(uploaded, dict):
        return dict(uploaded)

    download_url = getattr(uploaded, "download_url", "")
    content_type = getattr(uploaded, "content_type", "application/json")
    content_disposition = getattr(uploaded, "content_disposition", "")
    return {
        "url": getattr(uploaded, "url", ""),
        "download_url": download_url,
        "downloadUrl": download_url,
        "pathname": getattr(uploaded, "pathname", blob_path),
        "content_type": content_type,
        "contentType": content_type,
        "content_disposition": content_disposition,
        "contentDisposition": content_disposition,
    }


def publish_snapshot(
    *,
    query: str | None = None,
    sources: str | None = None,
    days_back: int | None = None,
    max_articles: int | None = None,
    max_headlines: int | None = None,
    prefer_transformers: bool | None = None,
    blob_path: str = DEFAULT_BLOB_PATH,
    cache_control_max_age: int = 60,
    skip_upload: bool = False,
    output_dir: Path | None = None,
    output_path: Path | None = None,
) -> Dict[str, Any]:
    """Generate, persist, and optionally upload the latest dashboard snapshot."""
    snapshot = generate_live_snapshot(
        query=query,
        sources=sources,
        days_back=days_back,
        max_articles=max_articles,
        max_headlines=max_headlines,
        prefer_transformers=prefer_transformers,
    )

    output_path = Path(output_path) if output_path is not None else None
    local_path = output_path or (output_dir or Path("data/processed/realtime")) / "live_snapshot.json"
    snapshot["local_snapshot_file"] = str(local_path)
    persist_snapshot_locally(snapshot, output_dir=output_dir, output_path=output_path)

    if skip_upload:
        logger.info("Skipping Blob upload | local_snapshot=%s", local_path)
        return snapshot

    upload_metadata = asyncio.run(
        upload_snapshot_to_blob(
            snapshot,
            blob_path=blob_path,
            cache_control_max_age=cache_control_max_age,
        )
    )
    snapshot["blob"] = upload_metadata
    snapshot["blob_path"] = blob_path
    persist_snapshot_locally(snapshot, output_dir=output_dir, output_path=output_path)
    logger.info(
        "Uploaded live snapshot to Blob | path=%s | url=%s",
        blob_path,
        upload_metadata.get("url", ""),
    )
    return snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and publish a single live dashboard snapshot.")
    parser.add_argument("--query", help="News query override")
    parser.add_argument("--sources", help="Optional comma-separated NewsAPI source IDs")
    parser.add_argument("--days", type=int, help="Days back to fetch")
    parser.add_argument("--max-articles", type=int, help="Maximum live articles to fetch")
    parser.add_argument("--max-headlines", type=int, help="Maximum headlines to publish to the dashboard")
    parser.add_argument("--transformers", action="store_true", help="Use transformer models for sentiment and emotion")
    parser.add_argument("--blob-path", default=DEFAULT_BLOB_PATH, help="Target pathname inside the Blob store")
    parser.add_argument("--cache-max-age", type=int, default=60, help="Blob cache max age in seconds")
    parser.add_argument("--skip-upload", action="store_true", help="Write the snapshot locally without uploading to Blob")
    parser.add_argument("--output", type=Path, help="Optional local JSON file path for the generated snapshot")
    return parser


def cli_main() -> Dict[str, Any]:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    args = build_parser().parse_args()
    result = publish_snapshot(
        query=args.query,
        sources=args.sources,
        days_back=args.days,
        max_articles=args.max_articles,
        max_headlines=args.max_headlines,
        prefer_transformers=True if args.transformers else False,
        blob_path=args.blob_path,
        cache_control_max_age=args.cache_max_age,
        skip_upload=args.skip_upload,
        output_path=args.output,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    cli_main()
