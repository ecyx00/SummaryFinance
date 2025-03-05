import os
from typing import Dict, Any
from .summarizer_agent import SummarizerAgent
from .sentiment_agent import SentimentAgent
from .key_points_agent import KeyPointsAgent

class AgentManager:
    """Manages and coordinates all AI agents"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.agents = {
            'summarizer': SummarizerAgent(api_key),
            'sentiment': SentimentAgent(api_key),
            'key_points': KeyPointsAgent(api_key)
        }
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """Process text through all agents and combine results"""
        
        # Process with each agent
        summary_result = self.agents['summarizer'].process(text)
        sentiment_result = self.agents['sentiment'].process(text)
        key_points_result = self.agents['key_points'].process(text)
        
        # Combine results
        return {
            "summary": summary_result["summary"],
            "sentiment_score": sentiment_result["sentiment_score"],
            "sentiment_explanation": sentiment_result["sentiment_explanation"],
            "key_points": key_points_result["key_points"],
            "main_topics": key_points_result["main_topics"]
        }
