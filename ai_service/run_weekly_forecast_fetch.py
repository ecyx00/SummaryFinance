#!/usr/bin/env python
"""
Weekly Economic Calendar Forecast Fetcher

Bu script, haftada bir kez çalıştırılarak gelecek 7-14 gün için planlanan ekonomik olayların
tahmin değerlerini FMP API'sinden çeker ve veritabanına kaydeder. Cron job veya
benzeri bir zamanlayıcı ile haftada bir kez çalıştırılması önerilir.
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
        logging.FileHandler('logs/weekly_forecast_fetch.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_log_directory():
    """Log dizininin var olduğundan emin ol."""
    if not os.path.exists('logs'):
        os.makedirs('logs')


def run_weekly_forecast_job():
    """Gelecek 7-14 gün için ekonomik olayların tahminlerini çeker ve kaydeder."""
    try:
        logger.info("Haftalık ekonomik takvim tahmin çekme işlemi başlatılıyor...")
        
        # Fetcher ve PersistenceManager nesnelerini oluştur
        fetcher = EconomicCalendarFetcher()
        persistence = PersistenceManager()
        
        # Tarih aralığını belirle (bugünden itibaren 14 gün)
        today = datetime.now().date()
        start_date = today.strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        
        logger.info(f"Ekonomik takvim verileri çekiliyor: {start_date} - {end_date}")
        
        # Verileri çek
        events = fetcher.run_fetch_job(from_date=start_date, to_date=end_date)
        
        if not events:
            logger.warning("Belirtilen tarih aralığında ekonomik olay bulunamadı.")
            return
            
        logger.info(f"Toplam {len(events)} ekonomik olay çekildi.")
        
        # Verileri veritabanına kaydet
        success = persistence.save_economic_events(events)
        
        if success:
            logger.info("Haftalık ekonomik takvim tahminleri başarıyla kaydedildi.")
        else:
            logger.error("Haftalık ekonomik takvim tahminleri kaydedilemedi.")
        
    except Exception as e:
        logger.error(f"Haftalık ekonomik takvim çekme işlemi sırasında hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ensure_log_directory()
    logger.info("=== Haftalık Ekonomik Takvim Çekme İşi Başlatılıyor ===")
    run_weekly_forecast_job()
    logger.info("=== Haftalık Ekonomik Takvim Çekme İşi Tamamlandı ===")
