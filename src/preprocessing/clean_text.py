"""
Text cleaning helpers used across ingestion and analysis stages.
"""

import html
import re
from typing import Dict, Iterable, List

URL_RE = re.compile(r"https?://\S+")
WHITESPACE_RE = re.compile(r"\s+")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def clean_text(
    text: str,
    *,
    lowercase: bool = False,
    strip_urls: bool = False,
    strip_control_chars: bool = True,
) -> str:
    """Normalize spacing and common noise in a piece of text."""
    if not text:
        return ""

    cleaned = html.unescape(text)
    if strip_urls:
        cleaned = URL_RE.sub("", cleaned)
    if strip_control_chars:
        cleaned = CONTROL_RE.sub(" ", cleaned)
    cleaned = cleaned.replace("\r", " ").replace("\n", " ")
    cleaned = WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned.lower() if lowercase else cleaned


def clean_article_fields(article: Dict, fields: Iterable[str] = ("title", "description", "content")) -> Dict:
    """Return a copy of an article with cleaned text fields."""
    cleaned = dict(article)
    for field in fields:
        cleaned[field] = clean_text(article.get(field, ""))
    return cleaned


def normalize_texts(texts: List[str], **kwargs) -> List[str]:
    """Clean a batch of strings with shared options."""
    return [clean_text(text, **kwargs) for text in texts]
