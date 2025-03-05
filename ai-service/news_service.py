import os
import sys
import logging
import json
import requests
from dotenv import load_dotenv
import time
from pathlib import Path
from api_client import ApiClient

# .env dosyasını yükle
load_dotenv()

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO if os.getenv("LOG_LEVEL", "INFO") == "INFO" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "news_service.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class NewsService:
    """Haber servisi, Guardian API'den haber almak ve işlemek için kullanılır."""
    
    def __init__(self):
        """Haber servisini başlatır ve API istemcisini yapılandırır."""
        self._load_config()
        self.guardian_client = ApiClient(
            base_url=self.guardian_api_url,
            api_key=self.guardian_api_key,
            timeout=int(os.getenv("REQUEST_TIMEOUT", "30"))
        )
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8080")
        self.backend_api_path = os.getenv("BACKEND_API_PATH", "/api/v1")
        
    def _load_config(self):
        """Yapılandırma değerlerini çevre değişkenlerinden yükler."""
        self.guardian_api_key = os.getenv("GUARDIAN_API_KEY")
        if not self.guardian_api_key:
            logger.error("Guardian API anahtarı bulunamadı! .env dosyasını kontrol edin.")
            raise ValueError("Guardian API anahtarı gerekli")
            
        self.guardian_api_url = os.getenv("GUARDIAN_API_URL", "https://content.guardianapis.com")
        
    def fetch_news(self, category="business", page_size=20):
        """
        Guardian API'den belirtilen kategoride haberleri getirir.
        
        Args:
            category: Haber kategorisi
            page_size: Sayfa başına haber sayısı
            
        Returns:
            List[Dict]: Haber makalelerinin listesi
        """
        try:
            params = {
                'section': category,
                'page-size': page_size,
                'show-fields': 'headline,trailText,bodyText,thumbnail,publication',
                'order-by': 'newest'
            }
            
            response_data = self.guardian_client.get('search', params)
            
            if not response_data or 'response' not in response_data:
                logger.error("Guardian API'den geçersiz yanıt alındı")
                return []
                
            news_items = response_data['response'].get('results', [])
            
            # Haber öğelerini standart formata dönüştür
            formatted_news = []
            for item in news_items:
                news_article = {
                    'externalId': item.get('id', ''),
                    'title': item.get('webTitle', ''),
                    'content': item.get('fields', {}).get('bodyText', ''),
                    'summary': item.get('fields', {}).get('trailText', ''),
                    'category': category,
                    'sourceUrl': item.get('webUrl', ''),
                    'sourceName': 'The Guardian',
                    'publishedDate': item.get('webPublicationDate', ''),
                    'imageUrl': item.get('fields', {}).get('thumbnail', '')
                }
                formatted_news.append(news_article)
                
            return formatted_news
                
        except Exception as e:
            logger.error(f"Haber getirme hatası: {str(e)}")
            return []
            
    def save_news_to_backend(self, news_articles):
        """
        Haber makalelerini backend'e kaydeder.
        
        Args:
            news_articles: Kaydedilecek haber makaleleri listesi
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        try:
            url = f"{self.backend_url}{self.backend_api_path}/agent/saveNews"
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'SummaryFinance-NewsService/1.0'
            }
            
            response = requests.post(
                url, 
                json=news_articles, 
                headers=headers, 
                timeout=int(os.getenv("REQUEST_TIMEOUT", "30"))
            )
            
            if response.status_code == 200:
                logger.info(f"{len(news_articles)} haber makalesi backend'e başarıyla kaydedildi")
                return True
            else:
                logger.error(f"Backend'e haber kaydedilirken hata: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Backend'e haber kaydedilirken hata: {str(e)}")
            return False
            
    def run(self, categories=None):
        """
        Servis ana işlem döngüsü. Belirtilen kategorilerde haberleri getirir ve kaydeder.
        
        Args:
            categories: İşlenecek haber kategorileri listesi
        """
        if categories is None:
            categories = ["business", "money", "world", "uk-news", "politics"]
            
        for category in categories:
            logger.info(f"{category} kategorisinde haberler getiriliyor...")
            news_articles = self.fetch_news(category=category)
            
            if news_articles:
                logger.info(f"{len(news_articles)} haber makalesi bulundu")
                success = self.save_news_to_backend(news_articles)
                if success:
                    logger.info(f"{category} kategorisindeki haberler başarıyla işlendi")
                else:
                    logger.error(f"{category} kategorisindeki haberler işlenirken hata oluştu")
            else:
                logger.warning(f"{category} kategorisinde haber bulunamadı")
                
    def cleanup(self):
        """Kaynakları temizler"""
        if hasattr(self, 'guardian_client'):
            self.guardian_client.close()

if __name__ == "__main__":
    try:
        service = NewsService()
        service.run()
    except Exception as e:
        logger.critical(f"Servis çalışırken kritik hata: {str(e)}")
    finally:
        if 'service' in locals():
            service.cleanup() 