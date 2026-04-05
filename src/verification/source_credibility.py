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
        "bbc news": 0.92,
        "apnews": 0.95,
        "al jazeera": 0.86,
        "aljazeera": 0.86,
        "the guardian": 0.9,
        "guardian": 0.9,
        "financial times": 0.93,
        "ft.com": 0.93,
        "wall street journal": 0.92,
        "wsj": 0.92,
        "new york times": 0.9,
        "nytimes": 0.9,
        "washington post": 0.89,
        "bloomberg": 0.92,
        "economist": 0.93,
        "foreign policy": 0.89,
        "france24": 0.86,
        "france 24": 0.86,
        "dw.com": 0.86,
        "deutsche welle": 0.86,
        "channelnewsasia": 0.88,
        "channel news asia": 0.88,
        "nikkei": 0.9,
        "south china morning post": 0.82,
        "scmp": 0.82,
        "the hindu": 0.84,
        "hindustan times": 0.79,
        "times of india": 0.76,
        "economic times": 0.78,
        "the irish times": 0.86,
        "politico": 0.84,
        "cnn": 0.78,
        "abc news": 0.83,
        "cbs news": 0.83,
        "nbc news": 0.83,
        "npr": 0.9,
        "new scientist": 0.9,
        "the times of india": 0.76,
        "rt": 0.35,
        "naturalnews": 0.2,
        "bitcoinist": 0.3,
        "oilprice": 0.55,
        "globalsecurity": 0.72,
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
