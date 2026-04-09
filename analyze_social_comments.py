"""
Analyze sentiment and emotions in social media comments.
This provides crowd psychology insights into geopolitical narratives.
"""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.console import configure_console_output
from analysis.sentiment import SentimentAnalyzer
from analysis.emotion import EmotionAnalyzer
from tqdm import tqdm

configure_console_output()


def load_comments(filepath: str):
    """Load comments from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and "comments" in data:
        return data["comments"]
    elif isinstance(data, list):
        return data
    else:
        return []


def analyze_social_comments():
    """Complete analysis of social media comments."""
    
    print("=" * 60)
    print("SOCIAL MEDIA REACTION ANALYSIS")
    print("=" * 60)
    
    # Load comments
    input_file = "data/raw/social/mock_social_comments.json"
    
    if not Path(input_file).exists():
        print(f"\n❌ Error: {input_file} not found")
        print("\nGenerate mock data first:")
        print("  python create_mock_data.py")
        return
    
    print(f"\n📂 Loading comments from: {input_file}")
    comments = load_comments(input_file)
    print(f"✓ Loaded {len(comments)} comments")
    
    # Initialize analyzers
    print("\n🔄 Loading NLP models...")
    sentiment_analyzer = SentimentAnalyzer()
    emotion_analyzer = EmotionAnalyzer()
    
    # Extract text from comments
    texts = [comment['text'] for comment in comments]
    
    # Analyze sentiment
    print("\n" + "=" * 60)
    print("SENTIMENT ANALYSIS")
    print("=" * 60)
    
    print("\n🔍 Analyzing sentiment...")
    sentiments = sentiment_analyzer.analyze_batch(texts, batch_size=16)
    
    # Add sentiment to comments
    for comment, sentiment in zip(comments, sentiments):
        comment['sentiment'] = sentiment
    
    # Analyze emotions
    print("\n" + "=" * 60)
    print("EMOTION ANALYSIS")
    print("=" * 60)
    
    print("\n🔍 Analyzing emotions...")
    analyzed_comments = []
    
    for comment in tqdm(comments, desc="Processing emotions"):
        emotion_scores = emotion_analyzer.analyze_text(comment['text'])
        
        # Find dominant emotion
        dominant = max(emotion_scores.items(), key=lambda x: x[1])
        
        comment['emotions'] = emotion_scores
        comment['dominant_emotion'] = {
            "emotion": dominant[0],
            "score": dominant[1]
        }
        
        analyzed_comments.append(comment)
    
    # Calculate statistics
    print("\n" + "=" * 60)
    print("OVERALL STATISTICS")
    print("=" * 60)
    
    # Sentiment breakdown
    sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    for comment in analyzed_comments:
        label = comment['sentiment']['label']
        sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
    
    total = len(analyzed_comments)
    print("\n📊 Sentiment Distribution:")
    for label, count in sorted(sentiment_counts.items()):
        percentage = (count / total) * 100
        print(f"  {label:10s}: {count:3d} ({percentage:5.1f}%)")
    
    # Emotion breakdown
    emotion_counts = {}
    for comment in analyzed_comments:
        emotion = comment['dominant_emotion']['emotion']
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    print("\n😊 Emotion Distribution:")
    for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {emotion:10s}: {count:3d} ({percentage:5.1f}%) {bar}")
    
    # Topic-level analysis
    print("\n" + "=" * 60)
    print("TOPIC-LEVEL ANALYSIS")
    print("=" * 60)
    
    topic_stats = {}
    
    for comment in analyzed_comments:
        topic = comment.get('topic', 'unknown')
        
        if topic not in topic_stats:
            topic_stats[topic] = {
                'total': 0,
                'sentiments': {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0},
                'emotions': {}
            }
        
        topic_stats[topic]['total'] += 1
        
        # Count sentiment
        sentiment = comment['sentiment']['label']
        topic_stats[topic]['sentiments'][sentiment] += 1
        
        # Count emotion
        emotion = comment['dominant_emotion']['emotion']
        topic_stats[topic]['emotions'][emotion] = topic_stats[topic]['emotions'].get(emotion, 0) + 1
    
    for topic, stats in sorted(topic_stats.items()):
        print(f"\n📌 Topic: {topic.upper()}")
        print(f"   Total comments: {stats['total']}")
        
        # Most common sentiment
        dominant_sent = max(stats['sentiments'].items(), key=lambda x: x[1])
        print(f"   Dominant sentiment: {dominant_sent[0]} ({dominant_sent[1]} comments)")
        
        # Most common emotion
        if stats['emotions']:
            dominant_emo = max(stats['emotions'].items(), key=lambda x: x[1])
            print(f"   Dominant emotion: {dominant_emo[0]} ({dominant_emo[1]} comments)")
    
    # High-engagement analysis
    print("\n" + "=" * 60)
    print("HIGH-ENGAGEMENT COMMENTS")
    print("=" * 60)
    
    # Sort by total engagement (likes + retweets + replies)
    for comment in analyzed_comments:
        eng = comment.get('engagement', {})
        comment['total_engagement'] = eng.get('likes', 0) + eng.get('retweets', 0) + eng.get('replies', 0)
    
    top_comments = sorted(
        analyzed_comments,
        key=lambda x: x['total_engagement'],
        reverse=True
    )[:5]
    
    for i, comment in enumerate(top_comments, 1):
        print(f"\n[{i}] {comment['text'][:80]}...")
        print(f"    Engagement: {comment['total_engagement']} interactions")
        print(f"    Sentiment: {comment['sentiment']['label']} ({comment['sentiment']['score']})")
        print(f"    Emotion: {comment['dominant_emotion']['emotion']} ({comment['dominant_emotion']['score']:.3f})")
        print(f"    Platform: {comment['platform']}")
    
    # Save results
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)
    
    output_dir = Path("data/processed/social_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save detailed results
    output_file = output_dir / "analyzed_comments.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_comments": len(analyzed_comments),
            "sentiment_distribution": sentiment_counts,
            "emotion_distribution": emotion_counts,
            "topic_analysis": topic_stats,
            "comments": analyzed_comments
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Detailed analysis saved to: {output_file}")
    
    # Save summary report
    summary_file = output_dir / "social_media_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("SOCIAL MEDIA REACTION ANALYSIS - SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Total Comments Analyzed: {total}\n\n")
        
        f.write("SENTIMENT BREAKDOWN:\n")
        for label, count in sorted(sentiment_counts.items()):
            percentage = (count / total) * 100
            f.write(f"  {label:10s}: {count} ({percentage:.1f}%)\n")
        
        f.write("\nEMOTION BREAKDOWN:\n")
        for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            f.write(f"  {emotion:10s}: {count} ({percentage:.1f}%)\n")
        
        f.write("\nKEY INSIGHTS:\n")
        
        # Sentiment insight
        if sentiment_counts['NEGATIVE'] > sentiment_counts['POSITIVE']:
            f.write(f"  • Public sentiment is predominantly NEGATIVE ({sentiment_counts['NEGATIVE']/total*100:.1f}%)\n")
        elif sentiment_counts['POSITIVE'] > sentiment_counts['NEGATIVE']:
            f.write(f"  • Public sentiment is predominantly POSITIVE ({sentiment_counts['POSITIVE']/total*100:.1f}%)\n")
        else:
            f.write(f"  • Public sentiment is relatively BALANCED\n")
        
        # Emotion insight
        top_emotion = max(emotion_counts.items(), key=lambda x: x[1])
        f.write(f"  • Dominant emotion: {top_emotion[0].upper()} ({top_emotion[1]/total*100:.1f}%)\n")
    
    print(f"✓ Summary report saved to: {summary_file}")
    
    print("\n" + "=" * 60)
    print("✅ SOCIAL MEDIA ANALYSIS COMPLETE")
    print("=" * 60)
    print("\n📊 Key Findings:")
    
    # Summary insights
    neg_pct = (sentiment_counts['NEGATIVE'] / total) * 100
    if neg_pct > 60:
        print(f"  ⚠️  High negativity detected ({neg_pct:.1f}%)")
    
    top_emotion_name = max(emotion_counts.items(), key=lambda x: x[1])[0]
    if top_emotion_name in ['fear', 'anger']:
        print(f"  😠 Strong emotional reactions: {top_emotion_name}")
    
    print("\n🚀 Next: Compare news sentiment vs. public reaction")


def main():
    """Run social media comment analysis."""
    analyze_social_comments()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
