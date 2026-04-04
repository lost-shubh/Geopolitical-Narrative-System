"""
Emotion Analysis Module - Stage 3.
Detects specific emotions (anger, fear, joy, sadness, etc.) in text and
falls back to a lexical model when transformers are unavailable.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
import warnings

from tqdm import tqdm

try:
    from transformers import pipeline
except Exception:  # pragma: no cover - optional dependency failure
    pipeline = None

warnings.filterwarnings("ignore")


class EmotionAnalyzer:
    """Analyze emotions in text using transformers or lexical rules."""

    EMOTIONS = [
        "anger", "disgust", "fear", "joy",
        "neutral", "sadness", "surprise"
    ]

    EMOTION_KEYWORDS = {
        "anger": {"anger", "angry", "furious", "aggression", "rage", "frustration"},
        "disgust": {"disgust", "corruption", "snub", "biased", "unacceptable"},
        "fear": {"fear", "danger", "dangerous", "threat", "crisis", "war", "alarming"},
        "joy": {"joy", "hope", "progress", "peace", "solution", "good", "success"},
        "neutral": {"complex", "developing", "monitoring", "analysis", "report", "said"},
        "sadness": {"sadness", "devastating", "humanitarian", "suffer", "civilians", "tragic"},
        "surprise": {"surprise", "unexpected", "sudden", "shock", "remarkable", "unprecedented"},
    }

    def __init__(
        self,
        model_name: str = "j-hartmann/emotion-english-distilroberta-base",
        prefer_transformers: bool | None = None,
    ):
        """
        Initialize emotion analyzer.

        Args:
            model_name: Hugging Face model for emotion detection
            prefer_transformers: Force or disable transformer usage. When None,
                the analyzer prefers the heuristic backend unless
                GNS_ENABLE_TRANSFORMERS=1 is set.
        """
        env_pref = os.getenv("GNS_ENABLE_TRANSFORMERS", "0") == "1"
        self.prefer_transformers = env_pref if prefer_transformers is None else prefer_transformers
        self.backend = "heuristic"
        self.model = None

        if self.prefer_transformers and pipeline is not None:
            try:
                print(f"Loading emotion model: {model_name}")
                print("(Using transformer backend)")
                self.model = pipeline(
                    "text-classification",
                    model=model_name,
                    top_k=None,
                    device=-1,
                )
                self.backend = "transformers"
                print("Emotion model loaded successfully")
            except Exception as exc:
                print(f"Falling back to heuristic emotion analysis: {exc}")
        else:
            print("Using heuristic emotion analyzer")

    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        Analyze emotions in a single text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping emotions to confidence scores
        """
        if not text or not text.strip():
            return {emotion: 0.0 for emotion in self.EMOTIONS}

        text = text[:512]

        if self.backend == "transformers" and self.model is not None:
            try:
                results = self.model(text)[0]
                return {
                    result["label"]: round(result["score"], 4)
                    for result in results
                }
            except Exception as exc:
                print(f"Error analyzing emotions with transformers: {exc}")

        return self._analyze_text_heuristic(text)

    def analyze_articles(self, articles: List[Dict], fields: List[str] = None) -> List[Dict]:
        """
        Analyze emotions in news articles.

        Args:
            articles: List of article dictionaries
            fields: Which fields to analyze

        Returns:
            Articles with added emotion analysis
        """
        if fields is None:
            fields = ["title", "description"]

        print(f"\nAnalyzing emotions in {len(articles)} articles...")
        print(f"Fields to analyze: {fields}")

        analyzed_articles = []

        for article in tqdm(articles, desc="Analyzing emotions"):
            article_copy = article.copy()
            article_copy["emotion_analysis"] = {}

            for field in fields:
                text = article.get(field, "")
                if text and text.strip():
                    article_copy["emotion_analysis"][field] = self.analyze_text(text)

            if article_copy["emotion_analysis"]:
                overall_emotions = {}

                for emotion in self.EMOTIONS:
                    scores = []
                    for field_emotions in article_copy["emotion_analysis"].values():
                        if emotion in field_emotions:
                            scores.append(field_emotions[emotion])

                    if scores:
                        overall_emotions[emotion] = round(sum(scores) / len(scores), 4)

                if overall_emotions:
                    dominant = max(overall_emotions.items(), key=lambda item: item[1])
                    overall_emotions["dominant_emotion"] = dominant[0]
                    overall_emotions["dominant_score"] = dominant[1]

                article_copy["emotion_analysis"]["overall"] = overall_emotions

            analyzed_articles.append(article_copy)

        return analyzed_articles

    def get_emotion_statistics(self, analyzed_articles: List[Dict]) -> Dict:
        """
        Calculate emotion statistics across articles.

        Args:
            analyzed_articles: Articles with emotion analysis

        Returns:
            Statistics dictionary
        """
        if not analyzed_articles:
            return {}

        emotion_totals = {emotion: [] for emotion in self.EMOTIONS}
        dominant_emotions = []

        for article in analyzed_articles:
            overall = article.get("emotion_analysis", {}).get("overall", {})

            if overall:
                for emotion in self.EMOTIONS:
                    if emotion in overall:
                        emotion_totals[emotion].append(overall[emotion])

                if "dominant_emotion" in overall:
                    dominant_emotions.append(overall["dominant_emotion"])

        emotion_averages = {
            emotion: round(sum(scores) / len(scores), 4) if scores else 0.0
            for emotion, scores in emotion_totals.items()
        }
        dominant_counts = {
            emotion: dominant_emotions.count(emotion)
            for emotion in set(dominant_emotions)
        }
        dominant_sorted = sorted(
            dominant_counts.items(),
            key=lambda item: item[1],
            reverse=True
        )

        return {
            "total_analyzed": len(analyzed_articles),
            "average_emotions": emotion_averages,
            "dominant_emotion_counts": dict(dominant_sorted),
            "most_common_emotion": dominant_sorted[0][0] if dominant_sorted else None,
            "emotion_distribution": {
                emotion: round(count / len(dominant_emotions) * 100, 2)
                for emotion, count in dominant_counts.items()
            } if dominant_emotions else {}
        }

    def _analyze_text_heuristic(self, text: str) -> Dict[str, float]:
        """Estimate emotion scores using keyword matches."""
        lowered = text.lower()
        raw_scores = {}

        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword in lowered)
            raw_scores[emotion] = float(matches)

        if not any(raw_scores.values()):
            raw_scores["neutral"] = 1.0

        total = sum(raw_scores.values()) or 1.0
        return {
            emotion: round(raw_scores.get(emotion, 0.0) / total, 4)
            for emotion in self.EMOTIONS
        }


