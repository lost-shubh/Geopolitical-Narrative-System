"""
Comment collection and topic filtering helpers.
"""

from typing import Dict, List, Sequence, Set


class CommentCollector:
    """Filter bundled social reactions down to comments relevant to the news set."""

    TOPIC_KEYWORDS = {
        "ukraine_russia": {"ukraine", "russia", "europe", "gas", "pipeline"},
        "china_taiwan": {"china", "taiwan", "asia", "starlink", "semiconductor"},
        "middle_east": {"iran", "israel", "middle east", "gulf", "oil"},
        "nato": {"nato", "alliance", "article 5", "european security"},
        "elections": {"election", "interference", "democracy", "platforms"},
    }

    def infer_topics_from_articles(self, articles: Sequence[Dict]) -> Set[str]:
        """Infer which synthetic social topics are relevant to the article set."""
        inferred: Set[str] = set()
        haystack = " ".join(
            f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
            for article in articles
        ).lower()

        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(keyword in haystack for keyword in keywords):
                inferred.add(topic)

        return inferred or set(self.TOPIC_KEYWORDS.keys())

    def collect_relevant_comments(self, articles: Sequence[Dict], comments: Sequence[Dict], max_comments: int | None = None) -> List[Dict]:
        """Return comments that match inferred topics from the article set."""
        allowed_topics = self.infer_topics_from_articles(articles)
        filtered = [comment for comment in comments if comment.get("topic") in allowed_topics]
        if max_comments is not None:
            filtered = filtered[:max_comments]
        return filtered
