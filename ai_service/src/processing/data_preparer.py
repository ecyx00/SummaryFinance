import logging
import os
from pathlib import Path
from typing import List, Dict
from sqlalchemy.orm import Session

# Logger oluştur
logger = logging.getLogger(__name__)

# NLTK gerekli veri setini indir (ilk çalıştırmada gerekli)
import nltk

def ensure_nltk_punkt_is_downloaded():
    """NLTK punkt ve punkt_tab tokenizer'larının yüklü olduğundan emin olur, gerekirse indirir."""
    # NLTK'nın varsayılan veri yollarını logla
    logger.info(f"NLTK'nın aradığı veri yolları: {nltk.data.path}")
    
    # Özel bir indirme dizini oluştur (ai_service içinde)
    project_dir = Path(os.path.abspath(__file__)).parent.parent.parent  # ai_service dizini
    nltk_data_dir = os.path.join(project_dir, ".nltk_data")
    
    # Dizin yoksa oluştur
    if not os.path.exists(nltk_data_dir):
        os.makedirs(nltk_data_dir)
        logger.info(f"NLTK veri dizini oluşturuldu: {nltk_data_dir}")
    
    # NLTK'nın arama yollarına ekle
    if nltk_data_dir not in nltk.data.path:
        nltk.data.path.append(nltk_data_dir)
        logger.info(f"NLTK arama yollarına eklendi: {nltk_data_dir}")
    
    resources_to_download = ['punkt', 'punkt_tab']
    resources_missing = []
    
    # Önce hangi kaynakların eksik olduğunu tespit et
    for resource in resources_to_download:
        try:
            nltk.data.find(f'tokenizers/{resource}')
            logger.info(f"NLTK '{resource}' tokenizer zaten yüklü.")
        except LookupError:
            resources_missing.append(resource)
            logger.warning(f"NLTK '{resource}' tokenizer bulunamadı, indirme listesine ekleniyor.")
    
    # Eksik kaynakları indir
    if resources_missing:
        logger.info(f"Toplam {len(resources_missing)} NLTK kaynağı indirilecek: {', '.join(resources_missing)}")
        
        for resource in resources_missing:
            try:
                # Özel dizine indir ve detaylı loglama yap
                logger.info(f"'{resource}' indiriliyor... Hedef: {nltk_data_dir}")
                nltk.download(resource, download_dir=nltk_data_dir, quiet=False, raise_on_error=True) 
                
                # İndirme sonrası kontrol et
                try:
                    nltk.data.find(f'tokenizers/{resource}')
                    logger.info(f"NLTK '{resource}' başarıyla indirildi ve doğrulandı.")
                except LookupError:
                    logger.error(f"NLTK '{resource}' indirildi, ancak hala bulunamıyor!")
                    raise
            except Exception as e:
                logger.error(f"NLTK '{resource}' indirilirken HATA oluştu: {e}")
                logger.error(f"Lütfen manuel olarak Python konsolunda `import nltk; nltk.download('{resource}', download_dir='{nltk_data_dir}')` komutunu çalıştırmayı deneyin.")
                logger.warning(f"NLTK '{resource}' eksikliği nedeniyle anahtar kelime çıkarma gibi NLP fonksiyonları düzgün çalışmayabilir.")
    else:
        logger.info("Tüm NLTK kaynakları zaten yüklü.")

# Bu modül ilk import edildiğinde NLTK kontrolünü ve indirmesini yap
ensure_nltk_punkt_is_downloaded()

from src.db.crud import get_unprocessed_news
from src.core.config import settings
from .content_scraper import get_newspaper_config, scrape_and_prepare_news_batch

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