def load_articles_from_json(filepath: str) -> List[Dict]:
    """Load articles from JSON file."""
    with open(filepath, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, dict) and "articles" in data:
        return data["articles"]
    if isinstance(data, list):
        return data
    return []


def save_analyzed_articles(articles: List[Dict], output_path: str):
    """Save analyzed articles to JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump({
            "total_articles": len(articles),
            "articles": articles
        }, handle, indent=2, ensure_ascii=False)

    print(f"Saved emotion analysis to: {output_path}")


def main():
    """Example usage of EmotionAnalyzer."""
    print("=" * 60)
    print("EMOTION ANALYSIS - STAGE 3")
    print("=" * 60)
    print()

    analyzer = EmotionAnalyzer()
    input_file = "data/raw/news/test_articles.json"

    if not Path(input_file).exists():
        print(f"Error: {input_file} not found")
        print("\nPlease run Stage 1 first:")
        print("  python test_news_ingestion.py")
        return

    print(f"\nLoading articles from: {input_file}")
    articles = load_articles_from_json(input_file)
    print(f"Loaded {len(articles)} articles")

    analyzed_articles = analyzer.analyze_articles(
        articles,
        fields=["title", "description"]
    )

    print("\n" + "=" * 60)
    print("EMOTION STATISTICS")
    print("=" * 60)

    stats = analyzer.get_emotion_statistics(analyzed_articles)

    print(f"\nTotal articles analyzed: {stats['total_analyzed']}")
    print(f"Most common emotion: {stats['most_common_emotion']}")

    print("\nEmotion Distribution:")
    for emotion, percentage in sorted(
        stats["emotion_distribution"].items(),
        key=lambda item: item[1],
        reverse=True
    ):
        print(f"  {emotion:10s}: {percentage:5.1f}%")

    print("\nAverage Emotion Scores:")
    for emotion, score in sorted(
        stats["average_emotions"].items(),
        key=lambda item: item[1],
        reverse=True
    ):
        print(f"  {emotion:10s}: {score:.4f}")

    print("\n" + "=" * 60)
    print("SAMPLE ANALYSIS")
    print("=" * 60)

    for i, article in enumerate(analyzed_articles[:3], 1):
        print(f"\n[{i}] {article.get('title', 'No title')[:60]}...")

        overall = article.get("emotion_analysis", {}).get("overall", {})
        if overall:
            dominant = overall.get("dominant_emotion", "Unknown")
            score = overall.get("dominant_score", 0.0)
            print(f"    Dominant Emotion: {dominant.upper()} (confidence: {score})")

            emotion_scores = {
                key: value
                for key, value in overall.items()
                if key not in ["dominant_emotion", "dominant_score"]
            }
            top_3 = sorted(emotion_scores.items(), key=lambda item: item[1], reverse=True)[:3]
            print("    Top emotions:")
            for emotion, value in top_3:
                print(f"      - {emotion}: {value}")

    output_file = "data/processed/emotion_analysis/analyzed_articles.json"
    save_analyzed_articles(analyzed_articles, output_file)

    print("\n" + "=" * 60)
    print("EMOTION ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
