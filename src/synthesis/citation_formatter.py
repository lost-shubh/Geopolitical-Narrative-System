"""
Citation formatting helpers for generated narratives.
"""

from typing import Dict, Iterable, List


class CitationFormatter:
    """Format inline citations and bibliographies."""

    def format_inline(self, evidence: Dict, index: int | None = None) -> str:
        prefix = f"[{index}] " if index is not None else ""
        source = evidence.get("source", "Unknown source")
        title = evidence.get("title", "Untitled")
        return f"{prefix}{source}: {title}"

    def format_bibliography(self, evidence_items: Iterable[Dict]) -> List[str]:
        bibliography = []
        for index, item in enumerate(evidence_items, start=1):
            bibliography.append(
                f"{index}. {item.get('source', 'Unknown source')} | "
                f"{item.get('title', 'Untitled')} | {item.get('url', '')}"
            )
        return bibliography
