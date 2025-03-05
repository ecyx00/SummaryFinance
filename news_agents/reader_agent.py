import logging
import mysql.connector

class NewsReaderAgent:
    def __init__(self, guardian_api_key, db_config):
        self.api_key = guardian_api_key
        self.db = mysql.connector.connect(**db_config)
        self.categories = {
            'primary': ['business', 'money', 'technology'],
            'secondary': ['world', 'uk-news', 'environment', 
                         'global-development', 'science'],
            'opinion': ['guardian-view', 'columnists', 'opinion']
        }
    
    async def fetch_and_store_news(self):
        """Haberleri çeker ve veritabanına kaydeder"""
        try:
            for category_type, categories in self.categories.items():
                for category in categories:
                    articles = await self._fetch_category(category)
                    await self._store_articles(articles, category_type)
        except Exception as e:
            logging.error(f"Haber çekme hatası: {str(e)}")
            raise

    async def _store_articles(self, articles, category_type):
        cursor = self.db.cursor()
        for article in articles:
            sql = """INSERT IGNORE INTO news_articles 
                     (guardian_id, title, category, publication_date, 
                      content, url) VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (
                article['id'],
                article['title'],
                article['category'],
                article['date'],
                article['content'],
                article['url']
            ))
        self.db.commit() 