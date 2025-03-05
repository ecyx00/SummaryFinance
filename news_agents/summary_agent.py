import google.generativeai as genai
import mysql.connector

class NewsSummaryAgent:
    def __init__(self, gemini_api_key, db_config):
        self.model = genai.configure(api_key=gemini_api_key)
        self.db = mysql.connector.connect(**db_config)
    
    async def generate_summaries(self):
        """İlişkili haber gruplarını özetler"""
        clusters = self._fetch_recent_clusters()
        
        for cluster in clusters:
            summary = await self._generate_cluster_summary(cluster)
            await self._store_summary(cluster['cluster_id'], summary)
    
    async def _generate_cluster_summary(self, cluster):
        prompt = self._create_summary_prompt(cluster)
        response = await self.model.generate_content(prompt)
        return self._parse_summary_response(response) 