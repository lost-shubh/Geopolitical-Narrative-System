"""
Test script for news ingestion.
Fetches a small batch of articles to verify everything works.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import sys

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestion.news_ingestor import NewsIngestor
from utils.logger import setup_logger


def main():
    """Test the news ingestion system."""
    
    # Load environment variables from .env
    load_dotenv()
    
    # Set up logging
    logger = setup_logger("test_ingestion", console_output=True)
    
    logger.info("="*60)
    logger.info("TESTING NEWS INGESTION SYSTEM")
    logger.info("="*60)
    
    # Get API key from environment
    api_key = os.getenv("NEWS_API_KEY")
    
    if not api_key:
        logger.error("❌ NEWS_API_KEY not found in environment variables")
        logger.error("")
        logger.error("Please create a .env file in the project root with:")
        logger.error("NEWS_API_KEY=your_actual_api_key_here")
        logger.error("")
        logger.error("Get your free API key from: https://newsapi.org/register")
        return
    
    logger.info(f"✓ API key loaded (length: {len(api_key)} characters)")
    
    # Initialize ingestor
    try:
        ingestor = NewsIngestor(api_key=api_key)
        logger.info("✓ NewsIngestor initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize NewsIngestor: {e}")
        return
    
    # Test with a single query - Ukraine/Russia conflict
    logger.info("")
    logger.info("📰 Fetching test articles about Ukraine-Russia conflict...")
    logger.info("   (This should take 5-10 seconds)")
    logger.info("")
    
    try:
        articles = ingestor.fetch_news(
            query="Ukraine Russia conflict",
            days_back=3,
            max_articles=10
        )
    except Exception as e:
        logger.error(f"❌ Failed to fetch articles: {e}")
        logger.error("")
        logger.error("Possible issues:")
        logger.error("1. Check your internet connection")
        logger.error("2. Verify your API key is correct")
        logger.error("3. Check if you've exceeded free tier limits (100 requests/day)")
        return
    
    if not articles:
        logger.warning("⚠️  No articles returned")
        logger.warning("This could mean:")
        logger.warning("- No recent articles match the query")
        logger.warning("- API rate limit reached")
        logger.warning("- Invalid API key")
        return
    
    logger.info(f"✓ Successfully fetched {len(articles)} articles")
    logger.info("")
    
    # Show details of the first article
    logger.info("="*60)
    logger.info("SAMPLE ARTICLE PREVIEW")
    logger.info("="*60)
    
    first_article = articles[0]
    logger.info(f"Title:       {first_article.get('title', 'N/A')[:80]}...")
    logger.info(f"Source:      {first_article.get('source', {}).get('name', 'N/A')}")
    logger.info(f"Author:      {first_article.get('author', 'N/A')}")
    logger.info(f"Published:   {first_article.get('publishedAt', 'N/A')}")
    logger.info(f"URL:         {first_article.get('url', 'N/A')[:60]}...")
    
    if first_article.get('description'):
        logger.info(f"Description: {first_article['description'][:100]}...")
    
    logger.info("")
    
    # Save articles to file
    logger.info("="*60)
    logger.info("SAVING ARTICLES")
    logger.info("="*60)
    
    try:
        filepath = ingestor.save_articles(articles, "test_articles.json")
        logger.info(f"✓ {len(articles)} articles saved successfully")
        logger.info(f"📁 Location: {filepath}")
    except Exception as e:
        logger.error(f"❌ Failed to save articles: {e}")
        return
    
    logger.info("")
    
    # Display statistics
    logger.info("="*60)
    logger.info("STATISTICS")
    logger.info("="*60)
    
    try:
        stats = ingestor.get_statistics(articles)
        logger.info(f"Total articles:      {stats['total']}")
        logger.info(f"Unique sources:      {stats['sources']}")
        logger.info(f"Date range:          {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
        logger.info("")
        logger.info("Top 5 sources:")
        for source, count in list(stats['top_sources'].items())[:5]:
            logger.info(f"  • {source}: {count} article(s)")
    except Exception as e:
        logger.warning(f"⚠️  Could not generate statistics: {e}")
    
    logger.info("")
    logger.info("="*60)
    logger.info("✅ TEST COMPLETED SUCCESSFULLY!")
    logger.info("="*60)
    logger.info("")
    logger.info("🎉 Your news ingestion system is working!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Check the saved file: data/raw/news/test_articles.json")
    logger.info("2. Check the log file in: logs/")
    logger.info("3. Run full ingestion: python src/ingestion/news_ingestor.py")
    logger.info("")
    logger.info("For Stage 2 (Sentiment Analysis), tell me:")
    logger.info("'Build Stage 3 - Sentiment Analysis code'")
    logger.info("")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("\nPlease report this error if the issue persists.")
        import traceback
        traceback.print_exc()