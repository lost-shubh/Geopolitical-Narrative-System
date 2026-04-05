"""Tests for strict live mode and news-only Stage 2 behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests

import src.ingestion.news_ingestor as news_ingestor
import src.pipeline.stage1_content_extraction as stage1
import run_realtime
from src.pipeline.stage2_reaction_analysis import run_stage as run_stage2
import src.realtime.live_news_monitor as live_monitor


def test_stage1_strict_live_requires_api_key(monkeypatch):
    monkeypatch.setattr(stage1, "get_news_api_key", lambda _cfg=None: "")

    with pytest.raises(RuntimeError, match="requires NEWS_API_KEY"):
        stage1.run_stage(
            query="geopolitics",
            days_back=1,
            max_articles=5,
            use_existing_data=False,
            offline_mode=False,
            strict_live=True,
        )


def test_stage1_strict_live_fetches_and_processes_articles(monkeypatch):
    sample_articles = [
        {
            "title": "NATO leaders meet in Brussels",
            "description": "Leaders discussed alliance coordination this week.",
            "content": "Officials said cooperation will continue.",
            "url": "https://example.test/nato-briefing",
            "source": {"name": "Reuters"},
            "publishedAt": "2026-04-05T00:00:00Z",
        }
    ]

    class FakeNewsIngestor:
        def __init__(self, api_key: str, data_dir: str):
            self.api_key = api_key
            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)

        def fetch_news(self, **_kwargs):
            return sample_articles

        def save_articles(self, articles, filename):
            output = self.data_dir / filename
            payload = {
                "total_articles": len(articles),
                "articles": [
                    {
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "content": item.get("content", ""),
                        "url": item.get("url", ""),
                        "source": item.get("source", {}).get("name", "Unknown"),
                        "author": item.get("author", "Unknown"),
                        "published_at": item.get("publishedAt", ""),
                        "fetched_at": "2026-04-05T00:00:00Z",
                        "url_to_image": item.get("urlToImage", ""),
                    }
                    for item in articles
                ],
            }
            with open(output, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
            return str(output)

    monkeypatch.setattr(stage1, "get_news_api_key", lambda _cfg=None: "test-key")
    monkeypatch.setattr(stage1, "NewsIngestor", FakeNewsIngestor)

    result = stage1.run_stage(
        query="nato",
        days_back=1,
        max_articles=5,
        use_existing_data=False,
        offline_mode=False,
        strict_live=True,
    )

    assert result["article_count"] == 1
    assert result["articles"][0]["title"] == "NATO leaders meet in Brussels"
    assert Path(result["processed_file"]).exists()


def test_stage2_builds_reactions_from_news_articles():
    stage1_result = {
        "raw_news_file": "data/raw/news/pipeline_news.json",
        "articles": [
            {
                "title": "Diplomatic talks resume",
                "description": "Officials said negotiations restarted on Monday.",
                "topics": ["nato"],
                "language": "en",
                "source": "BBC",
                "published_at": "2026-04-05T00:00:00Z",
            }
        ],
    }

    result = run_stage2(stage1_result=stage1_result, max_comments=10)
    assert result["comment_count"] == 1
    assert result["comments"][0]["platform"] == "news"
    assert result["comments"][0]["topic"] == "nato"


def test_stage1_strict_live_raises_when_fetch_returns_zero(monkeypatch):
    class EmptyNewsIngestor:
        def __init__(self, api_key: str, data_dir: str):
            self.api_key = api_key
            self.data_dir = Path(data_dir)

        def fetch_news(self, **_kwargs):
            return []

    monkeypatch.setattr(stage1, "get_news_api_key", lambda _cfg=None: "test-key")
    monkeypatch.setattr(stage1, "NewsIngestor", EmptyNewsIngestor)

    with pytest.raises(RuntimeError, match="Strict live mode failed: 0 articles fetched"):
        stage1.run_stage(
            query="geopolitics",
            days_back=1,
            max_articles=5,
            use_existing_data=False,
            offline_mode=False,
            strict_live=True,
        )


def test_snapshot_contains_health_fields():
    class FakeSentiment:
        def analyze_text(self, _text):
            return {
                "label": "NEUTRAL",
                "score": 0.5,
                "positive_percent": 20.0,
                "negative_percent": 20.0,
                "neutral_percent": 60.0,
                "intensity": 0.3,
                "valence": 0.0,
                "deep_label": "measured_neutral",
            }

    class FakeEmotion:
        def analyze_text(self, _text):
            return {"neutral": 1.0}

    snapshot = live_monitor._build_snapshot(
        cycle=1,
        query="geopolitics",
        stage1_result={
            "articles": [
                {
                    "title": "Talks continue",
                    "description": "Diplomats met in Geneva.",
                    "content": "",
                    "source": "Reuters",
                    "published_at": "2026-04-05T00:00:00Z",
                    "url": "https://example.test/talks",
                }
            ]
        },
        sentiment_analyzer=FakeSentiment(),
        emotion_analyzer=FakeEmotion(),
        credibility_scorer=live_monitor.SourceCredibilityScorer(),
        max_headlines=5,
    )

    assert snapshot["status"] == "ok"
    assert snapshot["articles_count"] == 1
    assert snapshot["fetched_articles_count"] == 1
    assert snapshot["new_articles_count"] == 1
    assert snapshot["seen_articles_skipped"] == 0
    assert snapshot["last_updated"]
    assert "average_trust_percent" in snapshot
    assert "deep_sentiment_distribution" in snapshot
    assert "average_intensity" in snapshot["deep_sentiment_summary"]
    assert snapshot["headlines"][0]["sentiment_detail"]


def test_news_ingestor_retries_on_connection_error(monkeypatch):
    attempts = {"count": 0}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": "ok",
                "totalResults": 1,
                "articles": [
                    {
                        "title": "Ceasefire talks",
                        "description": "Negotiations continue.",
                        "content": "Officials commented.",
                        "url": "https://example.test/ceasefire",
                        "source": {"name": "BBC"},
                        "publishedAt": "2026-04-05T00:00:00Z",
                    }
                ],
            }

    def fake_get(*_args, **_kwargs):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise requests.exceptions.ConnectionError("network down")
        return FakeResponse()

    monkeypatch.setattr(news_ingestor.requests, "get", fake_get)
    monkeypatch.setattr(news_ingestor.time, "sleep", lambda _seconds: None)

    ingestor = news_ingestor.NewsIngestor(api_key="test-key")
    articles = ingestor.fetch_news(query="geopolitics", days_back=1, max_articles=1)

    assert attempts["count"] == 3
    assert len(articles) == 1


def test_news_ingestor_builds_global_domain_batches():
    ingestor = news_ingestor.NewsIngestor(api_key="test-key")
    batches = ingestor._build_domain_batches(None)

    assert batches
    assert len(batches) >= 2
    assert all(batch for batch in batches)


def test_news_ingestor_sanitizes_api_key_in_error_messages():
    key = "secret1234567890"
    ingestor = news_ingestor.NewsIngestor(api_key=key)
    sanitized = ingestor._sanitize_error_message(
        f"https://newsapi.org/v2/everything?apiKey={key}&q=geopolitics token={key}"
    )

    assert key not in sanitized
    assert "apiKey=[REDACTED]" in sanitized
    assert "[REDACTED]" in sanitized


def test_news_ingestor_filters_irrelevant_articles():
    ingestor = news_ingestor.NewsIngestor(api_key="test-key")
    articles = [
        {
            "title": "This interactive timeline shows every iPhone size ever released",
            "description": "A roundup of Apple devices.",
            "content": "Specs and product history.",
            "url": "https://example.test/iphone",
        },
        {
            "title": "Iran ceasefire talks continue in regional summit",
            "description": "Diplomats discussed de-escalation and security guarantees.",
            "content": "The meeting focused on conflict prevention.",
            "url": "https://example.test/iran-talks",
        },
    ]

    filtered = ingestor._filter_relevant_articles(articles, query="geopolitics")

    assert len(filtered) == 1
    assert filtered[0]["url"] == "https://example.test/iran-talks"


def test_run_realtime_parser_accepts_bare_interval_flag():
    parser = run_realtime.build_parser()
    args = parser.parse_args(["--query", "geopolitics", "--interval"])

    assert args.query == "geopolitics"
    assert args.interval == 60


def test_sentiment_analyzer_returns_deep_sentiment_fields():
    from src.analysis.sentiment import SentimentAnalyzer

    analyzer = SentimentAnalyzer(prefer_transformers=False)
    result = analyzer.analyze_text("A dangerous conflict raises security fears and diplomatic uncertainty.")

    assert "deep_label" in result
    assert "positive_percent" in result
    assert "negative_percent" in result
    assert "neutral_percent" in result


def test_realtime_loop_degrades_on_zero_article_error(monkeypatch, tmp_path):
    captured = {}

    class FakeSentiment:
        def __init__(self, *args, **kwargs):
            pass

        def analyze_text(self, _text):
            return {"label": "NEUTRAL", "score": 0.5}

    class FakeEmotion:
        def __init__(self, *args, **kwargs):
            pass

        def analyze_text(self, _text):
            return {"neutral": 1.0}

    def fake_run_stage1(**_kwargs):
        raise RuntimeError("Strict live mode failed: 0 articles fetched")

    def fake_persist(snapshot, output_dir):
        captured["snapshot"] = snapshot
        captured["output_dir"] = output_dir

    monkeypatch.setattr(live_monitor, "SentimentAnalyzer", FakeSentiment)
    monkeypatch.setattr(live_monitor, "EmotionAnalyzer", FakeEmotion)
    monkeypatch.setattr(live_monitor, "run_stage1", fake_run_stage1)
    monkeypatch.setattr(live_monitor, "_persist_snapshot", fake_persist)
    monkeypatch.setattr(live_monitor, "_render_snapshot", lambda *args, **kwargs: None)

    result = live_monitor.run_live_monitor(
        query="geopolitics",
        days_back=1,
        max_articles=5,
        interval_seconds=1,
        max_cycles=1,
        output_dir=tmp_path,
    )

    assert result["status"] == "degraded"
    assert result["articles_count"] == 0
    assert captured["snapshot"]["status"] == "degraded"


def test_realtime_loop_rotates_unseen_articles_across_cycles(monkeypatch, tmp_path):
    class FakeSentiment:
        def __init__(self, *args, **kwargs):
            pass

        def analyze_text(self, _text):
            return {
                "label": "NEGATIVE",
                "score": 0.81,
                "positive_percent": 8.0,
                "negative_percent": 78.0,
                "neutral_percent": 14.0,
                "intensity": 0.82,
                "valence": -0.7,
                "deep_label": "strongly_negative",
            }

    class FakeEmotion:
        def __init__(self, *args, **kwargs):
            pass

        def analyze_text(self, _text):
            return {"fear": 0.7, "neutral": 0.3}

    repeated_feed = {
        "articles": [
            {
                "title": "Headline A",
                "description": "Talks collapsed overnight.",
                "content": "Diplomats blamed security fears.",
                "source": "Reuters",
                "published_at": "2026-04-05T00:00:00Z",
                "url": "https://example.test/a",
            },
            {
                "title": "Headline B",
                "description": "Sanctions talks continue.",
                "content": "Officials warned of escalation.",
                "source": "BBC",
                "published_at": "2026-04-05T00:05:00Z",
                "url": "https://example.test/b",
            },
        ]
    }

    monkeypatch.setattr(
        live_monitor,
        "load_pipeline_config",
        lambda: {
            "topic": "geopolitics",
            "days_back": 1,
            "max_articles": 1,
            "poll_interval_seconds": 1,
            "realtime_max_headlines": 1,
        },
    )
    monkeypatch.setattr(
        live_monitor,
        "load_model_config",
        lambda: {
            "sentiment_model": "fake-sentiment",
            "emotion_model": "fake-emotion",
            "prefer_transformers": False,
        },
    )
    monkeypatch.setattr(live_monitor, "SentimentAnalyzer", FakeSentiment)
    monkeypatch.setattr(live_monitor, "EmotionAnalyzer", FakeEmotion)
    monkeypatch.setattr(live_monitor, "run_stage1", lambda **_kwargs: repeated_feed)
    monkeypatch.setattr(live_monitor, "_render_snapshot", lambda *args, **kwargs: None)
    monkeypatch.setattr(live_monitor.time, "sleep", lambda _seconds: None)

    live_monitor.run_live_monitor(
        query="geopolitics",
        days_back=1,
        max_articles=1,
        interval_seconds=1,
        max_cycles=2,
        output_dir=tmp_path,
    )

    history_file = tmp_path / "live_history.jsonl"
    history_rows = [json.loads(line) for line in history_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(history_rows) == 2
    assert history_rows[0]["headlines"][0]["url"] == "https://example.test/a"
    assert history_rows[1]["headlines"][0]["url"] == "https://example.test/b"
    assert history_rows[1]["new_articles_count"] == 1
    assert history_rows[1]["seen_articles_skipped"] == 1
