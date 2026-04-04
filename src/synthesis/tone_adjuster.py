"""
Simple tone controls for generated narratives.
"""


class ToneAdjuster:
    """Adjust generated text for different audiences."""

    TONE_PREFIXES = {
        "analytical": "Assessment:",
        "public": "What this means:",
        "policy": "Policy note:",
    }

    def adjust(self, text: str, tone: str = "analytical") -> str:
        """Prefix and lightly reshape output tone."""
        prefix = self.TONE_PREFIXES.get(tone, self.TONE_PREFIXES["analytical"])
        if text.startswith(prefix):
            return text
        return f"{prefix}\n{text}"
