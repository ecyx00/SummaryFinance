import logging
from typing import List, Dict
from sqlalchemy.orm import Session

# NLTK gerekli veri setini indir (ilk çalıştırmada gerekli)
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

from src.db.crud import get_unprocessed_news
from src.core.config import settings
from .content_scraper import get_newspaper_config, scrape_and_prepare_news_batch

# Logger oluştur
logger = logging.getLogger(__name__)


def prepare_news_for_analysis(db: Session) -> List[Dict]:
    """Veritabanından işlenmemiş haberleri alır, içeriklerini çeker ve analiz için hazırlar.
    
    Args:
        db: SQLAlchemy veritabanı oturumu
        
    Returns:
        Analiz için hazırlanmış haber sözlüklerinin listesi
    """
    # Newspaper3k konfigürasyonunu al
    newspaper_config = get_newspaper_config()
    
    # Veritabanından TÜM işlenmemiş haberleri al (sınırsız)
    unprocessed_news = get_unprocessed_news(db, None)
    
    if not unprocessed_news:
        logger.info("İşlenecek yeni haber bulunamadı.")
        return []
    
    logger.info(f"{len(unprocessed_news)} adet işlenmemiş haber bulundu. İçerik çekimi başlatılıyor...")
    
    # Haberleri hazırla ve içeriklerini çek
    prepared_news = scrape_and_prepare_news_batch(unprocessed_news, newspaper_config)
    
    logger.info(f"{len(prepared_news)} adet haber başarıyla hazırlandı ve içerikleri çekildi.")
    
    return prepared_news
