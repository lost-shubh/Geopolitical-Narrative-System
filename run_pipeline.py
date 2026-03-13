"""
Complete Geopolitical Narrative Analysis Pipeline
Runs all stages: News → Social → Analysis → Report
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def stage1_fetch_news():
    """Stage 1: Fetch geopolitical news articles."""
    print_section("STAGE 1: NEWS INGESTION")
    
    from ingestion.news_ingestor import NewsIngestor
    
    # Load API key
    api_key = os.getenv("NEWS_API_KEY")
    
    if not api_key:
        print("⚠️  NEWS_API_KEY not found. Skipping news fetch.")
        print("   Using existing data if available...")
        
        # Check if we have existing data
        test_file = Path("data/raw/news/test_articles.json")
        if test_file.exists():
            print(f"✓ Found existing news data: {test_file}")
            return str(test_file)
        else:
            print("❌ No existing news data found.")
            print("   Please set NEWS_API_KEY in .env file or run:")
            print("   python test_news_ingestion.py")
            return None
    
    # Fetch news
    print("\n🔄 Initializing news ingestor...")
    ingestor = NewsIngestor(api_key=api_key)
    
    print("📰 Fetching geopolitical news (last 3 days)...")
    articles = ingestor.fetch_news(
        query="geopolitics OR international conflict OR diplomacy",
        days_back=3,
        max_articles=20
    )
    
    if not articles:
        print("⚠️  No articles fetched. Using existing data...")
        test_file = Path("data/raw/news/test_articles.json")
        if test_file.exists():
            return str(test_file)
        return None
    
    # Save articles
    filepath = ingestor.save_articles(articles, "pipeline_news.json")
    
    # Show stats
    stats = ingestor.get_statistics(articles)
    print(f"\n✓ Fetched {stats['total']} articles")
    print(f"✓ From {stats['sources']} unique sources")
    
    return filepath


def stage2_generate_social():
    """Stage 2: Generate/fetch social media reactions."""
    print_section("STAGE 2: SOCIAL MEDIA DATA")
    
    # Check if mock data already exists
    mock_file = Path("data/raw/social/mock_social_comments.json")
    
    if mock_file.exists():
        print("✓ Using existing mock social media data")
        
        with open(mock_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            count = data.get('total_comments', len(data.get('comments', [])))
            print(f"✓ Loaded {count} comments")
        
        return str(mock_file)
    
    # Generate new mock data
    print("🔄 Generating mock social media comments...")
    
    import create_mock_data
    filepath = create_mock_data.create_mock_social_dataset()
    
    return str(filepath)


def stage3_analyze_news(news_file):
    """Stage 3a: Analyze news articles."""
    print_section("STAGE 3A: NEWS SENTIMENT & EMOTION ANALYSIS")
    
    from analysis.sentiment import SentimentAnalyzer, load_articles_from_json
    from analysis.emotion import EmotionAnalyzer
    
    # Load articles
    print(f"📂 Loading articles from: {news_file}")
    articles = load_articles_from_json(news_file)
    print(f"✓ Loaded {len(articles)} articles")
    
    # Sentiment analysis
    print("\n🔄 Running sentiment analysis...")
    sentiment_analyzer = SentimentAnalyzer()
    sentiment_results = sentiment_analyzer.analyze_articles(articles, fields=["title", "description"])
    
    sentiment_stats = sentiment_analyzer.get_sentiment_statistics(sentiment_results)
    print(f"✓ Sentiment: {sentiment_stats['positive']} positive, {sentiment_stats['negative']} negative, {sentiment_stats['neutral']} neutral")
    
    # Emotion analysis
    print("\n🔄 Running emotion analysis...")
    emotion_analyzer = EmotionAnalyzer()
    emotion_results = emotion_analyzer.analyze_articles(articles, fields=["title", "description"])
    
    emotion_stats = emotion_analyzer.get_emotion_statistics(emotion_results)
    print(f"✓ Dominant emotion: {emotion_stats['most_common_emotion']}")
    
    # Merge results
    combined = []
    for sent, emo in zip(sentiment_results, emotion_results):
        article = sent.copy()
        article['emotion_analysis'] = emo.get('emotion_analysis', {})
        combined.append(article)
    
    # Save results
    output_dir = Path("data/processed/pipeline_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "news_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "sentiment_stats": sentiment_stats,
            "emotion_stats": emotion_stats,
            "articles": combined
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to: {output_file}")
    
    return {
        "articles": combined,
        "sentiment_stats": sentiment_stats,
        "emotion_stats": emotion_stats
    }


def stage3_analyze_social(social_file):
    """Stage 3b: Analyze social media comments."""
    print_section("STAGE 3B: SOCIAL MEDIA SENTIMENT & EMOTION ANALYSIS")
    
    from analysis.sentiment import SentimentAnalyzer
    from analysis.emotion import EmotionAnalyzer
    
    # Load comments
    print(f"📂 Loading comments from: {social_file}")
    with open(social_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        comments = data.get('comments', data)
    
    print(f"✓ Loaded {len(comments)} comments")
    
    # Initialize analyzers
    sentiment_analyzer = SentimentAnalyzer()
    emotion_analyzer = EmotionAnalyzer()
    
    # Analyze
    print("\n🔄 Analyzing sentiment...")
    texts = [c['text'] for c in comments]
    sentiments = sentiment_analyzer.analyze_batch(texts, batch_size=16)
    
    print("🔄 Analyzing emotions...")
    analyzed_comments = []
    for comment, sentiment in zip(comments, sentiments):
        emotions = emotion_analyzer.analyze_text(comment['text'])
        dominant = max(emotions.items(), key=lambda x: x[1])
        
        comment['sentiment'] = sentiment
        comment['emotions'] = emotions
        comment['dominant_emotion'] = {"emotion": dominant[0], "score": dominant[1]}
        
        analyzed_comments.append(comment)
    
    # Calculate stats
    sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    emotion_counts = {}
    
    for comment in analyzed_comments:
        sentiment_counts[comment['sentiment']['label']] += 1
        emotion = comment['dominant_emotion']['emotion']
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    total = len(analyzed_comments)
    print(f"\n✓ Sentiment: {sentiment_counts['POSITIVE']} positive ({sentiment_counts['POSITIVE']/total*100:.1f}%), {sentiment_counts['NEGATIVE']} negative ({sentiment_counts['NEGATIVE']/total*100:.1f}%)")
    
    top_emotion = max(emotion_counts.items(), key=lambda x: x[1])
    print(f"✓ Dominant emotion: {top_emotion[0]} ({top_emotion[1]/total*100:.1f}%)")
    
    # Save results
    output_dir = Path("data/processed/pipeline_results")
    output_file = output_dir / "social_analysis.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "sentiment_counts": sentiment_counts,
            "emotion_counts": emotion_counts,
            "comments": analyzed_comments
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to: {output_file}")
    
    return {
        "comments": analyzed_comments,
        "sentiment_counts": sentiment_counts,
        "emotion_counts": emotion_counts
    }


def generate_final_report(news_results, social_results):
    """Generate comprehensive final report."""
    print_section("GENERATING FINAL REPORT")
    
    output_dir = Path("data/processed/pipeline_results")
    report_file = output_dir / "FINAL_REPORT.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 70 + "\n")
        f.write("  GEOPOLITICAL NARRATIVE INTELLIGENCE SYSTEM\n")
        f.write("  COMPREHENSIVE ANALYSIS REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # News Analysis
        f.write("\n" + "=" * 70 + "\n")
        f.write("SECTION 1: NEWS MEDIA ANALYSIS\n")
        f.write("=" * 70 + "\n\n")
        
        news_sent = news_results['sentiment_stats']
        f.write(f"Total Articles Analyzed: {news_sent['total_analyzed']}\n\n")
        
        f.write("Sentiment Distribution:\n")
        f.write(f"  Positive: {news_sent['positive']} ({news_sent['positive_percent']}%)\n")
        f.write(f"  Negative: {news_sent['negative']} ({news_sent['negative_percent']}%)\n")
        f.write(f"  Neutral:  {news_sent['neutral']} ({news_sent['neutral_percent']}%)\n\n")
        
        news_emo = news_results['emotion_stats']
        f.write(f"Dominant Emotion in Coverage: {news_emo['most_common_emotion'].upper()}\n\n")
        
        f.write("Emotion Distribution:\n")
        for emotion, pct in sorted(news_emo['emotion_distribution'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {emotion.capitalize():12s}: {pct:5.1f}%\n")
        
        # Social Media Analysis
        f.write("\n" + "=" * 70 + "\n")
        f.write("SECTION 2: PUBLIC REACTION ANALYSIS\n")
        f.write("=" * 70 + "\n\n")
        
        social_sent = social_results['sentiment_counts']
        total_comments = len(social_results['comments'])
        
        f.write(f"Total Comments Analyzed: {total_comments}\n\n")
        
        f.write("Public Sentiment:\n")
        for label, count in sorted(social_sent.items()):
            pct = (count / total_comments) * 100
            f.write(f"  {label:10s}: {count} ({pct:5.1f}%)\n")
        
        f.write("\nPublic Emotions:\n")
        social_emo = social_results['emotion_counts']
        for emotion, count in sorted(social_emo.items(), key=lambda x: x[1], reverse=True)[:5]:
            pct = (count / total_comments) * 100
            f.write(f"  {emotion.capitalize():12s}: {count} ({pct:5.1f}%)\n")
        
        # Comparison
        f.write("\n" + "=" * 70 + "\n")
        f.write("SECTION 3: MEDIA vs. PUBLIC COMPARISON\n")
        f.write("=" * 70 + "\n\n")
        
        # Sentiment gap
        news_neg_pct = news_sent['negative_percent']
        public_neg_pct = (social_sent['NEGATIVE'] / total_comments) * 100
        sentiment_gap = public_neg_pct - news_neg_pct
        
        f.write("Sentiment Analysis:\n")
        f.write(f"  News negativity:   {news_neg_pct:.1f}%\n")
        f.write(f"  Public negativity: {public_neg_pct:.1f}%\n")
        f.write(f"  Gap: {abs(sentiment_gap):.1f}% ")
        if sentiment_gap > 0:
            f.write("(public MORE negative)\n")
        else:
            f.write("(public LESS negative)\n")
        
        # Key Insights
        f.write("\n" + "=" * 70 + "\n")
        f.write("SECTION 4: KEY INSIGHTS\n")
        f.write("=" * 70 + "\n\n")
        
        insights = []
        
        # Sentiment insights
        if news_neg_pct > 60:
            insights.append("• News coverage is predominantly NEGATIVE - potential crisis framing")
        
        if public_neg_pct > 60:
            insights.append("• Public sentiment is highly NEGATIVE - strong emotional reactions")
        
        if abs(sentiment_gap) > 20:
            insights.append(f"• Significant sentiment GAP between media and public ({abs(sentiment_gap):.1f}%)")
        
        # Emotion insights
        news_top_emotion = news_emo['most_common_emotion']
        social_top_emotion = max(social_emo.items(), key=lambda x: x[1])[0]
        
        if news_top_emotion in ['fear', 'anger']:
            insights.append(f"• News coverage evokes {news_top_emotion.upper()} - potentially alarming framing")
        
        if social_top_emotion in ['fear', 'anger']:
            insights.append(f"• Public reactions show high {social_top_emotion.upper()} - emotional escalation")
        
        if news_top_emotion != social_top_emotion:
            insights.append(f"• Emotional DISCONNECT: News emphasizes {news_top_emotion}, public feels {social_top_emotion}")
        
        for insight in insights:
            f.write(f"{insight}\n")
        
        # Recommendations
        f.write("\n" + "=" * 70 + "\n")
        f.write("SECTION 5: RECOMMENDATIONS\n")
        f.write("=" * 70 + "\n\n")
        
        if public_neg_pct > 70:
            f.write("1. High public negativity detected - fact-based corrections needed\n")
        
        if sentiment_gap > 20:
            f.write("2. Media-public sentiment gap - investigate narrative amplification\n")
        
        if social_top_emotion == 'fear':
            f.write("3. Fear-driven reactions - provide context and reassurance\n")
        
        if social_top_emotion == 'anger':
            f.write("4. Anger-driven reactions - address underlying concerns directly\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 70 + "\n")
    
    print(f"✓ Final report saved to: {report_file}")
    return str(report_file)


def main():
    """Run the complete pipeline."""
    
    print("=" * 70)
    print("  GEOPOLITICAL NARRATIVE INTELLIGENCE SYSTEM")
    print("  Complete Analysis Pipeline")
    print("=" * 70)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load environment
    load_dotenv()
    
    # Stage 1: News
    news_file = stage1_fetch_news()
    
    if not news_file:
        print("\n❌ Cannot proceed without news data")
        return
    
    # Stage 2: Social
    social_file = stage2_generate_social()
    
    # Stage 3: Analysis
    news_results = stage3_analyze_news(news_file)
    social_results = stage3_analyze_social(social_file)
    
    # Generate Report
    report_file = generate_final_report(news_results, social_results)
    
    # Final Summary
    print_section("✅ PIPELINE COMPLETE")
    
    print("\n📁 Output Files:")
    print(f"  • News analysis:   data/processed/pipeline_results/news_analysis.json")
    print(f"  • Social analysis: data/processed/pipeline_results/social_analysis.json")
    print(f"  • Final report:    {report_file}")
    
    print("\n📊 Quick Summary:")
    print(f"  • Analyzed {news_results['sentiment_stats']['total_analyzed']} news articles")
    print(f"  • Analyzed {len(social_results['comments'])} social media comments")
    
    news_neg = news_results['sentiment_stats']['negative_percent']
    social_neg = (social_results['sentiment_counts']['NEGATIVE'] / len(social_results['comments'])) * 100
    
    print(f"  • News negativity:   {news_neg:.1f}%")
    print(f"  • Public negativity: {social_neg:.1f}%")
    
    print(f"\n📄 Read the full report: {report_file}")
    print("\n🎉 Analysis complete! Check the output files above.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()