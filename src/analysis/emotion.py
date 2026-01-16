"""
Emotion Analysis Module - Stage 3
Detects specific emotions (anger, fear, joy, sadness, etc.) in text.
"""

import json
from pathlib import Path
from typing import List, Dict
from transformers import pipeline
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')


class EmotionAnalyzer:
    """Analyze emotions in text using transformer models."""
    
    # Emotion categories from the model
    EMOTIONS = [
        "anger", "disgust", "fear", "joy", 
        "neutral", "sadness", "surprise"
    ]
    
    def __init__(self, model_name: str = "j-hartmann/emotion-english-distilroberta-base"):
        """
        Initialize emotion analyzer.
        
        Args:
            model_name: Hugging Face model for emotion detection
        """
        print(f"Loading emotion model: {model_name}")
        print("(This may take 1-2 minutes on first run...)")
        
        self.model = pipeline(
            "text-classification",
            model=model_name,
            top_k=None,  # Return all emotion scores
            device=-1  # Use CPU
        )
        
        print("✓ Emotion model loaded successfully")
    
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
        
        # Truncate to model's max length
        text = text[:512]
        
        try:
            results = self.model(text)[0]
            
            # Convert to dictionary
            emotion_scores = {
                result["label"]: round(result["score"], 4)
                for result in results
            }
            
            return emotion_scores
            
        except Exception as e:
            print(f"Error analyzing emotions: {e}")
            return {emotion: 0.0 for emotion in self.EMOTIONS}
    
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
            
            # Analyze each field
            for field in fields:
                text = article.get(field, "")
                if text and text.strip():
                    emotions = self.analyze_text(text)
                    article_copy["emotion_analysis"][field] = emotions
            
            # Calculate overall emotions (average across fields)
            if article_copy["emotion_analysis"]:
                overall_emotions = {}
                
                for emotion in self.EMOTIONS:
                    scores = []
                    for field_emotions in article_copy["emotion_analysis"].values():
                        if emotion in field_emotions:
                            scores.append(field_emotions[emotion])
                    
                    if scores:
                        overall_emotions[emotion] = round(
                            sum(scores) / len(scores), 4
                        )
                
                # Find dominant emotion
                if overall_emotions:
                    dominant = max(overall_emotions.items(), key=lambda x: x[1])
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
        
        # Collect all overall emotions
        emotion_totals = {emotion: [] for emotion in self.EMOTIONS}
        dominant_emotions = []
        
        for article in analyzed_articles:
            overall = article.get("emotion_analysis", {}).get("overall", {})
            
            if overall:
                # Collect scores
                for emotion in self.EMOTIONS:
                    if emotion in overall:
                        emotion_totals[emotion].append(overall[emotion])
                
                # Collect dominant emotions
                if "dominant_emotion" in overall:
                    dominant_emotions.append(overall["dominant_emotion"])
        
        # Calculate averages
        emotion_averages = {
            emotion: round(sum(scores) / len(scores), 4) if scores else 0.0
            for emotion, scores in emotion_totals.items()
        }
        
        # Count dominant emotions
        dominant_counts = {
            emotion: dominant_emotions.count(emotion)
            for emotion in set(dominant_emotions)
        }
        
        # Sort by frequency
        dominant_sorted = sorted(
            dominant_counts.items(),
            key=lambda x: x[1],
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


def load_articles_from_json(filepath: str) -> List[Dict]:
    """Load articles from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
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
            "total_articles": len(articles),
            "articles": articles
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved emotion analysis to: {output_path}")


def main():
    """Example usage of EmotionAnalyzer."""
    
    print("="*60)
    print("EMOTION ANALYSIS - STAGE 3")
    print("="*60)
    print()
    
    # Initialize analyzer
    analyzer = EmotionAnalyzer()
    
    # Load articles
    input_file = "data/raw/news/test_articles.json"
    
    if not Path(input_file).exists():
        print(f"❌ Error: {input_file} not found")
        print("\nPlease run Stage 1 first:")
        print("  python test_news_ingestion.py")
        return
    
    print(f"\n📂 Loading articles from: {input_file}")
    articles = load_articles_from_json(input_file)
    print(f"✓ Loaded {len(articles)} articles")
    
    # Analyze emotions
    analyzed_articles = analyzer.analyze_articles(
        articles,
        fields=["title", "description"]
    )
    
    # Get statistics
    print("\n" + "="*60)
    print("EMOTION STATISTICS")
    print("="*60)
    
    stats = analyzer.get_emotion_statistics(analyzed_articles)
    
    print(f"\nTotal articles analyzed: {stats['total_analyzed']}")
    print(f"Most common emotion: {stats['most_common_emotion']}")
    
    print("\nEmotion Distribution:")
    for emotion, percentage in sorted(
        stats['emotion_distribution'].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"  {emotion:10s}: {percentage:5.1f}%")
    
    print("\nAverage Emotion Scores:")
    for emotion, score in sorted(
        stats['average_emotions'].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"  {emotion:10s}: {score:.4f}")
    
    # Show sample results
    print("\n" + "="*60)
    print("SAMPLE ANALYSIS")
    print("="*60)
    
    for i, article in enumerate(analyzed_articles[:3], 1):
        print(f"\n[{i}] {article.get('title', 'No title')[:60]}...")
        
        overall = article.get('emotion_analysis', {}).get('overall', {})
        if overall:
            dominant = overall.get('dominant_emotion', 'Unknown')
            score = overall.get('dominant_score', 0.0)
            print(f"    Dominant Emotion: {dominant.upper()} (confidence: {score})")
            
            # Show top 3 emotions
            emotion_scores = {k: v for k, v in overall.items() 
                            if k not in ['dominant_emotion', 'dominant_score']}
            top_3 = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"    Top emotions:")
            for emotion, score in top_3:
                print(f"      • {emotion}: {score}")
    
    # Save results
    output_file = "data/processed/emotion_analysis/analyzed_articles.json"
    save_analyzed_articles(analyzed_articles, output_file)
    
    print("\n" + "="*60)
    print("✅ EMOTION ANALYSIS COMPLETE")
    print("="*60)
    print(f"\n📊 Results saved to: {output_file}")


if __name__ == "__main__":
    main()