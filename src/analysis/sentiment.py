"""
Sentiment Analysis Module - Stage 3.
Analyzes sentiment (positive/negative/neutral) in news articles and comments.
Falls back to a deterministic lexical model when transformers are unavailable.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Union
import warnings

from tqdm import tqdm

try:
    from transformers import pipeline
except Exception:  # pragma: no cover - optional dependency failure
    pipeline = None

warnings.filterwarnings("ignore")


class SentimentAnalyzer:
    """Analyze sentiment in text using transformers or a lexical fallback."""

    POSITIVE_WORDS = {
        "peace", "progress", "hope", "optimistic", "cooperate", "stability",
        "resilient", "success", "agreement", "diplomatic", "solution",
        "reassure", "trusted", "improve", "support", "credible",
    }
    NEGATIVE_WORDS = {
        "war", "conflict", "crisis", "danger", "dangerous", "fear", "anger",
        "escalation", "attack", "attacking", "aggression", "threat",
        "devastating", "humanitarian", "bias", "propaganda", "sanctions",
        "uncertain", "worse", "hostile", "disputed", "weapon", "casualty",
        "distrust", "concern", "alarming",
    }
    UNCERTAINTY_WORDS = {
        "uncertain", "developing", "reportedly", "may", "might", "could",
        "risk", "volatile", "questions", "warning", "fragile", "tensions",
    }

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased-finetuned-sst-2-english",
        prefer_transformers: bool | None = None,
    ):
        """
        Initialize sentiment analyzer.

        Args:
            model_name: Hugging Face model to use for sentiment analysis
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
                os.environ.setdefault("DISABLE_SAFETENSORS_CONVERSION", "1")
                print(f"Loading sentiment model: {model_name}")
                print("(Using transformer backend)")
                self.model = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    device=-1,
                    use_safetensors=False,
                )
                self.backend = "transformers"
                print("Sentiment model loaded successfully")
            except Exception as exc:
                print(f"Falling back to heuristic sentiment analysis: {exc}")
        else:
            print("Using heuristic sentiment analyzer")

    def analyze_text(self, text: str) -> Dict[str, Union[str, float]]:
        """
        Analyze sentiment of a single text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with label and score
        """
        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.0}

        text = text[:512]

        if self.backend == "transformers" and self.model is not None:
            try:
                result = self.model(text)[0]
                base_result = {
                    "label": result["label"],
                    "score": round(result["score"], 4)
                }
                return self._augment_transformer_result(base_result)
            except Exception as exc:
                print(f"Error analyzing text with transformers: {exc}")

        return self._analyze_text_heuristic(text)

    def analyze_batch(self, texts: List[str], batch_size: int = 8) -> List[Dict]:
        """
        Analyze sentiment of multiple texts.

        Args:
            texts: List of texts to analyze
            batch_size: Number of texts to process at once

        Returns:
            List of sentiment results
        """
        results = []

        print(f"Analyzing {len(texts)} texts...")

        for i in tqdm(range(0, len(texts), batch_size), desc="Processing batches"):
            batch = texts[i:i + batch_size]
            cleaned_batch = [
                text[:512] if text and text.strip() else ""
                for text in batch
            ]

            if self.backend == "transformers" and self.model is not None:
                try:
                    batch_results = self.model(cleaned_batch)
                    results.extend([
                        {
                            "label": result["label"],
                            "score": round(result["score"], 4)
                        }
                        for result in batch_results
                    ])
                    continue
                except Exception as exc:
                    print(f"Error in batch {i}: {exc}")

            results.extend([self._analyze_text_heuristic(text) for text in batch])

        return results

    def analyze_articles(self, articles: List[Dict], fields: List[str] = None) -> List[Dict]:
        """
        Analyze sentiment in news articles.

        Args:
            articles: List of article dictionaries
            fields: Which fields to analyze (default: ["title", "description"])

        Returns:
            Articles with added sentiment analysis
        """
        if fields is None:
            fields = ["title", "description"]

        print(f"\nAnalyzing sentiment in {len(articles)} articles...")
        print(f"Fields to analyze: {fields}")

        analyzed_articles = []

        for article in tqdm(articles, desc="Analyzing articles"):
            article_copy = article.copy()
            article_copy["sentiment_analysis"] = {}

            for field in fields:
                text = article.get(field, "")
                if text and text.strip():
                    article_copy["sentiment_analysis"][field] = self.analyze_text(text)

            sentiments = list(article_copy["sentiment_analysis"].values())
            if sentiments:
                labels = [item["label"] for item in sentiments]
                most_common = max(set(labels), key=labels.count)
                avg_score = sum(item["score"] for item in sentiments) / len(sentiments)
                article_copy["sentiment_analysis"]["overall"] = {
                    "label": most_common,
                    "score": round(avg_score, 4)
                }

            analyzed_articles.append(article_copy)

        return analyzed_articles

    def get_sentiment_statistics(self, analyzed_articles: List[Dict]) -> Dict:
        """
        Calculate sentiment statistics across articles.

        Args:
            analyzed_articles: Articles with sentiment analysis

        Returns:
            Statistics dictionary
        """
        if not analyzed_articles:
            return {}

        sentiments = []
        for article in analyzed_articles:
            overall = article.get("sentiment_analysis", {}).get("overall")
            if overall:
                sentiments.append(overall)

        if not sentiments:
            return {}

        positive = sum(1 for item in sentiments if item["label"] == "POSITIVE")
        negative = sum(1 for item in sentiments if item["label"] == "NEGATIVE")
        neutral = len(sentiments) - positive - negative
        avg_score = sum(item["score"] for item in sentiments) / len(sentiments)
        avg_positive = sum(float(item.get("positive_percent", 0.0)) for item in sentiments) / len(sentiments)
        avg_negative = sum(float(item.get("negative_percent", 0.0)) for item in sentiments) / len(sentiments)
        avg_neutral = sum(float(item.get("neutral_percent", 0.0)) for item in sentiments) / len(sentiments)

        return {
            "total_analyzed": len(sentiments),
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "positive_percent": round(positive / len(sentiments) * 100, 2),
            "negative_percent": round(negative / len(sentiments) * 100, 2),
            "neutral_percent": round(neutral / len(sentiments) * 100, 2),
            "average_confidence": round(avg_score, 4),
            "average_positive_signal": round(avg_positive, 2),
            "average_negative_signal": round(avg_negative, 2),
            "average_neutral_signal": round(avg_neutral, 2),
        }

    def _analyze_text_heuristic(self, text: str) -> Dict[str, Union[str, float]]:
        """Score text with a lexical fallback model."""
        lowered = text.lower()
        positive_hits = sum(1 for word in self.POSITIVE_WORDS if word in lowered)
        negative_hits = sum(1 for word in self.NEGATIVE_WORDS if word in lowered)
        uncertainty_hits = sum(1 for word in self.UNCERTAINTY_WORDS if word in lowered)
        delta = positive_hits - negative_hits

        if delta > 0:
            label = "POSITIVE"
        elif delta < 0:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"

        magnitude = abs(delta)
        score = min(0.55 + magnitude * 0.12, 0.99) if magnitude else 0.5
        total_hits = positive_hits + negative_hits + uncertainty_hits

        if total_hits == 0:
            positive_percent = 20.0
            negative_percent = 20.0
            neutral_percent = 60.0
        else:
            positive_percent = round((positive_hits / total_hits) * 100, 2)
            negative_percent = round((negative_hits / total_hits) * 100, 2)
            neutral_percent = round((uncertainty_hits / total_hits) * 100, 2)
            spillover = round(max(0.0, 100.0 - (positive_percent + negative_percent + neutral_percent)), 2)
            neutral_percent = round(neutral_percent + spillover, 2)

        intensity = round(min((max(total_hits, magnitude) / 4.0), 1.0), 4)
        valence = round((positive_percent - negative_percent) / 100, 4)
        deep_label = self._derive_deep_label(label=label, valence=valence, intensity=intensity, neutral_percent=neutral_percent)

        return {
            "label": label,
            "score": round(score, 4),
            "positive_percent": positive_percent,
            "negative_percent": negative_percent,
            "neutral_percent": neutral_percent,
            "intensity": intensity,
            "valence": valence,
            "deep_label": deep_label,
        }

    def _augment_transformer_result(self, base_result: Dict[str, Union[str, float]]) -> Dict[str, Union[str, float]]:
        """Derive richer sentiment structure from a transformer label/score pair."""
        label = str(base_result.get("label", "NEUTRAL")).upper()
        score = float(base_result.get("score", 0.5))

        if label == "POSITIVE":
            positive_percent = round(score * 100, 2)
            negative_percent = round(max(0.0, (1 - score) * 35), 2)
        elif label == "NEGATIVE":
            negative_percent = round(score * 100, 2)
            positive_percent = round(max(0.0, (1 - score) * 35), 2)
        else:
            positive_percent = 20.0
            negative_percent = 20.0

        neutral_percent = round(max(0.0, 100.0 - positive_percent - negative_percent), 2)
        intensity = round(max(abs(positive_percent - negative_percent) / 100, score), 4)
        valence = round((positive_percent - negative_percent) / 100, 4)
        deep_label = self._derive_deep_label(label=label, valence=valence, intensity=intensity, neutral_percent=neutral_percent)

        enriched = dict(base_result)
        enriched.update(
            {
                "positive_percent": positive_percent,
                "negative_percent": negative_percent,
                "neutral_percent": neutral_percent,
                "intensity": intensity,
                "valence": valence,
                "deep_label": deep_label,
            }
        )
        return enriched

    def _derive_deep_label(self, *, label: str, valence: float, intensity: float, neutral_percent: float) -> str:
        """Convert simple sentiment into a deeper qualitative band."""
        if neutral_percent >= 55 and intensity <= 0.55:
            return "measured_neutral"
        if label == "POSITIVE":
            return "strongly_positive" if intensity >= 0.8 or valence >= 0.45 else "moderately_positive"
        if label == "NEGATIVE":
            return "strongly_negative" if intensity >= 0.8 or valence <= -0.45 else "moderately_negative"
        return "mixed_or_cautious"


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
            "analyzed_at": str(Path(__file__).parent),
            "total_articles": len(articles),
            "articles": articles
        }, handle, indent=2, ensure_ascii=False)

    print(f"Saved analyzed articles to: {output_path}")


