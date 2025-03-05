import logging
from .reader_agent import NewsReaderAgent
from .relation_agent import NewsRelationAgent
from .summary_agent import NewsSummaryAgent

class NewsAnalysisOrchestrator:
    def __init__(self, config):
        self.reader = NewsReaderAgent(
            config['guardian_api_key'], 
            config['db_config']
        )
        self.relation_analyzer = NewsRelationAgent(
            config['gemini_api_key'], 
            config['db_config']
        )
        self.summarizer = NewsSummaryAgent(
            config['gemini_api_key'], 
            config['db_config']
        )
    
    async def run_analysis(self):
        """Tüm analiz sürecini yönetir"""
        try:
            # 1. Haberleri çek ve kaydet
            await self.reader.fetch_and_store_news()
            
            # 2. İlişkileri analiz et
            await self.relation_analyzer.analyze_relations()
            
            # 3. Özetleri oluştur
            await self.summarizer.generate_summaries()
            
        except Exception as e:
            logging.error(f"Analiz hatası: {str(e)}")
            raise 