from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.core.config import settings

# SQLAlchemy bağlantı engine'i oluştur
engine = create_engine(settings.DATABASE_URL)  # şu anda DATABASE_URL kullanıyoruz, SQLALCHEMY_DATABASE_URI de kullanılabilir

# Session oluşturucu (factory)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM modellerinin miras alacağı temel sınıf
Base = declarative_base()

# Veritabanı bağlantısı için yardımcı fonksiyon
def get_db():
    """Her istek için yeni bir DB oturumu oluşturur ve işlem sonunda kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
