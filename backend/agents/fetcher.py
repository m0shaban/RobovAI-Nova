import feedparser
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def fetch_rss_content(source_url: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetches the latest articles from an RSS feed.
    """
    try:
        logger.info(f"Fetching RSS feed from: {source_url}")
        feed = feedparser.parse(source_url)
        
        if feed.bozo:
            logger.error(f"Error parsing feed {source_url}: {feed.bozo_exception}")
            # Sometimes it's just a malformed feed but still has entries, let's try to proceed
            if not feed.entries:
                return []
                
        articles = []
        for entry in feed.entries[:limit]:
            article = {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "content": ""
            }
            
            # Try to get full content if available
            if "content" in entry and len(entry.content) > 0:
                article["content"] = entry.content[0].value
            elif "description" in entry:
                article["content"] = entry.description
            
            if article["title"] and article["link"]:
                 articles.append(article)
                 
        return articles
        
    except Exception as e:
        logger.error(f"Failed to fetch RSS from {source_url}: {e}")
        return []
