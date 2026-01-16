"""
Test script for Stage 3 - Sentiment and Emotion Analysis
Runs both analyzers on your fetched news articles.
"""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analysis.sentiment import SentimentAnalyzer, load_articles_from_json
from src.analysis.emotion import EmotionAnalyzer


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(text)
    print("="*60)


def main():
    """Run complete sentiment and emotion analysis."""
    
    print_header("STAGE 3: SENTIMENT & EMOTION ANALYSIS TEST")
    
    # Check if news articles exist
    input_file = "data/raw/news/test_articles.json"
    
    if not Path(input_file).exists():
        print(f"\n❌ Error: {input_file} not found")
        print("\nYou need to run Stage 1 first to fetch news articles:")
        print("  python test_news_ingestion.py")
        return
    
    print(f"\n📂 Loading articles from: {input_file}")
    articles = load_articles_from_json(input_file)
    print(f"✓ Loaded {len(articles)} articles")
    
    # ========================================
    # PART 1: SENTIMENT ANALYSIS
    # ========================================
    print_header("PART 1: SENTIMENT ANALYSIS")
    
    print("\n🔄 Initializing sentiment analyzer...")
    sentiment_analyzer = SentimentAnalyzer()
    
    print("\n🔍 Analyzing sentiment in articles...")
    sentiment_results = sentiment_analyzer.analyze_articles(
        articles,
        fields=["title", "description"]
    )
    
    # Get sentiment statistics
    sentiment_stats = sentiment_analyzer.get_sentiment_statistics(sentiment_results)
    
    print("\n📊 SENTIMENT RESULTS:")
    print(f"  Total analyzed:     {sentiment_stats['total_analyzed']}")
    print(f"  Positive:           {sentiment_stats['positive']} ({sentiment_stats['positive_percent']}%)")
    print(f"  Negative:           {sentiment_stats['negative']} ({sentiment_stats['negative_percent']}%)")
    print(f"  Neutral:            {sentiment_stats['neutral']} ({sentiment_stats['neutral_percent']}%)")
    print(f"  Avg confidence:     {sentiment_stats['average_confidence']}")
    
    # ========================================
    # PART 2: EMOTION ANALYSIS
    # ========================================
    print_header("PART 2: EMOTION ANALYSIS")
    
    print("\n🔄 Initializing emotion analyzer...")
    emotion_analyzer = EmotionAnalyzer()
    
    print("\n🔍 Analyzing emotions in articles...")
    emotion_results = emotion_analyzer.analyze_articles(
        articles,
        fields=["title", "description"]
    )
    
    # Get emotion statistics
    emotion_stats = emotion_analyzer.get_emotion_statistics(emotion_results)
    
    print("\n📊 EMOTION RESULTS:")
    print(f"  Total analyzed:     {emotion_stats['total_analyzed']}")
    print(f"  Most common:        {emotion_stats['most_common_emotion'].upper()}")
    
    print("\n  Emotion Distribution:")
    for emotion, percentage in sorted(
        emotion_stats['emotion_distribution'].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        bar_length = int(percentage / 2)  # Scale to fit terminal
        bar = "█" * bar_length
        print(f"    {emotion:10s} {percentage:5.1f}% {bar}")
    
    # ========================================
    # COMBINED SAMPLE RESULTS
    # ========================================
    print_header("SAMPLE ARTICLE ANALYSIS")
    
    # Merge both analyses
    combined_results = []
    for sent_article, emo_article in zip(sentiment_results, emotion_results):
        combined = sent_article.copy()
        combined["emotion_analysis"] = emo_article.get("emotion_analysis", {})
        combined_results.append(combined)
    
    # Show top 3 articles
    for i, article in enumerate(combined_results[:3], 1):
        print(f"\n[{i}] {article.get('title', 'No title')[:70]}...")
        print(f"    Source: {article.get('source', 'Unknown')}")
        print(f"    Published: {article.get('published_at', 'Unknown')}")
        
        # Sentiment
        sentiment = article.get('sentiment_analysis', {}).get('overall', {})
        if sentiment:
            print(f"    📊 Sentiment: {sentiment['label']} (confidence: {sentiment['score']})")
        
        # Emotion
        emotion = article.get('emotion_analysis', {}).get('overall', {})
        if emotion and 'dominant_emotion' in emotion:
            dom_emotion = emotion['dominant_emotion']
            dom_score = emotion['dominant_score']
            print(f"    😊 Dominant Emotion: {dom_emotion.upper()} (confidence: {dom_score})")
            
            # Top 3 emotions
            emotion_scores = {k: v for k, v in emotion.items() 
                            if k not in ['dominant_emotion', 'dominant_score']}
            top_3 = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"    🎭 Top emotions: {', '.join(f'{e}({s:.2f})' for e, s in top_3)}")
    
    # ========================================
    # SAVE COMBINED RESULTS
    # ========================================
    print_header("SAVING RESULTS")
    
    # Save combined analysis
    output_dir = Path("data/processed/combined_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "sentiment_emotion_analysis.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_articles": len(combined_results),
            "sentiment_statistics": sentiment_stats,
            "emotion_statistics": emotion_stats,
            "articles": combined_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Combined analysis saved to: {output_file}")
    
    # Also save summary report
    summary_file = output_dir / "analysis_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("GEOPOLITICAL NARRATIVE ANALYSIS - SUMMARY REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("SENTIMENT ANALYSIS:\n")
        f.write(f"  Total articles:  {sentiment_stats['total_analyzed']}\n")
        f.write(f"  Positive:        {sentiment_stats['positive']} ({sentiment_stats['positive_percent']}%)\n")
        f.write(f"  Negative:        {sentiment_stats['negative']} ({sentiment_stats['negative_percent']}%)\n")
        f.write(f"  Neutral:         {sentiment_stats['neutral']} ({sentiment_stats['neutral_percent']}%)\n\n")
        
        f.write("EMOTION ANALYSIS:\n")
        f.write(f"  Most common emotion: {emotion_stats['most_common_emotion']}\n")
        f.write(f"  Distribution:\n")
        for emotion, percentage in sorted(
            emotion_stats['emotion_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            f.write(f"    {emotion:10s}: {percentage:5.1f}%\n")
    
    print(f"✓ Summary report saved to: {summary_file}")
    
    # ========================================
    # FINAL SUMMARY
    # ========================================
    print_header("✅ ANALYSIS COMPLETE!")
    
    print("\n📁 Files created:")
    print(f"  1. {output_file}")
    print(f"  2. {summary_file}")
    
    print("\n📊 Key Insights:")
    
    # Sentiment insight
    if sentiment_stats['negative_percent'] > 50:
        print(f"  ⚠️  {sentiment_stats['negative_percent']}% of coverage is NEGATIVE")
    elif sentiment_stats['positive_percent'] > 50:
        print(f"  ✅ {sentiment_stats['positive_percent']}% of coverage is POSITIVE")
    else:
        print(f"  ℹ️  Coverage is relatively BALANCED")
    
    # Emotion insight
    dominant_emotion = emotion_stats['most_common_emotion']
    emotion_meanings = {
        "fear": "⚠️ High anxiety about the situation",
        "anger": "😠 Public frustration evident",
        "sadness": "😢 Somber tone in coverage",
        "joy": "😊 Optimistic reporting",
        "surprise": "😲 Unexpected developments",
        "neutral": "📊 Objective reporting tone",
        "disgust": "🤢 Strong negative reactions"
    }
    
    if dominant_emotion in emotion_meanings:
        print(f"  {emotion_meanings[dominant_emotion]}")
    
    print("\n🚀 Next Steps:")
    print("  1. Check the JSON file to see detailed results")
    print("  2. Read the summary report")
    print("  3. Ready for Stage 4? Tell me: 'Build Stage 4 - Claim Extraction'")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()