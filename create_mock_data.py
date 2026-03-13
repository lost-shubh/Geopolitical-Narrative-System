"""
Create mock social media data for testing.
Generates realistic-looking comments and reactions to news articles.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path


# Sample realistic comments about geopolitical topics
COMMENT_TEMPLATES = {
    "ukraine_russia": [
        "This is absolutely devastating. When will this conflict end?",
        "The humanitarian crisis is getting worse every day.",
        "This is clear aggression and the world needs to act.",
        "Both sides need to come to the negotiating table.",
        "The media isn't showing the full picture here.",
        "This will have global economic consequences.",
        "My thoughts are with the innocent civilians caught in this.",
        "This is a violation of international law.",
        "The West is escalating this unnecessarily.",
        "We need diplomatic solutions, not more weapons.",
        "This is propaganda. Don't believe everything you read.",
        "The UN needs to step in immediately.",
        "This reminds me of the Cold War all over again.",
        "Energy prices are going through the roof because of this.",
        "Why isn't anyone talking about peace negotiations?"
    ],
    "china_taiwan": [
        "This is a very dangerous situation for the region.",
        "Taiwan has the right to self-determination.",
        "This could trigger a global conflict.",
        "The semiconductor industry will be severely impacted.",
        "China is just defending its territorial integrity.",
        "The US needs to stop interfering in Asian affairs.",
        "This is about more than just Taiwan - it's about democracy.",
        "Economic ties between these nations are too strong for war.",
        "Military posturing on both sides is alarming.",
        "ASEAN needs to play a mediating role here.",
        "This will reshape global supply chains entirely.",
        "Japan and South Korea are watching this very closely.",
        "We're heading towards a new Cold War.",
        "Diplomatic channels need to stay open at all costs.",
        "The stakes have never been higher."
    ],
    "middle_east": [
        "When will this region know peace?",
        "The humanitarian toll is unacceptable.",
        "This is a complex situation with no easy answers.",
        "International intervention has failed repeatedly.",
        "Oil prices are going to spike again.",
        "Religious and ethnic tensions run deep here.",
        "The UN resolutions are being ignored.",
        "Civilians are always the ones who suffer most.",
        "This needs a regional solution, not outside powers.",
        "The media coverage is incredibly biased.",
        "Water rights are going to be the next big issue.",
        "Iran's influence in the region is growing.",
        "Saudi Arabia's role in this is questionable.",
        "Democracy movements are being suppressed.",
        "This will destabilize the entire region."
    ],
    "nato": [
        "NATO expansion is a legitimate security concern.",
        "These nations have the right to choose their alliances.",
        "This is Cold War thinking in the 21st century.",
        "Collective defense is more important than ever.",
        "This will only increase tensions further.",
        "Europe needs to invest more in its own defense.",
        "The US is overextended militarily.",
        "This is about deterrence, not aggression.",
        "Military spending is out of control globally.",
        "NATO is a defensive alliance, not offensive.",
        "Russia sees this as an existential threat.",
        "Article 5 commitments are being tested.",
        "The alliance needs reform to stay relevant.",
        "Turkey's position in NATO is complicated.",
        "This is reshaping European security architecture."
    ],
    "elections": [
        "Foreign interference in elections is a real threat.",
        "These allegations need to be investigated thoroughly.",
        "This is just conspiracy theory nonsense.",
        "Social media platforms are being weaponized.",
        "Election security must be a top priority.",
        "The evidence presented is not convincing.",
        "This undermines trust in democratic institutions.",
        "Both sides engage in disinformation campaigns.",
        "Cyber warfare is the new battleground.",
        "Independent observers found no irregularities.",
        "The timing of these revelations is suspicious.",
        "Sanctions should be imposed immediately.",
        "This is domestic politics, not foreign interference.",
        "Intelligence agencies have confirmed the threats.",
        "We need international election monitoring."
    ]
}

# Sentiment indicators for different types of comments
POSITIVE_INDICATORS = ["hopeful", "optimistic", "good", "progress", "peace", "solution"]
NEGATIVE_INDICATORS = ["concerning", "alarming", "crisis", "devastating", "dangerous", "worse"]
NEUTRAL_INDICATORS = ["complex", "situation", "developing", "monitoring", "observing"]


def generate_user_profile():
    """Generate a random user profile."""
    return {
        "user_id": f"user_{random.randint(10000, 99999)}",
        "username": f"@user{random.randint(1000, 9999)}",
        "followers": random.randint(10, 50000),
        "verified": random.choice([True, False, False, False])  # Most users not verified
    }


def generate_engagement_metrics():
    """Generate realistic engagement metrics."""
    base_likes = random.randint(0, 100)
    return {
        "likes": base_likes,
        "retweets": int(base_likes * random.uniform(0.1, 0.3)),
        "replies": random.randint(0, int(base_likes * 0.5)),
        "shares": random.randint(0, int(base_likes * 0.2))
    }


def generate_timestamp(days_back=7):
    """Generate a random timestamp within the last N days."""
    now = datetime.now()
    random_date = now - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    return random_date.isoformat()


def create_mock_comments(topic, num_comments=50):
    """
    Create mock social media comments for a topic.
    
    Args:
        topic: Topic key (e.g., 'ukraine_russia')
        num_comments: Number of comments to generate
        
    Returns:
        List of comment dictionaries
    """
    if topic not in COMMENT_TEMPLATES:
        topic = random.choice(list(COMMENT_TEMPLATES.keys()))
    
    comments = []
    comment_pool = COMMENT_TEMPLATES[topic]
    
    for i in range(num_comments):
        comment_text = random.choice(comment_pool)
        
        comment = {
            "comment_id": f"comment_{random.randint(100000, 999999)}",
            "text": comment_text,
            "user": generate_user_profile(),
            "timestamp": generate_timestamp(),
            "engagement": generate_engagement_metrics(),
            "platform": random.choice(["twitter", "reddit", "facebook"]),
            "topic": topic,
            "language": "en"
        }
        
        comments.append(comment)
    
    return comments


def create_mock_social_dataset():
    """Create a complete mock social media dataset."""
    
    all_comments = []
    
    print("Generating mock social media data...")
    print("=" * 60)
    
    for topic in COMMENT_TEMPLATES.keys():
        num_comments = random.randint(30, 60)
        print(f"Generating {num_comments} comments for: {topic}")
        
        comments = create_mock_comments(topic, num_comments)
        all_comments.extend(comments)
    
    # Create output directory
    output_dir = Path("data/raw/social")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save all comments
    output_file = output_dir / "mock_social_comments.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_comments": len(all_comments),
            "topics": list(COMMENT_TEMPLATES.keys()),
            "comments": all_comments
        }, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print(f"✓ Generated {len(all_comments)} mock comments")
    print(f"✓ Saved to: {output_file}")
    
    # Generate statistics
    print("\n" + "=" * 60)
    print("DATASET STATISTICS")
    print("=" * 60)
    
    # Count by topic
    topic_counts = {}
    platform_counts = {}
    
    for comment in all_comments:
        topic = comment['topic']
        platform = comment['platform']
        
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    print("\nComments by Topic:")
    for topic, count in sorted(topic_counts.items()):
        print(f"  {topic:20s}: {count}")
    
    print("\nComments by Platform:")
    for platform, count in sorted(platform_counts.items()):
        print(f"  {platform:10s}: {count}")
    
    print("\n" + "=" * 60)
    print("✅ MOCK DATA GENERATION COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run sentiment analysis on these comments")
    print("2. Run emotion analysis on these comments")
    print("3. Analyze polarization patterns")
    
    return output_file


def main():
    """Generate mock social media dataset."""
    create_mock_social_dataset()


if __name__ == "__main__":
    main()