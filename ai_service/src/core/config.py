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
    
    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL bağlantı URI'sini oluşturur."""
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Settings örneğini oluştur
settings = Settings() 