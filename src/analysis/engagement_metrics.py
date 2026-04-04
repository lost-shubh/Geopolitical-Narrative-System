"""
Engagement and virality helpers for social reactions.
"""

from typing import Dict, List


class EngagementMetricsAnalyzer:
    """Compute engagement totals and simple virality estimates."""

    def analyze_comments(self, comments: List[Dict], top_n: int = 5) -> Dict:
        """Aggregate engagement metrics from social comments."""
        if not comments:
            return {
                "total_interactions": 0,
                "average_interactions": 0.0,
                "top_comments": [],
                "platform_totals": {},
                "virality_score": 0.0,
            }

        platform_totals: Dict[str, int] = {}
        enriched = []
        total_interactions = 0

        for comment in comments:
            engagement = comment.get("engagement", {})
            interactions = sum(
                int(engagement.get(metric, 0))
                for metric in ("likes", "retweets", "replies", "shares")
            )
            platform = comment.get("platform", "unknown")
            platform_totals[platform] = platform_totals.get(platform, 0) + interactions
            total_interactions += interactions

            item = dict(comment)
            item["total_engagement"] = interactions
            item["virality"] = round(min(interactions / 250.0, 1.0), 4)
            enriched.append(item)

        average_interactions = total_interactions / len(comments)
        virality_score = round(min(average_interactions / 120.0, 1.0), 4)
        top_comments = sorted(enriched, key=lambda item: item["total_engagement"], reverse=True)[:top_n]

        return {
            "total_interactions": total_interactions,
            "average_interactions": round(average_interactions, 2),
            "platform_totals": platform_totals,
            "virality_score": virality_score,
            "top_comments": [
                {
                    "comment_id": item.get("comment_id"),
                    "text": item.get("text", "")[:160],
                    "platform": item.get("platform"),
                    "topic": item.get("topic"),
                    "total_engagement": item["total_engagement"],
                    "virality": item["virality"],
                }
                for item in top_comments
            ],
        }
