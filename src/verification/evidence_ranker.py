"""
Evidence ranking and deduplication.
"""

from typing import Dict, Iterable, List


class EvidenceRanker:
    """Rank evidence by credibility, relevance, and stance strength."""

    STANCE_WEIGHTS = {
        "support": 1.0,
        "neutral": 0.6,
        "contradict": 1.0,
    }

    def rank(self, evidence: Iterable[Dict], max_results: int = 5) -> List[Dict]:
        """Return ranked evidence records."""
        deduped: List[Dict] = []
        seen = set()

        for item in evidence:
            fingerprint = (
                item.get("url"),
                item.get("source"),
                item.get("title"),
            )
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            record = dict(item)
            record["ranking_score"] = round(self._score(record), 4)
            deduped.append(record)

        deduped.sort(key=lambda item: item["ranking_score"], reverse=True)
        return deduped[:max_results]

    def _score(self, item: Dict) -> float:
        credibility = float(item.get("credibility_score", 0.6))
        relevance = float(item.get("relevance_score", 0.5))
        stance = self.STANCE_WEIGHTS.get(item.get("stance", "neutral"), 0.6)
        return (credibility * 0.55) + (relevance * 0.3) + (stance * 0.15)
