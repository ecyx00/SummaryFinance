from pydantic_settings import BaseSettings
from typing import Optional


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
    NEWS_BATCH_SIZE: int
    LOG_LEVEL: str
    
    # External API Keys and URLs
    GEMINI_API_KEY: str
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