from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
from pydantic import model_validator

# Analiz sonuçları için standart yasal uyarı metni
DEFAULT_DISCLAIMER = "Bu içerik yapay zeka ile otomatik olarak üretilmiş olup, sağlanan haberlere dayanmaktadır ve genel bilgilendirme amaçlıdır. Yatırım tavsiyesi niteliği taşımaz."


class Settings(BaseSettings):
    """Uygulama ayarları.
    
    .env dosyasından ortam değişkenlerini okur.
    """
    # PostgreSQL Database Configuration
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    
    # Application Settings
    NEWS_BATCH_SIZE: Optional[int] = None
    LOG_LEVEL: str
    
    @model_validator(mode='before')
    @classmethod
    def validate_news_batch_size(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """String olan 'None' değerini gerçek None değerine dönüştür"""
        if isinstance(data, dict) and 'NEWS_BATCH_SIZE' in data:
            if data['NEWS_BATCH_SIZE'] == 'None':
                data['NEWS_BATCH_SIZE'] = None
        return data
    
    # External API Keys and URLs
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str = "" # Güvenli bir varsayılan
    SPRING_BOOT_SUBMIT_URL: str
    FMP_API_KEY: str  # Financial Modeling Prep API key for economic calendar data
    NEWSDATA_API_KEY: str  # NewsData.io API key for news fetching
    FINNHUB_API_KEY: str   # Finnhub API key for additional news sources
    
    # Feature Extraction Models
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    SPACY_MODEL_NAME: str = "en_core_web_sm"
    
    # Interaction Scorer Settings
    SEMANTIC_SIMILARITY_WEIGHT: float = 0.50
    ENTITY_SIMILARITY_WEIGHT: float = 0.30
    TEMPORAL_PROXIMITY_WEIGHT: float = 0.20
    TOP_K_NEAREST: int = 50  # Yakın komşu sayısı
    INTERACTION_THRESHOLD: float = 0.65  # Graf kenarları için eşik değer
    INTERACTION_SCORER_K_NEIGHBORS: int = 10
    
    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL bağlantı URI'sini oluşturur."""
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Settings örneğini oluştur
settings = Settings() 