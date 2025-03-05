from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import os
from dotenv import load_dotenv
from agents.agent_manager import AgentManager
from services.news_fetcher import GuardianNewsFetcher

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="SummaryFinance AI Service")

# Get API keys from environment variables
google_api_key = os.getenv("GOOGLE_API_KEY")
guardian_api_key = os.getenv("GUARDIAN_API_KEY")

if not google_api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")
if not guardian_api_key:
    raise ValueError("GUARDIAN_API_KEY environment variable is not set")

# Initialize services
agent_manager = AgentManager(google_api_key)
news_fetcher = GuardianNewsFetcher(guardian_api_key)

class NewsInput(BaseModel):
    title: str
    content: str
    source_name: str
    category: str

class AnalysisResult(BaseModel):
    summary: str
    sentiment_score: float
    sentiment_explanation: str
    key_points: List[str]
    main_topics: List[str]

class NewsArticle(BaseModel):
    title: str
    content: str
    source_url: str
    source_name: str
    category: str
    published_date: str

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_news(news: NewsInput):
    try:
        # Create full text for analysis
        full_text = f"""
        Title: {news.title}
        Source: {news.source_name}
        Category: {news.category}
        
        Content:
        {news.content}
        """
        
        # Process with agent manager
        result = await agent_manager.analyze_text(full_text)
        
        return AnalysisResult(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/news/fetch", response_model=List[NewsArticle])
async def fetch_news(
    query: Optional[str] = None,
    section: Optional[str] = None,
    page_size: int = 10
):
    """Fetch news articles from The Guardian"""
    try:
        articles = await news_fetcher.fetch_news(query, section, page_size)
        return [NewsArticle(**article) for article in articles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/news/fetch-and-analyze")
async def fetch_and_analyze(
    query: Optional[str] = None,
    section: Optional[str] = "business",
    page_size: int = 1
):
    """Fetch news and perform AI analysis"""
    try:
        # First fetch the news
        articles = await news_fetcher.fetch_news(query, section, page_size)
        if not articles:
            raise HTTPException(status_code=404, detail="No articles found")
            
        # Analyze first article
        article = articles[0]
        news_input = NewsInput(
            title=article["title"],
            content=article["content"],
            source_name=article["source_name"],
            category=article["category"]
        )
        
        # Get analysis
        analysis = await analyze_news(news_input)
        
        # Return combined result
        return {
            "article": article,
            "analysis": analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI Analysis Service",
        "guardianAPI": "configured",
        "googleAI": "configured"
    }
