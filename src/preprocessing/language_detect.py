"""
Language detection with a safe fallback.
"""

from typing import Dict, Iterable, List

try:
    from langdetect import DetectorFactory, detect

    DetectorFactory.seed = 0
except Exception:  # pragma: no cover - optional dependency failure
    detect = None


class LanguageDetector:
    """Detect text language for multilingual routing."""

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language

    def detect_language(self, text: str) -> str:
        """Return an ISO language code or a configured default."""
        if not text or not text.strip():
            return self.default_language

        if detect is not None:
            try:
                return detect(text)
            except Exception:
                pass

        ascii_chars = sum(1 for char in text if ord(char) < 128)
        ratio = ascii_chars / max(len(text), 1)
        return "en" if ratio > 0.8 else self.default_language

    def detect_many(self, texts: Iterable[str]) -> List[str]:
        """Detect languages for a list of texts."""
        return [self.detect_language(text) for text in texts]

    def summarize(self, texts: Iterable[str]) -> Dict[str, int]:
        """Return counts by detected language."""
        counts: Dict[str, int] = {}
        for language in self.detect_many(texts):
            counts[language] = counts.get(language, 0) + 1
        return counts
