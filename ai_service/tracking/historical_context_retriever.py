"""
historical_context_retriever.py

Veritabanındaki anlamsal olarak benzer geçmiş hikayeleri bulmak için kullanılan sınıfı içerir.
Bu modül, pgvector kullanarak veritabanındaki analyzed_stories tablosunda ANN (Yaklaşık En Yakın Komşu) 
araması yaparak, yeni bir hikaye vektörüne en benzer geçmiş hikayeleri bulur.
"""

import logging
from typing import Dict, List, Optional

import numpy as np

from src.db.persistence_manager import PersistenceManager

# Logging yapılandırması
logger = logging.getLogger(__name__)


class HistoricalContextRetriever:
    """
    Veritabanında anlamsal olarak benzer geçmiş hikayeleri bulan sınıf.
    
    Bu sınıf, pgvector kullanarak veritabanındaki analyzed_stories tablosunda
    kosinüs mesafesine dayalı bir arama yaparak, yeni bir hikaye vektörüne
    en benzer geçmiş hikayeleri bulur.
    """
    
    def __init__(self, persistence_manager: PersistenceManager):
        """
        HistoricalContextRetriever sınıfının başlatıcısı.
        
        Args:
            persistence_manager: Veritabanı işlemleri için PersistenceManager örneği
        """
        if persistence_manager is None:
            raise ValueError("PersistenceManager zorunlu bir parametredir ve None olamaz")
            
        self.persistence_manager = persistence_manager
        logger.info("HistoricalContextRetriever başlatıldı")
        
    def retrieve_similar_stories(self, vector: np.ndarray, k: int = 3) -> List[Dict]:
        """
        Verilen vektöre en benzer k adet hikayeyi veritabanından getirir.
        
        Args:
            vector: Sorgulanacak hikaye vektörü
            k: Dönülecek maksimum benzer hikaye sayısı
            
        Returns:
            List[Dict]: En benzer hikayelerin detaylarını içeren liste
        """
        try:
            # PersistenceManager ile benzer hikayeleri getir
            similar_stories = self.persistence_manager.fetch_similar_stories_by_vector(vector, k)
            
            if not similar_stories:
                logger.info(f"Benzer hikaye bulunamadı")
                return []
                
            logger.info(f"{len(similar_stories)} benzer hikaye bulundu")
            return similar_stories
            
        except Exception as e:
            logger.error(f"Benzer hikaye arama hatası: {e}")
            return []
