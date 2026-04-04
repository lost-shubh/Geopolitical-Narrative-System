"""
Local evidence retrieval against the bundled news corpus.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Sequence

from .source_credibility import SourceCredibilityScorer


class FactFinder:
    """Retrieve relevant evidence from locally available articles."""

    STOPWORDS = {
        "the", "and", "with", "from", "that", "this", "have", "will", "about",
        "into", "over", "more", "than", "their", "they", "them", "said", "says",
        "claim", "claims", "reported", "report", "fact", "check",
    }

    def __init__(self, articles: Sequence[Dict] | None = None):
        self.credibility = SourceCredibilityScorer()
        self.articles = list(articles) if articles else self._load_local_articles()

    def _load_local_articles(self) -> List[Dict]:
        """Load bundled article sets from disk."""
        candidates = [
            Path("data/raw/news/pipeline_news.json"),
            Path("data/raw/news/test_articles.json"),
        ]
        articles: List[Dict] = []
        for path in candidates:
            if not path.exists():
                continue
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            for article in data.get("articles", data if isinstance(data, list) else []):
                if article not in articles:
                    articles.append(article)
        return articles

    def search_claim(self, claim_text: str, claim_type: str = "unknown", max_results: int = 5) -> List[Dict]:
        """Return local evidence items sorted by relevance."""
        terms = self._extract_terms(claim_text)
        ranked: List[Dict] = []

        for article in self.articles:
            combined = " ".join(
                [
                    article.get("title", ""),
                    article.get("description", ""),
                    article.get("content", ""),
                ]
            )
            relevance = self._score_overlap(terms, combined)
            if relevance <= 0:
                continue

            source = article.get("source", "Unknown")
            stance = self._infer_stance(claim_text, combined, claim_type)
            ranked.append(
                {
                    "title": article.get("title", "Local article match"),
                    "source": source,
                    "url": article.get("url", ""),
                    "snippet": article.get("description") or article.get("content", "")[:220],
                    "credibility_score": self.credibility.score(source, article.get("url", "")),
                    "relevance_score": round(relevance, 4),
                    "stance": stance,
                    "evidence_type": "local_news",
                }
            )

        ranked.sort(
            key=lambda item: (item["relevance_score"], item["credibility_score"]),
            reverse=True,
        )
        return ranked[:max_results]

    def _extract_terms(self, text: str) -> List[str]:
        words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower())
        return [word for word in words if word not in self.STOPWORDS][:12]

    def _score_overlap(self, terms: Sequence[str], text: str) -> float:
        haystack = text.lower()
        if not terms:
            return 0.0
        hits = sum(1 for term in terms if term in haystack)
        return hits / len(terms)

    def _infer_stance(self, claim_text: str, evidence_text: str, claim_type: str) -> str:
        lowered_claim = claim_text.lower()
        lowered_evidence = evidence_text.lower()

        if any(token in lowered_evidence for token in ("denied", "no evidence", "disputed", "investigating")):
            return "contradict"
        if claim_type in {"statistical", "casualty_report"} and re.search(r"\b\d+\b", lowered_evidence):
            return "support"
        if any(token in lowered_claim for token in ("secret", "alleged", "accuse", "propaganda")):
            return "neutral"
        return "support"
