"""
Polarization analysis helpers.
Measures how sharply split reaction data is across sentiment and topics.
"""

from typing import Dict, List


class PolarizationAnalyzer:
    """Compute lightweight polarization metrics for reaction data."""

    def analyze_comments(self, comments: List[Dict]) -> Dict:
        """Summarize ideological fragmentation from labeled comments."""
        if not comments:
            return {
                "score": 0.0,
                "level": "low",
                "label_distribution": {},
                "topic_distribution": {},
                "platform_distribution": {},
            }

        label_counts: Dict[str, int] = {}
        topic_counts: Dict[str, int] = {}
        platform_counts: Dict[str, int] = {}

        for comment in comments:
            label = (
                comment.get("sentiment", {}).get("label")
                or comment.get("sentiment_analysis", {}).get("overall", {}).get("label")
                or "NEUTRAL"
            )
            topic = comment.get("topic", "unknown")
            platform = comment.get("platform", "unknown")
            label_counts[label] = label_counts.get(label, 0) + 1
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

        total = len(comments)
        pos = label_counts.get("POSITIVE", 0) / total
        neg = label_counts.get("NEGATIVE", 0) / total
        neutral = label_counts.get("NEUTRAL", 0) / total
        confrontation = min(pos, neg) * 2
        fragmentation = len(topic_counts) / max(total, 1)
        score = round(min((confrontation * 0.8) + (fragmentation * 5.0) + ((1 - neutral) * 0.2), 1.0), 4)

        if score >= 0.7:
            level = "high"
        elif score >= 0.4:
            level = "medium"
        else:
            level = "low"

        return {
            "score": score,
            "level": level,
            "label_distribution": {label: round(count / total * 100, 2) for label, count in label_counts.items()},
            "topic_distribution": {topic: round(count / total * 100, 2) for topic, count in topic_counts.items()},
            "platform_distribution": {platform: round(count / total * 100, 2) for platform, count in platform_counts.items()},
        }
