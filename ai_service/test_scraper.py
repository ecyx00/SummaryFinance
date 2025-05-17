import logging
from processing.content_scraper import get_newspaper_config, _scrape_single_article_content

# Loglama ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scraper():
    """Scraper'ın test edilmesi için basit bir fonksiyon"""
    # Test edilecek URL örnekleri
    test_urls = [
        "https://www.bloomberg.com/news/articles/2023-12-01/stock-market-today-dow-s-p-live-updates",
        "https://www.reuters.com/business/finance/",
        "https://www.ft.com/markets",
        # İsterseniz daha fazla test URL'si ekleyebilirsiniz
    ]
    
    # Newspaper3k konfigürasyonu al
    config = get_newspaper_config()
    
    logger.info("Scraper testi başlatılıyor...")
    
    # Her URL için test yap
    for url in test_urls:
        logger.info(f"Test ediliyor: {url}")
        
        # İçeriği çek
        content = _scrape_single_article_content(url, config)
        
        # Sonucu kontrol et
        if content:
            logger.info(f"Başarılı! İçerik uzunluğu: {len(content)} karakter")
            # İçeriğin ilk 100 karakterini göster
            logger.info(f"İçerik örneği: {content[:100]}...")
        else:
            logger.error(f"Başarısız! İçerik çekilemedi: {url}")

if __name__ == "__main__":
    test_scraper()
