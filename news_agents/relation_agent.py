import google.generativeai as genai
import mysql.connector

class NewsRelationAgent:
    def __init__(self, gemini_api_key, db_config):
        self.model = genai.configure(api_key=gemini_api_key)
        self.db = mysql.connector.connect(**db_config)
    
    async def analyze_relations(self):
        """Veritabanındaki haberleri analiz eder"""
        news_items = self._fetch_recent_news()
        clusters = await self._create_clusters(news_items)
        
        for cluster in clusters:
            await self._store_relations(cluster)
    
    async def _create_clusters(self, news_items):
        # Gemini 2.0 Flash ile analiz
        prompt = self._create_analysis_prompt(news_items)
        response = await self.model.generate_content(prompt)
        return self._parse_gemini_response(response) 