def main():
    """Example usage of SentimentAnalyzer."""
    print("=" * 60)
    print("SENTIMENT ANALYSIS - STAGE 3")
    print("=" * 60)
    print()

    analyzer = SentimentAnalyzer()
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
    print("SENTIMENT STATISTICS")
    print("=" * 60)

    stats = analyzer.get_sentiment_statistics(analyzed_articles)
    print(f"\nTotal articles analyzed: {stats['total_analyzed']}")
    print(f"Positive: {stats['positive']} ({stats['positive_percent']}%)")
    print(f"Negative: {stats['negative']} ({stats['negative_percent']}%)")
    print(f"Neutral:  {stats['neutral']} ({stats['neutral_percent']}%)")
    print(f"Average confidence: {stats['average_confidence']}")

    print("\n" + "=" * 60)
    print("SAMPLE ANALYSIS")
    print("=" * 60)

    for i, article in enumerate(analyzed_articles[:3], 1):
        print(f"\n[{i}] {article.get('title', 'No title')[:60]}...")
        print(f"    Source: {article.get('source', 'Unknown')}")

        sentiment = article.get("sentiment_analysis", {})
        if "overall" in sentiment:
            overall = sentiment["overall"]
            print(f"    Overall Sentiment: {overall['label']} (confidence: {overall['score']})")

        if "title" in sentiment:
            title_sent = sentiment["title"]
            print(f"    Title: {title_sent['label']} ({title_sent['score']})")

        if "description" in sentiment:
            desc_sent = sentiment["description"]
            print(f"    Description: {desc_sent['label']} ({desc_sent['score']})")

    output_file = "data/processed/sentiment_analysis/analyzed_articles.json"
    save_analyzed_articles(analyzed_articles, output_file)

    print("\n" + "=" * 60)
    print("SENTIMENT ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nResults saved to: {output_file}")
    print("\nNext: Run emotion analysis")
    print("  python src/analysis/emotion.py")


if __name__ == "__main__":
    main()
