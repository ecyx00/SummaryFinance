#!/usr/bin/env python
"""
Daily Economic Calendar Actuals Updater

Bu script, günlük olarak çalıştırılarak son 1-3 gün içindeki ekonomik olayların
gerçekleşen (actual) değerlerini FMP API'sinden çeker ve veritabanını günceller.
Cron job veya benzeri bir zamanlayıcı ile günlük olarak çalıştırılması önerilir.
"""

import sys
import logging
from datetime import datetime, timedelta
import os

# Proje klasörünü Python yoluna ekle
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Bağımlılıkları içe aktar
from data_ingestion.economic_calendar_fetcher import EconomicCalendarFetcher
from src.db.persistence_manager import PersistenceManager
from src.core.config import settings

# Logging yapılandırması
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/daily_actuals_update.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_log_directory():
    """Log dizininin var olduğundan emin ol."""
    if not os.path.exists('logs'):
        os.makedirs('logs')


def run_daily_actuals_job():
    """Son 1-3 gün içindeki ekonomik olayların gerçekleşen değerlerini çeker ve günceller."""
    try:
        logger.info("Günlük ekonomik takvim gerçekleşen değer güncelleme işlemi başlatılıyor...")
        
        # Fetcher ve PersistenceManager nesnelerini oluştur
        fetcher = EconomicCalendarFetcher()
        persistence = PersistenceManager()
        
        # Tarih aralığını belirle (3 gün önceden bugüne)
        today = datetime.now().date()
        end_date = today.strftime("%Y-%m-%d")
        start_date = (today - timedelta(days=3)).strftime("%Y-%m-%d")
        
        logger.info(f"Ekonomik takvim gerçekleşen değerleri çekiliyor: {start_date} - {end_date}")
        
        # Verileri çek
        events = fetcher.run_fetch_job(from_date=start_date, to_date=end_date)
        
        if not events:
            logger.warning("Belirtilen tarih aralığında ekonomik olay bulunamadı.")
            return
            
        logger.info(f"Toplam {len(events)} ekonomik olay çekildi.")
        
        # Gerçekleşen değeri olan olayları filtrele
        events_with_actuals = [event for event in events if event.get('actual_value') is not None]
        logger.info(f"Bunlardan {len(events_with_actuals)} tanesi gerçekleşen değere sahip.")
        
        if not events_with_actuals:
            logger.info("Güncellenecek gerçekleşen değer bulunamadı.")
            return
            
        # Verileri veritabanına kaydet/güncelle
        success = persistence.save_economic_events(events_with_actuals)
        
        if success:
            logger.info("Günlük ekonomik takvim gerçekleşen değerleri başarıyla güncellendi.")
        else:
            logger.error("Günlük ekonomik takvim gerçekleşen değerleri güncellenemedi.")
        
    except Exception as e:
        logger.error(f"Günlük ekonomik takvim güncelleme işlemi sırasında hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ensure_log_directory()
    logger.info("=== Günlük Ekonomik Takvim Güncelleme İşi Başlatılıyor ===")
    run_daily_actuals_job()
    logger.info("=== Günlük Ekonomik Takvim Güncelleme İşi Tamamlandı ===")
