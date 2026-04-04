"""
Source credibility scoring for evidence ranking.
"""

from typing import Dict, Iterable, List


class SourceCredibilityScorer:
    """Assign a rough credibility score to named sources."""

    SOURCE_SCORES = {
        "reuters": 0.95,
        "associated press": 0.95,
        "ap": 0.95,
        "bbc": 0.92,
        "npr": 0.9,
        "new scientist": 0.9,
        "al jazeera": 0.86,
        "the times of india": 0.76,
        "rt": 0.35,
        "factcheck.org": 0.9,
        "who": 0.98,
        "un": 0.97,
        "opcw": 0.97,
        "international idea": 0.9,
        "peer reviewed": 0.93,
        "academic source": 0.9,
    }

    def score(self, source: str, url: str = "") -> float:
        """Score a source by name and url tokens."""
        haystack = f"{source} {url}".lower()
        for token, score in self.SOURCE_SCORES.items():
            if token in haystack:
                return score
        return 0.65

    def annotate(self, evidence: Iterable[Dict]) -> List[Dict]:
        """Attach credibility scores to a list of evidence items."""
        annotated = []
        for item in evidence:
            record = dict(item)
            record["credibility_score"] = round(
                float(record.get("credibility_score", self.score(record.get("source", ""), record.get("url", "")))),
                4,
            )
            annotated.append(record)
        return annotated
