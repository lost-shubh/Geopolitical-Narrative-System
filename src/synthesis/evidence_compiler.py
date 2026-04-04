"""
Helpers for converting evidence into narrative-ready bullet points.
"""

from typing import Dict

from .citation_formatter import CitationFormatter


class EvidenceCompiler:
    """Compile supporting evidence into concise summary points."""

    def __init__(self):
        self.citations = CitationFormatter()

    def compile(self, verified_claim: Dict, max_items: int = 3) -> Dict:
        """Build summary bullets, citations, and evidence stats."""
        evidence = verified_claim.get("evidence", [])[:max_items]
        bullet_points = []

        for index, item in enumerate(evidence, start=1):
            citation = self.citations.format_inline(item, index=index)
            snippet = item.get("snippet", "No summary available").strip()
            bullet_points.append(f"{citation}. {snippet}")

        return {
            "bullet_points": bullet_points,
            "bibliography": self.citations.format_bibliography(evidence),
            "source_count": len(evidence),
        }
