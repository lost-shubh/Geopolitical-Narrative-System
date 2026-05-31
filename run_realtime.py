"""
Entry point for the live real-time monitor.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.realtime.live_news_monitor import run_live_monitor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the live real-time GNS monitor.")
    parser.add_argument("--query", default="geopolitics", help="Live query string (default: geopolitics)")
    parser.add_argument("--topic", help="Legacy alias for query")
    parser.add_argument("--sources", help="Optional comma-separated NewsAPI source IDs")
    parser.add_argument("--days", type=int, help="Days back to fetch")
    parser.add_argument("--max-articles", type=int, help="Maximum live articles to fetch per cycle")
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


def main():
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    args = build_parser().parse_args()
    query = args.query
    if args.topic and args.query == "geopolitics":
        query = args.topic

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
    main()
