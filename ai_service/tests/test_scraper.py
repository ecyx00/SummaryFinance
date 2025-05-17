#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

# Bu script'in bulunduğu dizinin bir üst dizinini (ai_service) al
# Sonra bu yola 'src' ekleyerek src klasörünün tam yolunu oluştur
# ve Python'ın import yolları listesine ekle.
# Bu, 'src' klasörünün 'tests' klasörüyle aynı seviyede olduğunu varsayar.
# Eğer 'tests' klasörü 'src'nin içindeyse veya yapı farklıysa, bu yol ayarlanmalıdır.
# Mevcut yapı: ai_service -> tests ve ai_service -> src şeklinde.

# NOT: Bu kodlar VS Code/Pylance için gereksiz olabilir, ancak terminal üzerinden
# script'i çalıştırırken gereklidir.
# current_script_path = os.path.abspath(__file__) # .../ai_service/tests/test_scraper.py
# tests_dir = os.path.dirname(current_script_path)  # .../ai_service/tests
# ai_service_dir = os.path.dirname(tests_dir)       # .../ai_service
# src_dir_path = os.path.join(ai_service_dir, 'src')  # .../ai_service/src

# if src_dir_path not in sys.path:
#     sys.path.insert(0, src_dir_path)

"""
Test script for the content_scraper module.
Tests the _scrape_single_article_content and scrape_and_prepare_news_batch functions.
"""

import logging
from datetime import datetime

# Gerekli modülleri import ediyoruz
# Not: .vscode/settings.json ayarları ile Python, ai_service/src klasörünü import yolu olarak tanıyor
from src.core.logging_config import setup_logging
from src.core.config import settings
from src.processing.content_scraper import get_newspaper_config, _scrape_single_article_content, scrape_and_prepare_news_batch
from src.db.models import News


# Test edilecek URL'ler
test_urls = [
    # NYTimes'dan çalışan URL'ler
    "https://www.nytimes.com/2025/05/14/world/middleeast/trump-middle-east-nation-building.html",
    "https://www.nytimes.com/2025/05/14/world/middleeast/trump-syria-al-shara-sanctions.html",
    
    # Guardian'dan çalışan URL'ler
    "https://www.theguardian.com/world/2025/may/14/kremlin-tight-lipped-for-third-day-on-whether-putin-will-meet-zelenskyy",
    
    # Var olmayan/hatalı URL'ler
    "https://www.example.com/bu-sayfa-yok",
    
    # Haber içeriği değil kategori sayfası
    "https://www.nytimes.com/section/business",
    
    # JavaScript ile dinamik yüklenen içerik
    "https://www.wsj.com/articles/federal-reserve-meeting-interest-rates-inflation-11683124889"
]


def create_test_news_objects():
    """Test için sahte News nesneleri oluştur."""
    test_news_list = []
    
    for i, url in enumerate(test_urls[:4]):  # Sadece ilk 4 URL için (çalışması beklenenler)
        news_item = News(
            id=1000 + i,
            url=url,
            title=f"Test Haber Başlığı {i+1}",
            source="NYTimes" if i < 2 else "Guardian",
            publication_date=datetime.now(),
            fetched_at=datetime.now()
        )
        test_news_list.append(news_item)
    
    return test_news_list


def run_scraper_test():
    """Content scraper modülündeki fonksiyonları test et."""
    # Loglama sistemini başlat
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Content scraper testi başlatılıyor...")
    
    # Newspaper konfigürasyonunu al
    newspaper_config = get_newspaper_config()
    
    # _scrape_single_article_content fonksiyonunu test et
    logger.info("--- _scrape_single_article_content fonksiyonu testi başlıyor ---")
    for i, url in enumerate(test_urls):
        logger.info(f"URL {i+1}/{len(test_urls)} test ediliyor: {url}")
        content = _scrape_single_article_content(url, newspaper_config)
        
        if content:
            logger.info(f"    Başarı! Metin çekildi. Uzunluk: {len(content)} karakter")
            # İlk 100 karakteri göster
            logger.info(f"    İçerik önizleme: {content[:100]}...")
        else:
            logger.warning(f"    Başarısız! İçerik çekilemedi.")
    
    # scrape_and_prepare_news_batch fonksiyonunu test et
    logger.info("--- scrape_and_prepare_news_batch fonksiyonu testi başlıyor ---")
    
    # Test için sahte News nesneleri oluştur
    test_news_list = create_test_news_objects()
    logger.info(f"Oluşturulan test News nesnesi sayısı: {len(test_news_list)}")
    
    # scrape_and_prepare_news_batch fonksiyonunu çağır
    prepared_news = scrape_and_prepare_news_batch(test_news_list, newspaper_config)
    
    # Sonuçları logla
    logger.info(f"Başarılı içerik çekilen haber sayısı: {len(prepared_news)}/{len(test_news_list)}")
    
    # Başarılı sonuçların içeriğini kontrol et
    for i, news_dict in enumerate(prepared_news):
        logger.info(f"Haber {i+1}:")
        logger.info(f"    ID: {news_dict['id']}")
        logger.info(f"    Başlık: {news_dict['title']}")
        logger.info(f"    Kaynak: {news_dict['source']}")
        logger.info(f"    İçerik uzunluğu: {len(news_dict['content'])} karakter")
        logger.info(f"    İçerik önizleme: {news_dict['content'][:100]}...")
    
    logger.info("Content scraper testi tamamlandı.")


if __name__ == "__main__":
    run_scraper_test() 