"""
Offline-friendly social reaction ingestion.
Normalizes external social exports and can fall back to bundled mock data.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def _first_text_value(record: Dict, keys: List[str]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


class SocialIngestor:
    """Load or generate social reaction datasets."""

    def __init__(self, data_dir: str = "data/raw/social"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_comments(self, filepath: str | Path) -> List[Dict]:
        """Load comments from a JSON file."""
        path = Path(filepath)
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and "comments" in data:
            return data["comments"]
        if isinstance(data, list):
            return data
        return []

    def normalize_comment(self, comment: Dict, index: int) -> Dict | None:
        """Normalize a social export row to the Stage 3 comment schema."""
        text = _first_text_value(comment, ["text", "body", "comment", "content", "message"])
        if not text:
            return None

        platform = _first_text_value(comment, ["platform", "network", "source_platform"])
        if not platform and comment.get("subreddit"):
            platform = "reddit"
        platform = platform or "external"

        engagement = comment.get("engagement")
        if not isinstance(engagement, dict):
            engagement = {
                "likes": _safe_int(comment.get("likes") or comment.get("like_count") or comment.get("upvotes") or comment.get("score")),
                "retweets": _safe_int(comment.get("retweets") or comment.get("retweet_count") or comment.get("reposts")),
                "replies": _safe_int(comment.get("replies") or comment.get("reply_count") or comment.get("comments")),
                "shares": _safe_int(comment.get("shares") or comment.get("share_count")),
            }

        normalized = {
            "comment_id": str(comment.get("comment_id") or comment.get("id") or f"external_comment_{index}"),
            "text": text,
            "platform": platform,
            "topic": comment.get("topic") or comment.get("query") or "external",
            "language": comment.get("language") or comment.get("lang") or "en",
            "timestamp": comment.get("timestamp") or comment.get("created_at") or comment.get("published_at") or "",
            "source": comment.get("source") or comment.get("author") or comment.get("subreddit") or platform,
            "sentiment_hint": comment.get("sentiment_hint") or comment.get("sentiment") or "",
            "engagement": engagement,
        }
        if comment.get("url"):
            normalized["url"] = comment["url"]
        return normalized

    def load_normalized_comments(self, filepath: str | Path) -> List[Dict]:
        """Load comments from JSON and normalize them to the pipeline schema."""
        comments = self.load_comments(filepath)
        normalized = []
        for index, comment in enumerate(comments, start=1):
            if not isinstance(comment, dict):
                continue
            record = self.normalize_comment(comment, index)
            if record:
                normalized.append(record)
        return normalized

    def save_comments(self, comments: List[Dict], filename: str = "mock_social_comments.json", metadata: Optional[Dict] = None) -> str:
        """Persist comments using the project JSON format."""
        output_path = self.data_dir / filename
        payload = metadata.copy() if metadata else {}
        payload.update({
            "total_comments": len(comments),
            "comments": comments,
        })
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        return str(output_path)

    def load_or_generate(self, filename: str = "mock_social_comments.json") -> str:
        """Return an existing dataset or create one using the bundled generator."""
        output_path = self.data_dir / filename
        if output_path.exists():
            return str(output_path)

        import create_mock_data

        return str(create_mock_data.create_mock_social_dataset())
