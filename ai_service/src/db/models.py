from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from src.db.database import Base


class News(Base):
    """Haber veritabanı tablosu.
    
    Bu model sadece okuma amaçlı olarak tasarlanmıştır. Spring Boot tarafından yönetilen
    news tablosundan veri okuma için kullanılır.
    """
    __tablename__ = "news"
    
    id = Column(BigInteger, primary_key=True, index=True)
    url = Column(String, index=True)
    title = Column(String)
    source = Column(String)
    publication_date = Column(DateTime)
    fetched_at = Column(DateTime)
    
    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title[:20]}...', source='{self.source}')>"


class AnalyzedNewsLink(Base):
    """Analiz edilmiş haberlerin bağlantı tablosu.
    
    Bu model sadece filtreleme amaçlı olarak tasarlanmıştır. "İşlenmemiş" haberleri
    belirlemek için original_news_id alanı kullanılacaktır.
    """
    __tablename__ = "analyzed_news_links"
    
    id = Column(BigInteger, primary_key=True, index=True)
    original_news_id = Column(BigInteger, index=True)  # News.id'ye karşılık gelir
    
    def __repr__(self):
        return f"<AnalyzedNewsLink(id={self.id}, original_news_id={self.original_news_id})>"