import logging
from typing import List, Dict, Optional
from datetime import datetime

import newspaper
from newspaper import Article
from sqlalchemy.orm import Session

from src.db.models import News

# Logger oluştur
logger = logging.getLogger(__name__)

# Genel User-Agent tanımı
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'

# Newspaper konfigürasyonu
def get_newspaper_config() -> newspaper.Config:
    """Newspaper3k için varsayılan konfigürasyon oluşturur."""
    config = newspaper.Config()
    config.browser_user_agent = USER_AGENT
    config.request_timeout = 10
    config.fetch_images = False
    config.memoize_articles = False
    return config


def _scrape_single_article_content(url: str, config: newspaper.Config) -> Optional[str]:
    """Tek bir URL'den haber içeriğini çeker.
    
    Args:
        url: Haber içeriğinin çekileceği URL
        config: Newspaper3k konfigürasyonu
        
    Returns:
        Çekilen haber metni veya None (başarısızlık durumunda)
    """
    if not url or not url.startswith(('http://', 'https://')):
        logger.warning(f"Geçersiz URL: {url}")
        return None
    
    try:
        # Article nesnesi oluştur ve indir
        article = Article(url, config=config, language='en')
        article.download()
        
        # İndirme durumunu kontrol et
        if article.download_state != 2:  # 2: İndirme başarılı
            logger.warning(f"İçerik indirilemedi. URL: {url}, Durum: {article.download_state}")
            return None
        
        # Article.download_exception_msg kontrol et
        if hasattr(article, 'download_exception_msg') and article.download_exception_msg:
            logger.warning(f"İndirme hatası. URL: {url}, Hata: {article.download_exception_msg}")
            return None
        
        # İçeriği ayrıştır
        article.parse()
        
        # İçerik uzunluğunu kontrol et
        if not article.text or len(article.text.strip()) < 150:  # Minimum 150 karakter
            logger.warning(f"Yetersiz içerik uzunluğu. URL: {url}, Uzunluk: {len(article.text) if article.text else 0}")
            return None
        
        logger.info(f"İçerik başarıyla çekildi. URL: {url}, Uzunluk: {len(article.text)}")
        return article.text
    
    except Exception as e:
        logger.error(f"İçerik çekme hatası. URL: {url}, Hata: {str(e)}")
        return None


def scrape_and_prepare_news_batch(news_items_from_db: List[News], newspaper_config: newspaper.Config) -> List[Dict]:
    """Veritabanından alınan haber listesi için içerik çeker ve analiz için hazırlar.
    
    Args:
        news_items_from_db: Veritabanından alınan News nesneleri listesi
        newspaper_config: Newspaper3k konfigürasyonu
        
    Returns:
        İçeriği başarıyla çekilen haberlerin bilgilerini içeren sözlük listesi
    """
    results = []
    
    logger.info(f"İşlenecek haber sayısı: {len(news_items_from_db)}")
    
    for news_item in news_items_from_db:
        # Haberin URL'den içeriğini çek
        content = _scrape_single_article_content(news_item.url, newspaper_config)
        
        # İçerik başarıyla çekildiyse sonuç listesine ekle
        if content:
            # ISO formatında tarih
            publication_date_str = news_item.publication_date.isoformat() if news_item.publication_date else None
            
            # Sonuç sözlüğü oluştur
            result_dict = {
                "id": str(news_item.id),
                "title": news_item.title,
                "source": news_item.source,
                "publication_date": publication_date_str,
                "content": content
            }
            
            results.append(result_dict)
        else:
            logger.warning(f"İçerik çekilemedi, haber atlandı. ID: {news_item.id}, URL: {news_item.url}")
    
    logger.info(f"Başarıyla içerik çekilen haber sayısı: {len(results)}")
    return results


# NLTK için ek indirimlerin yorum satırı olarak eklenmesi
"""
# İlk kullanımda NLTK'nin gerekli verilerini indirmek için:
import nltk
nltk.download('punkt')
""" 