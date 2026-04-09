from __future__ import annotations

from pathlib import Path

import src.realtime.publish_live_snapshot as publisher


def test_generate_live_snapshot_returns_degraded_payload_when_stage1_fails(monkeypatch):
    monkeypatch.setattr(publisher, "load_pipeline_config", lambda: {"topic": "geopolitics", "days_back": 1, "max_articles": 5, "realtime_max_headlines": 3})
    monkeypatch.setattr(
        publisher,
        "load_model_config",
        lambda: {
            "sentiment_model": "fake-sentiment",
            "emotion_model": "fake-emotion",
            "prefer_transformers": False,
        },
    )
    monkeypatch.setattr(publisher, "run_stage1", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("401 from NewsAPI")))

    snapshot = publisher.generate_live_snapshot(query="geopolitics")

    assert snapshot["status"] == "degraded"
    assert snapshot["query"] == "geopolitics"
    assert "401 from NewsAPI" in snapshot["error"]


def test_publish_snapshot_persists_locally_when_upload_is_skipped(monkeypatch, tmp_path):
    monkeypatch.setattr(
        publisher,
        "generate_live_snapshot",
        lambda **_kwargs: {
            "schema_version": 1,
            "status": "ok",
            "generated_at": "2026-04-09T00:00:00",
            "last_updated": "2026-04-09T00:00:00",
            "published_at": "2026-04-09T00:00:00",
            "cycle": 1,
            "query": "geopolitics",
            "articles_count": 1,
            "article_count": 1,
            "fetched_articles_count": 2,
            "new_articles_count": 1,
            "seen_articles_skipped": 0,
            "message": "",
            "sentiment_distribution": {"NEGATIVE": 1},
            "deep_sentiment_distribution": {"strongly_negative": 1},
            "deep_sentiment_summary": {"average_intensity": 0.8},
            "emotion_distribution": {"fear": 1},
            "average_trust_percent": 91.2,
            "top_sources": {"Reuters": 1},
            "headlines": [{"title": "Talks collapse", "source": "Reuters"}],
        },
    )

    result = publisher.publish_snapshot(skip_upload=True, output_dir=tmp_path)

    snapshot_file = tmp_path / "live_snapshot.json"
    history_file = tmp_path / "live_history.jsonl"
    assert result["status"] == "ok"
    assert Path(result["local_snapshot_file"]) == snapshot_file
    assert snapshot_file.exists()
    assert history_file.exists()
