"""Pytest coverage for text preprocessing utilities."""

from src.preprocessing.clean_text import clean_text
from src.preprocessing.language_detect import LanguageDetector


def test_clean_text_normalizes_spacing():
    assert clean_text("Hello,\n\nworld   ") == "Hello, world"


def test_language_detector_defaults_to_english_for_ascii_text():
    detector = LanguageDetector()
    assert detector.detect_language("This is a short English sentence.") == "en"
