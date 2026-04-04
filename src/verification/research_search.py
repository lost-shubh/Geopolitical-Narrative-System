"""
Template-backed research and institutional source retrieval.
"""

from typing import Dict, List

from .source_credibility import SourceCredibilityScorer


class ResearchSearch:
    """Return high-credibility research-style context for a claim."""

    KNOWLEDGE_BASE = {
        "ukraine": [
            {
                "title": "OSINT and conflict verification practices",
                "source": "Peer Reviewed Security Studies",
                "snippet": "Independent verification of battlefield claims requires corroboration across multiple open-source and institutional datasets.",
                "url": "https://example.org/research/osint-conflict-verification",
                "stance": "neutral",
            }
        ],
        "iran": [
            {
                "title": "IAEA and regional security reporting methods",
                "source": "UN",
                "snippet": "Security accusations in the region are typically assessed through formal inspections, public statements, and multilateral reporting.",
                "url": "https://example.org/un/regional-security-reporting",
                "stance": "neutral",
            }
        ],
        "election": [
            {
                "title": "Election monitoring and foreign influence indicators",
                "source": "International IDEA",
                "snippet": "Election interference claims are strongest when supported by technical forensics, coordinated-behavior analysis, and independent observation.",
                "url": "https://example.org/idea/election-monitoring",
                "stance": "neutral",
            }
        ],
        "default": [
            {
                "title": "Fact-checking standards for geopolitical reporting",
                "source": "FactCheck.org",
                "snippet": "Claims should be evaluated against primary reporting, institutional records, and corroborating independent sources.",
                "url": "https://example.org/factcheck/geopolitical-reporting-standards",
                "stance": "neutral",
            }
        ],
    }

    def __init__(self):
        self.credibility = SourceCredibilityScorer()

    def search(self, claim_text: str, entities: Dict | None = None, max_results: int = 3) -> List[Dict]:
        """Return research-style evidence matched to the claim topic."""
        claim_lower = claim_text.lower()
        key = "default"
        for candidate in ("ukraine", "iran", "election"):
            if candidate in claim_lower:
                key = candidate
                break

        results = []
        for item in self.KNOWLEDGE_BASE.get(key, self.KNOWLEDGE_BASE["default"])[:max_results]:
            record = dict(item)
            record["credibility_score"] = self.credibility.score(record["source"], record["url"])
            record["relevance_score"] = 0.72 if key != "default" else 0.55
            record["evidence_type"] = "research_context"
            if entities:
                record["entities_considered"] = entities
            results.append(record)
        return results
