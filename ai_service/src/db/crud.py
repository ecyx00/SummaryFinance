from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.sql import exists

from .models import News, AnalyzedNewsLink


def get_unprocessed_news(db: Session, batch_size: int) -> List[News]:
    """İşlenmemiş (analiz edilmemiş) haberleri veritabanından çeker.
    
    İşlenmemiş haberler, News tablosunda olup AnalyzedNewsLink tablosunda
    karşılığı olmayan haberlerdir.
    
    Args:
        db: SQLAlchemy veritabanı oturumu
        batch_size: Çekilecek maksimum haber sayısı
        
    Returns:
        List[News]: İşlenmemiş haberlerin listesi, fetched_at'e göre en yeniden eskiye sıralı
    """
    # NOT EXISTS alt sorgusu ile işlenmemiş haberleri bul
    # Bu, News.id'si AnalyzedNewsLink.original_news_id'de olmayan kayıtları seçer
    stmt = ~exists().where(AnalyzedNewsLink.original_news_id == News.id)
    
    # Sorguyu oluştur, filtrele ve sırala
    query = db.query(News)\
        .filter(stmt)\
        .order_by(News.fetched_at.desc())
    
    # Eğer batch_size belirtilmişse limit uygula
    if batch_size is not None:
        query = query.limit(batch_size)
    
    # Sorguyu çalıştır ve sonuçları döndür
    return query.all()


# Alternatif yöntem: LEFT OUTER JOIN + IS NULL
def get_unprocessed_news_alt(db: Session, batch_size: int) -> List[News]:
    """İşlenmemiş (analiz edilmemiş) haberleri veritabanından çeker.
    
    Bu fonksiyon, get_unprocessed_news ile aynı işlevi LEFT OUTER JOIN
    kullanarak gerçekleştirir.
    
    Args:
        db: SQLAlchemy veritabanı oturumu
        batch_size: Çekilecek maksimum haber sayısı
        
    Returns:
        List[News]: İşlenmemiş haberlerin listesi, fetched_at'e göre en yeniden eskiye sıralı
    """
    # News tablosunu AnalyzedNewsLink ile LEFT OUTER JOIN yap
    # News.id = AnalyzedNewsLink.news_id olacak şekilde
    # AnalyzedNewsLink.id IS NULL olanları filtrele (ilişkisi olmayanlar)
    query = db.query(News)\
        .outerjoin(AnalyzedNewsLink, News.id == AnalyzedNewsLink.news_id)\
        .filter(AnalyzedNewsLink.id == None)\
        .order_by(News.fetched_at.desc())\
        .limit(batch_size)
    
    return query.all()


# Test etmek için örnek kod (yorum satırı olarak):
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
from db.database import SessionLocal

# Test için Session oluştur
def test_get_unprocessed_news():
    db = SessionLocal()
    try:
        # batch_size = 10 ile haberleri çek
        unprocessed_news = get_unprocessed_news(db, 10)
        print(f"İşlenmemiş haber sayısı: {len(unprocessed_news)}")
        for news in unprocessed_news:
            print(f"ID: {news.id}, Başlık: {news.title}, Tarih: {news.fetched_at}")
    finally:
        db.close()

# Alternatif fonksiyonu test et
def test_get_unprocessed_news_alt():
    db = SessionLocal()
    try:
        unprocessed_news = get_unprocessed_news_alt(db, 10)
        print(f"İşlenmemiş haber sayısı (alt): {len(unprocessed_news)}")
    finally:
        db.close()
"""
