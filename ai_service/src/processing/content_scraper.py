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


def _scrape_single_article_content(url: str, config: newspaper.Config) -> Optional[Article]:
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
        
        # NLP işlemi ve anahtar kelime çıkarma
        try:
            # NLP işlem öncesi NLTK tokenizer kaynaklarını kontrol et
            try:
                import nltk
                for resource in ['punkt', 'punkt_tab']:
                    resource_path = f'tokenizers/{resource}'
                    if nltk.data.find(resource_path):
                        logger.debug(f"NLTK '{resource}' kaynağı mevcut, NLP işlemi için kullanılabilir.")
            except LookupError as lookup_err:
                logger.warning(f"NLP işlemi öncesi NLTK kaynak kontrolü başarısız: {lookup_err}")
                logger.warning("Eksik kaynaklar data_preparer.py'de indirilmiş olmalıydı, ancak yine de NLP işlemi denenecek.")
            
            # NLP işlemini yap
            article.nlp()
            # Başarılı ise, anahtar kelimelerin sayısını logla
            if hasattr(article, 'keywords') and article.keywords:
                logger.info(f"Çıkarılan anahtar kelime sayısı: {len(article.keywords)}, URL: {url}")
        except LookupError as nltk_error:
            # NLTK kaynak hatalarını spesifik olarak yakalayıp logla
            logger.error(f"NLTK kaynak hatası: {str(nltk_error)}")
            logger.error("Bu hata NLTK kaynaklarının eksik olduğunu gösteriyor, data_preparer.py içindeki ensure_nltk_punkt_is_downloaded() fonksiyonu çalıştırıldı mı?")
            # NLP başarısız olsa bile devam ediyoruz, boş anahtar kelime listesi olacak
        except Exception as nlp_error:
            logger.warning(f"NLP işlemi başarısız oldu. URL: {url}, Hata: {str(nlp_error)}")
            # NLP başarısız olsa bile devam ediyoruz, boş anahtar kelime listesi olacak
        
        logger.info(f"İçerik başarıyla çekildi. URL: {url}, Uzunluk: {len(article.text)}")
        return article
    
    except Exception as e:
        logger.error(f"İçerik çekme hatası. URL: {url}, Hata: {str(e)}")
        return None


def scrape_and_prepare_news_batch(news_items_from_db: List[News], newspaper_config: newspaper.Config) -> List[Dict]:
    """İşlenecek haber listesi için içerik çeker, anahtar kelimeler çıkarır ve analiz için hazırlar.
    
    Args:
        news_items_from_db: Veritabanından alınan News nesneleri listesi
        newspaper_config: Newspaper3k konfigürasyonu
        
    Returns:
        İçeriği başarıyla çekilen haberlerin bilgilerini ({id, title, extracted_keywords, content}) içeren sözlük listesi
    """
    results = []
    
    logger.info(f"İşlenecek haber sayısı: {len(news_items_from_db)}")
    
    for news_item in news_items_from_db:
        # Haberin URL'den içeriğini çek
        article = _scrape_single_article_content(news_item.url, newspaper_config)
        
        # Article nesnesi başarıyla oluşturulduysa sonuç listesine ekle
        if article:
            # Anahtar kelimeleri al (NLP işlemi _scrape_single_article_content içinde yapılıyor)
            # Eğer anahtar kelime çıkarılamadıysa boş liste kullan
            extracted_keywords = article.keywords if hasattr(article, 'keywords') and article.keywords else []
            
            # Sonuç sözlüğü oluştur - Gemini için gerekli alanlar ve URL referansı
            result_dict = {
                "id": str(news_item.id),
                "title": news_item.title,
                "extracted_keywords": extracted_keywords,
                "content": article.text,
                "url": news_item.url
            }
            
            results.append(result_dict)
        else:
            logger.warning(f"İçerik çekilemedi, haber atlandı. ID: {news_item.id}, URL: {news_item.url}")
    
    logger.info(f"Başarıyla içerik çekilen ve anahtar kelimeler çıkarılan haber sayısı: {len(results)}")
    return results


# NLTK için ek indirimlerin yorum satırı olarak eklenmesi
"""
# İlk kullanımda NLTK'nin gerekli verilerini indirmek için:
import nltk
nltk.download('punkt')
""" 