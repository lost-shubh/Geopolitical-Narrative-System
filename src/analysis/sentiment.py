"""
Sentiment Analysis Module - Stage 3
Analyzes sentiment (positive/negative/neutral) in news articles and comments.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Union
from transformers import pipeline
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')


class SentimentAnalyzer:
    """Analyze sentiment in text using transformer models."""
    
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initialize sentiment analyzer.
        
        Args:
            model_name: Hugging Face model to use for sentiment analysis
        """
        print(f"Loading sentiment model: {model_name}")
        print("(This may take a minute on first run - downloading model...)")
        
        self.model = pipeline(
            "sentiment-analysis",
            model=model_name,
            device=-1  # Use CPU (set to 0 for GPU)
        )
        
        print("✓ Sentiment model loaded successfully")
    
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
        
        # Truncate to model's max length (512 tokens)
        text = text[:512]
        
        try:
            result = self.model(text)[0]
            return {
                "label": result["label"],
                "score": round(result["score"], 4)
            }
        except Exception as e:
            print(f"Error analyzing text: {e}")
            return {"label": "ERROR", "score": 0.0}
    
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
        
        # Process in batches to avoid memory issues
        for i in tqdm(range(0, len(texts), batch_size), desc="Processing batches"):
            batch = texts[i:i + batch_size]
            
            # Clean and truncate texts
            cleaned_batch = [
                text[:512] if text and text.strip() else "" 
                for text in batch
            ]
            
            try:
                batch_results = self.model(cleaned_batch)
                results.extend([
                    {
                        "label": r["label"],
                        "score": round(r["score"], 4)
                    }
                    for r in batch_results
                ])
            except Exception as e:
                print(f"Error in batch {i}: {e}")
                # Add error placeholders
                results.extend([
                    {"label": "ERROR", "score": 0.0}
                    for _ in batch
                ])
        
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
            
            # Analyze each field
            for field in fields:
                text = article.get(field, "")
                if text and text.strip():
                    sentiment = self.analyze_text(text)
                    article_copy["sentiment_analysis"][field] = sentiment
            
            # Calculate overall sentiment (average of all fields)
            sentiments = list(article_copy["sentiment_analysis"].values())
            if sentiments:
                # Count labels
                labels = [s["label"] for s in sentiments]
                most_common = max(set(labels), key=labels.count)
                
                # Average score
                avg_score = sum(s["score"] for s in sentiments) / len(sentiments)
                
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
        
        # Count by label
        positive = sum(1 for s in sentiments if s["label"] == "POSITIVE")
        negative = sum(1 for s in sentiments if s["label"] == "NEGATIVE")
        neutral = len(sentiments) - positive - negative
        
        # Average confidence scores
        avg_score = sum(s["score"] for s in sentiments) / len(sentiments)
        
        return {
            "total_analyzed": len(sentiments),
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "positive_percent": round(positive / len(sentiments) * 100, 2),
            "negative_percent": round(negative / len(sentiments) * 100, 2),
            "neutral_percent": round(neutral / len(sentiments) * 100, 2),
            "average_confidence": round(avg_score, 4)
        }


def load_articles_from_json(filepath: str) -> List[Dict]:
    """Load articles from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both formats: {"articles": [...]} and direct list
    if isinstance(data, dict) and "articles" in data:
        return data["articles"]
    elif isinstance(data, list):
        return data
    else:
        return []


def save_analyzed_articles(articles: List[Dict], output_path: str):
    """Save analyzed articles to JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analyzed_at": str(Path(__file__).parent),
            "total_articles": len(articles),
            "articles": articles
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved analyzed articles to: {output_path}")


def main():
    """Example usage of SentimentAnalyzer."""
    
    print("="*60)
    print("SENTIMENT ANALYSIS - STAGE 3")
    print("="*60)
    print()
    
    # Initialize analyzer
    analyzer = SentimentAnalyzer()
    
    # Load articles from Stage 1 output
    input_file = "data/raw/news/test_articles.json"
    
    if not Path(input_file).exists():
        print(f"❌ Error: {input_file} not found")
        print("\nPlease run Stage 1 first:")
        print("  python test_news_ingestion.py")
        return
    
    print(f"\n📂 Loading articles from: {input_file}")
    articles = load_articles_from_json(input_file)
    print(f"✓ Loaded {len(articles)} articles")
    
    # Analyze sentiment
    analyzed_articles = analyzer.analyze_articles(
        articles,
        fields=["title", "description"]
    )
    
    # Get statistics
    print("\n" + "="*60)
    print("SENTIMENT STATISTICS")
    print("="*60)
    
    stats = analyzer.get_sentiment_statistics(analyzed_articles)
    print(f"\nTotal articles analyzed: {stats['total_analyzed']}")
    print(f"Positive: {stats['positive']} ({stats['positive_percent']}%)")
    print(f"Negative: {stats['negative']} ({stats['negative_percent']}%)")
    print(f"Neutral:  {stats['neutral']} ({stats['neutral_percent']}%)")
    print(f"Average confidence: {stats['average_confidence']}")
    
    # Show sample results
    print("\n" + "="*60)
    print("SAMPLE ANALYSIS")
    print("="*60)
    
    for i, article in enumerate(analyzed_articles[:3], 1):
        print(f"\n[{i}] {article.get('title', 'No title')[:60]}...")
        print(f"    Source: {article.get('source', 'Unknown')}")
        
        sentiment = article.get('sentiment_analysis', {})
        if 'overall' in sentiment:
            overall = sentiment['overall']
            print(f"    Overall Sentiment: {overall['label']} (confidence: {overall['score']})")
        
        if 'title' in sentiment:
            title_sent = sentiment['title']
            print(f"    Title: {title_sent['label']} ({title_sent['score']})")
        
        if 'description' in sentiment:
            desc_sent = sentiment['description']
            print(f"    Description: {desc_sent['label']} ({desc_sent['score']})")
    
    # Save results
    output_file = "data/processed/sentiment_analysis/analyzed_articles.json"
    save_analyzed_articles(analyzed_articles, output_file)
    
    print("\n" + "="*60)
    print("✅ SENTIMENT ANALYSIS COMPLETE")
    print("="*60)
    print(f"\n📊 Results saved to: {output_file}")
    print("\nNext: Run emotion analysis")
    print("  python src/analysis/emotion.py")


if __name__ == "__main__":
    main()