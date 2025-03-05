import os
import aiohttp
from typing import Dict, List, Optional, Any
import logging

class GuardianNewsFetcher:
    """Service for fetching news from The Guardian API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://content.guardianapis.com"
        
    async def fetch_news(self, 
                        query: Optional[str] = None, 
                        section: Optional[str] = None,
                        page_size: int = 10) -> List[Dict[str, Any]]:
        """Fetch news articles from The Guardian"""
        
        # Build the query parameters
        params = {
            "api-key": self.api_key,
            "show-fields": "all",
            "page-size": page_size
        }
        
        if query:
            params["q"] = query
        if section:
            params["section"] = section
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/search", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data["response"]["results"]
                        
                        # Transform to our format
                        return [{
                            "title": article["webTitle"],
                            "content": article["fields"].get("bodyText", ""),
                            "source_url": article["webUrl"],
                            "source_name": "The Guardian",
                            "category": article["sectionName"],
                            "published_date": article["webPublicationDate"]
                        } for article in articles]
                    else:
                        logging.error(f"Guardian API error: {response.status}")
                        return []
                        
        except Exception as e:
            logging.error(f"Error fetching news from Guardian: {str(e)}")
            return []
            
    async def search_by_topic(self, topic: str, page_size: int = 5) -> List[Dict[str, Any]]:
        """Search news by specific topic"""
        return await self.fetch_news(query=topic, page_size=page_size)
