"""
Named-entity extraction with spaCy and heuristic fallbacks.
"""

import re
from typing import Dict, Iterable, List

try:
    import spacy
except Exception:  # pragma: no cover - optional dependency failure
    spacy = None


class EntityExtractor:
    """Extract entities from text fields."""

    GEO_HINTS = {
        "ukraine", "russia", "iran", "china", "taiwan", "europe", "asia",
        "middle east", "israel", "germany", "india", "america", "us",
    }

    def __init__(self, model_name: str = "en_core_web_sm"):
        self.nlp = None
        if spacy is not None:
            try:
                self.nlp = spacy.load(model_name)
            except Exception:
                self.nlp = None

    def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from one text value."""
        if not text:
            return {}

        if self.nlp is not None:
            doc = self.nlp(text)
            entities: Dict[str, List[str]] = {}
            for ent in doc.ents:
                entities.setdefault(ent.label_, [])
                if ent.text not in entities[ent.label_]:
                    entities[ent.label_].append(ent.text)
            return entities

        entities = {"GPE": [], "ORG": [], "PERSON": [], "DATE": []}
        for match in re.findall(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text):
            lowered = match.lower()
            if lowered in self.GEO_HINTS:
                entities["GPE"].append(match)
            elif match in {"UN", "NATO", "EU", "WHO", "OPCW"}:
                entities["ORG"].append(match)
            else:
                entities["PERSON"].append(match)

        for date_match in re.findall(r"\b(?:19|20)\d{2}\b", text):
            entities["DATE"].append(date_match)

        return {label: sorted(set(values)) for label, values in entities.items() if values}

    def extract_from_fields(self, item: Dict, fields: Iterable[str]) -> Dict[str, List[str]]:
        """Merge entities from multiple text fields."""
        merged: Dict[str, List[str]] = {}
        for field in fields:
            for label, values in self.extract(item.get(field, "")).items():
                merged.setdefault(label, [])
                for value in values:
                    if value not in merged[label]:
                        merged[label].append(value)
        return merged
