"""
Streamlit dashboard for live news snapshots.

Run:
    streamlit run src/realtime/dashboard.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st


SNAPSHOT_PATH = Path("data/processed/realtime/live_snapshot.json")


def _load_snapshot() -> dict:
    if not SNAPSHOT_PATH.exists():
        return {}
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _render_snapshot(snapshot: dict) -> None:
    if not snapshot:
        st.warning("No live snapshot found yet. Start `python run_realtime.py` first.")
        return

    if "error" in snapshot:
        st.error(f"Latest cycle failed: {snapshot['error']}")
        st.caption(f"Cycle: {snapshot.get('cycle', '-')}, time: {snapshot.get('generated_at', '-')}")
        return

    st.caption(
        f"Cycle {snapshot.get('cycle', '-')} | Updated: {snapshot.get('generated_at', '-')} | "
        f"Status: {snapshot.get('status', '-')}"
    )
    st.write(f"**Query:** {snapshot.get('query', '-')}")
    if snapshot.get("message"):
        st.info(snapshot["message"])

    sentiment_summary = snapshot.get("deep_sentiment_summary", {})
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("New Headlines", snapshot.get("new_articles_count", snapshot.get("article_count", 0)))
    col2.metric("Fetched", snapshot.get("fetched_articles_count", snapshot.get("article_count", 0)))
    col3.metric("Seen Skipped", snapshot.get("seen_articles_skipped", 0))
    col4.metric("Avg Trust %", snapshot.get("average_trust_percent", 0.0))
    col5.metric("Avg Intensity", sentiment_summary.get("average_intensity", 0.0))

    st.subheader("Sentiment Distribution")
    st.json(snapshot.get("sentiment_distribution", {}))

    st.subheader("Deep Sentiment Distribution")
    st.json(snapshot.get("deep_sentiment_distribution", {}))

    st.subheader("Deep Sentiment Summary")
    st.json(snapshot.get("deep_sentiment_summary", {}))

    st.subheader("Dominant Emotion Distribution")
    st.json(snapshot.get("emotion_distribution", {}))

    st.subheader("Top Sources")
    st.json(snapshot.get("top_sources", {}))

    headlines = snapshot.get("headlines", [])
    if headlines:
        frame = pd.DataFrame(headlines)
        if "sentiment_profile" in frame.columns:
            profile_frame = pd.json_normalize(frame["sentiment_profile"]).rename(
                columns={
                    "positive_percent": "positive_percent",
                    "negative_percent": "negative_percent",
                    "neutral_percent": "neutral_percent",
                    "intensity": "sentiment_intensity",
                    "valence": "sentiment_valence",
                }
            )
            frame = pd.concat([frame.drop(columns=["sentiment_profile"]), profile_frame], axis=1)
        preferred_columns = [
            "source",
            "trust_percent",
            "sentiment",
            "deep_sentiment",
            "positive_percent",
            "negative_percent",
            "neutral_percent",
            "sentiment_intensity",
            "sentiment_valence",
            "dominant_emotion",
            "sentiment_detail",
            "published_at",
            "title",
            "url",
        ]
        existing_columns = [col for col in preferred_columns if col in frame.columns]
        st.subheader("Latest Headlines")
        st.dataframe(frame[existing_columns], use_container_width=True, hide_index=True)
    else:
        st.warning("No unseen headlines were available in the latest refresh. The monitor skipped previously shown items.")


def main() -> None:
    st.set_page_config(page_title="GNS Live Dashboard", layout="wide")
    st.title("GNS Live News Dashboard")

    auto_refresh = st.sidebar.toggle("Auto Refresh", value=True)
    interval = st.sidebar.slider("Refresh Interval (sec)", min_value=10, max_value=300, value=60, step=5)
    st.sidebar.caption("Run `python run_realtime.py` in another terminal to keep snapshots fresh.")

    snapshot = _load_snapshot()
    _render_snapshot(snapshot)

    if auto_refresh:
        time.sleep(interval)
        st.rerun()


if __name__ == "__main__":
    main()
