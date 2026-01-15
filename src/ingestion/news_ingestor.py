"""
News Ingestion Module - Stage 1
Fetches geopolitical news articles from NewsAPI and saves them.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import time


class NewsIngestor:
    """Fetch and store news articles about geopolitical topics."""
    
    def __init__(self, api_key: str, data_dir: str = "data/raw/news"):
        """
        Initialize the news ingestor.
        
        Args:
            api_key: NewsAPI key
            data_dir: Directory to save news articles
        """
        self.api_key = api_key
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://newsapi.org/v2/everything"
        
    def fetch_news(
        self, 
        query: str = "geopolitics OR international relations OR diplomacy",
        days_back: int = 7,
        language: str = "en",
        sort_by: str = "relevancy",
        max_articles: int = 100
    ) -> List[Dict]:
        """
        Fetch news articles from NewsAPI.
        
        Args:
            query: Search query for articles
            days_back: How many days back to search
            language: Article language
            sort_by: Sort method (relevancy, popularity, publishedAt)
            max_articles: Maximum number of articles to fetch
            
        Returns:
            List of article dictionaries
        """
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        # Build request parameters
        params = {
            "q": query,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
            "language": language,
            "sortBy": sort_by,
            "pageSize": min(max_articles, 100),  # API limit is 100 per request
            "apiKey": self.api_key
        }
        
        print(f"Fetching news articles...")
        print(f"Query: {query}")
        print(f"Date range: {from_date.date()} to {to_date.date()}")
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] != "ok":
                print(f"Error from API: {data.get('message', 'Unknown error')}")
                return []
            
            articles = data.get("articles", [])
            print(f"✓ Fetched {len(articles)} articles")
            
            return articles
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching news: {e}")
            return []
    
    def clean_article(self, article: Dict) -> Dict:
        """
        Clean and extract relevant fields from article.
        
        Args:
            article: Raw article dictionary from API
            
        Returns:
            Cleaned article dictionary
        """
        return {
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "content": article.get("content", ""),
            "url": article.get("url", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
            "author": article.get("author", "Unknown"),
            "published_at": article.get("publishedAt", ""),
            "fetched_at": datetime.now().isoformat(),
            "url_to_image": article.get("urlToImage", "")
        }
    
    def save_articles(self, articles: List[Dict], filename: Optional[str] = None) -> str:
        """
        Save articles to JSON file.
        
        Args:
            articles: List of article dictionaries
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to saved file
        """
        if not articles:
            print("No articles to save")
            return ""
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_{timestamp}.json"
        
        filepath = self.data_dir / filename
        
        # Clean articles before saving
        cleaned_articles = [self.clean_article(article) for article in articles]
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "fetched_at": datetime.now().isoformat(),
                "total_articles": len(cleaned_articles),
                "articles": cleaned_articles
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {len(cleaned_articles)} articles to: {filepath}")
        return str(filepath)
    
    def fetch_multiple_topics(
        self, 
        topics: List[str],
        days_back: int = 7,
        max_per_topic: int = 50
    ) -> Dict[str, List[Dict]]:
        """
        Fetch articles for multiple geopolitical topics.
        
        Args:
            topics: List of topic queries
            days_back: How many days back to search
            max_per_topic: Max articles per topic
            
        Returns:
            Dictionary mapping topics to articles
        """
        results = {}
        
        for i, topic in enumerate(topics, 1):
            print(f"\n[{i}/{len(topics)}] Fetching: {topic}")
            articles = self.fetch_news(
                query=topic,
                days_back=days_back,
                max_articles=max_per_topic
            )
            results[topic] = articles
            
            # Be nice to the API - rate limiting
            if i < len(topics):
                print("Waiting 2 seconds before next request...")
                time.sleep(2)
        
        return results
    
    def get_statistics(self, articles: List[Dict]) -> Dict:
        """
        Get basic statistics about fetched articles.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Statistics dictionary
        """
        if not articles:
            return {"total": 0}
        
        sources = {}
        for article in articles:
            source = article.get("source", {}).get("name", "Unknown")
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "total": len(articles),
            "sources": len(sources),
            "top_sources": dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]),
            "date_range": {
                "earliest": min(a.get("publishedAt", "") for a in articles if a.get("publishedAt")),
                "latest": max(a.get("publishedAt", "") for a in articles if a.get("publishedAt"))
            }
        }


def main():
    """Example usage of NewsIngestor."""
    
    # Load API key from environment
    api_key = os.getenv("NEWS_API_KEY")
    
    if not api_key:
        print("Error: NEWS_API_KEY not found in environment variables")
        print("Please create a .env file with: NEWS_API_KEY=your_key_here")
        return
    
    # Initialize ingestor
    ingestor = NewsIngestor(api_key=api_key)
    
    # Define geopolitical topics to track
    topics = [
        "Ukraine Russia conflict",
        "China Taiwan geopolitics",
        "Middle East diplomacy",
        "NATO expansion",
        "election interference"
    ]
    
    print("="*60)
    print("GEOPOLITICAL NEWS INGESTION - STAGE 1")
    print("="*60)
    
    # Fetch articles for each topic
    all_results = ingestor.fetch_multiple_topics(
        topics=topics,
        days_back=7,
        max_per_topic=20
    )
    
    # Save each topic's articles
    print("\n" + "="*60)
    print("SAVING RESULTS")
    print("="*60)
    
    for topic, articles in all_results.items():
        if articles:
            safe_topic = topic.replace(" ", "_").lower()
            filename = f"news_{safe_topic}_{datetime.now().strftime('%Y%m%d')}.json"
            ingestor.save_articles(articles, filename)
            
            # Show statistics
            stats = ingestor.get_statistics(articles)
            print(f"\nStatistics for '{topic}':")
            print(f"  Total articles: {stats['total']}")
            print(f"  Unique sources: {stats['sources']}")
            print(f"  Top sources: {list(stats['top_sources'].keys())[:3]}")
    
    print("\n" + "="*60)
    print("✓ INGESTION COMPLETE")
    print("="*60)
    print(f"Articles saved to: {ingestor.data_dir}")


if __name__ == "__main__":
    main()