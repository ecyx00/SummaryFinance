import logging
from fastapi import FastAPI, BackgroundTasks
from sqlalchemy.orm import Session

# Mutlak import kullanarak
from src.core.logging_config import setup_logging
from src.core.config import settings
from src.db.database import SessionLocal
from src.processing.data_preparer import prepare_news_for_analysis

# Loglama sistemini başlat
setup_logging()

# Logger oluştur
logger = logging.getLogger(__name__)

# FastAPI uygulamasını oluştur
app = FastAPI(title="AI Servisi", description="Finans haberleri analiz servisi")

@app.on_event("startup")
async def startup_event():
    """Uygulama başladığında çalışacak fonksiyon."""
    logger.info("AI Servisi Başlatılıyor...")
    logger.info(f"Veritabanı kullanıcısı: {settings.POSTGRES_USER}")
    logger.info(f"Veritabanı: {settings.POSTGRES_DB}")
    logger.info(f"Haber parti boyutu: {settings.NEWS_BATCH_SIZE}")
    logger.info(f"Log seviyesi: {settings.LOG_LEVEL}")
    logger.info(f"Spring Boot submit URL: {settings.SPRING_BOOT_SUBMIT_URL}")

@app.get("/")
async def root():
    """Kök endpoint."""
    logger.info("Kök endpoint çağrıldı")
    return {"message": "AI Servisi Çalışıyor"}

async def analysis_process_background():
    """Analiz sürecini arka planda çalıştıracak fonksiyon."""
    logger.info("Arka plan analiz süreci başlatıldı.")
    
    # Veritabanı oturumu oluştur
    db = SessionLocal()
    try:
        # Veritabanından veri çek ve scraping yap
        prepared_news_list = prepare_news_for_analysis(db)
        
        # Sonuçları logla
        if not prepared_news_list:
            logger.info("Analiz edilecek yeni haber bulunamadı veya içerikleri çekilemedi.")
        else:
            logger.info(f"Toplam {len(prepared_news_list)} adet haber scrape edildi ve Gemini için hazırlandı.")
            
            # İlk birkaç haberin detaylarını logla
            max_preview = min(2, len(prepared_news_list))
            for i in range(max_preview):
                news = prepared_news_list[i]
                logger.info(f"Örnek Haber {i+1}:")
                logger.info(f"  ID: {news['id']}")
                logger.info(f"  Başlık: {news['title']}")
                # İçeriğin ilk 200 karakterini göster
                content_preview = news['content'][:200] + "..." if len(news['content']) > 200 else news['content']
                logger.info(f"  İçerik Önizleme: {content_preview}")
    
    finally:
        # Veritabanı oturumunu kapat
        db.close()
    
    logger.info("Arka plan analiz süreci tamamlandı.")

@app.post("/trigger-analysis")
async def trigger_analysis(background_tasks: BackgroundTasks):
    """Haber analiz sürecini tetikleyen endpoint."""
    logger.info("/trigger-analysis endpoint'i çağrıldı")
    
    # Analiz sürecini arka planda başlat
    background_tasks.add_task(analysis_process_background)
    
    return {"message": "Analiz süreci başlatıldı"}
