"""
Feature Extraction Module

Bu modül, haber URL'lerinden metin çıkarma, varlık tanıma ve metin gömme işlemlerini 
gerçekleştiren FeatureExtractor sınıfını içerir.
"""

from typing import Dict, Any, List, Optional, Union, Set, Tuple
import logging
import numpy as np
from newspaper import Article, Config as NewspaperConfig
import spacy
from sentence_transformers import SentenceTransformer
import torch
from ..core.config import settings

# Logger yapılandırması
logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Haber URL'lerinden metin ve özellik çıkaran sınıf.

    Bu sınıf, bir haber URL'sinden tam metin içeriğini çekmek, 
    metinden varlıkları (örn. kişiler, kurumlar, konumlar) tanımak ve
    metnin semantik vektör temsilini oluşturmak için kullanılır.
    """

    def __init__(self):
        """
        FeatureExtractor sınıfını başlat.
        
        Bu metod, spaCy ve SentenceTransformer modellerini yükler ve
        newspaper3k için yapılandırma oluşturur.
        """
        logger.info("FeatureExtractor başlatılıyor...")
        
        # newspaper3k için yapılandırma
        self.newspaper_config = NewspaperConfig()
        self.newspaper_config.fetch_images = False
        self.newspaper_config.memoize_articles = False
        self.newspaper_config.request_timeout = 10
        
        # spaCy NER modeli yükleme
        try:
            logger.info(f"spaCy modeli yükleniyor: {settings.SPACY_MODEL_NAME}")
            self.nlp = spacy.load(settings.SPACY_MODEL_NAME)
            logger.info("spaCy modeli başarıyla yüklendi")
        except Exception as e:
            logger.error(f"spaCy modeli yüklenirken hata: {e}")
            logger.error("Lütfen 'python -m spacy download en_core_web_sm' komutunu çalıştırın")
            self.nlp = None

        # Embedding modeli yükleme
        try:
            logger.info(f"Embedding modeli yükleniyor: {settings.EMBEDDING_MODEL_NAME}")
            self.embedder = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            # Cuda kullanılabilir mi kontrol et
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.embedder = self.embedder.to(self.device)
            logger.info(f"Embedding modeli başarıyla yüklendi (Cihaz: {self.device})")
        except Exception as e:
            logger.error(f"Embedding modeli yüklenirken hata: {e}")
            self.embedder = None

    def extract_features(self, news_item: Dict[str, Any], entity_types: Set[str] = None) -> Dict[str, Any]:
        """
        Haber öğesinden tüm özellikleri çıkarır.
        
        Args:
            news_item: İşlenecek haber öğesi (dictionary olarak)
                       En azından "id" ve "url" alanları olmalıdır
            entity_types: Filtrelenecek varlık tipleri kümesi, ör: {"ORG", "PERSON", "GPE"}
                         None verilirse tüm varlık tipleri alınır
        
        Returns:
            Zenginleştirilmiş haber bilgilerini içeren dictionary:
            {
                "id": int,
                "url": str,
                "full_text": str veya None,
                "entities": Dict[str, List[str]] veya None,
                "embedding_vector": List[float] veya None
            }
        """
        result = {
            "id": news_item.get("id"),
            "full_text": None,
            "entities": None,
            "embedding_vector": None
        }
        
        if not news_item.get("url"):
            logger.error(f"Haber ID {news_item.get('id')} için URL bulunamadı")
            return result
        
        # Adım 1: URL'den tam metni çıkar
        full_text = self._extract_text(news_item["url"])
        result["full_text"] = full_text
        
        # Metin başarıyla çıkarılamazsa, diğer özellikleri hesaplama
        if not full_text:
            logger.warning(f"Haber ID {news_item.get('id')} için metin çıkarılamadı, diğer özellikler atlanıyor")
            return result
            
        # Adım 2: Metinden varlıkları çıkar
        entities = self._extract_entities(full_text, entity_types)
        result["entities"] = entities
        
        # Adım 3: Metin gömmesini oluştur
        embedding_vector = self._create_embedding(full_text)
        if embedding_vector is not None:
            # NumPy dizisini normal liste olarak serileştir
            result["embedding_vector"] = embedding_vector.tolist()
        
        return result
        
    def _extract_text(self, url: str) -> Optional[str]:
        """
        URL'den tam metin içeriğini çıkarır.
        
        Args:
            url: İçerik çıkarılacak URL
            
        Returns:
            Tam metin içeriği veya None (hata durumunda)
        """
        try:
            logger.info(f"Metin çıkarılıyor: {url}")
            article = Article(url, config=self.newspaper_config)
            article.download()
            article.parse()
            
            if not article.text or len(article.text) < 100:
                logger.warning(f"URL'den yetersiz içerik çıkarıldı: {url}")
                return None
                
            return article.text
            
        except Exception as e:
            logger.error(f"URL'den metin çıkarırken hata ({url}): {e}")
            return None
            
    def _extract_entities(self, text: str, entity_types: Set[str] = None) -> Optional[Dict[str, List[str]]]:
        """
        Metinden isim varlıklarını (named entities) çıkarır.
        
        Args:
            text: İşlenecek metin
            entity_types: Filtrelenecek varlık tipleri kümesi, ör: {"ORG", "PERSON", "GPE"}
                         None verilirse tüm tipler alınır
            
        Returns:
            Varlık tipleri ve değerleri içeren sözlük veya None (hata durumunda)
        """
        if not self.nlp:
            logger.error("spaCy modeli yüklenmemiş, varlık tanıma atlanıyor")
            return None
            
        try:
            logger.info("Metinden varlıklar çıkarılıyor")
            doc = self.nlp(text)
            
            # Varlıkları türlerine göre gruplandır
            entities_by_type = {}
            for ent in doc.ents:
                # Eğer filtreleme yapılacaksa ve varlık tipi isteniyorsa ekle
                if entity_types is None or ent.label_ in entity_types:
                    if ent.label_ not in entities_by_type:
                        entities_by_type[ent.label_] = []
                    # Aynı değeri tekrar eklememek için kontrol et
                    if ent.text not in entities_by_type[ent.label_]:
                        # Çok kısa varlık adlarını filtrele (örn: 1-2 karakterlik)
                        if len(ent.text.strip()) > 2:
                            entities_by_type[ent.label_].append(ent.text)
                    
            return entities_by_type
            
        except Exception as e:
            logger.error(f"Varlık çıkarma işlemi sırasında hata: {e}")
            return None
            
    def _create_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Metin için gömme vektörü oluşturur.
        
        Args:
            text: Gömme vektörü oluşturulacak metin
            
        Returns:
            Metin gömme vektörü veya None (hata durumunda)
        """
        if not self.embedder:
            logger.error("Embedding modeli yüklenmemiş, gömme vektörü oluşturma atlanıyor")
            return None
            
        try:
            logger.info("Metin gömmesi oluşturuluyor")
            
            words = text.split()
            total_words = len(words)
            
            # Model maksimum token limitini aşan metinler için gelişmiş kesme stratejisi
            max_tokens = 512
            
            if total_words <= max_tokens:
                # Kısa metinler için tüm metni kullan
                truncated_text = text
            else:
                logger.info(f"Uzun metin için gelişmiş kesme uyguluyorum (Toplam kelime: {total_words})")
                
                # Baştan ve sondan eşit miktarda token alarak önemli bilgileri koru
                start_size = max_tokens // 2
                end_size = max_tokens - start_size
                
                start_text = " ".join(words[:start_size])
                end_text = " ".join(words[-end_size:])
                
                truncated_text = f"{start_text} [...] {end_text}"
                
                logger.info(f"Metin {total_words} kelimeden {max_tokens} kelimeye kısaltıldı")
            
            embedding = self.embedder.encode(truncated_text)
            return embedding
            
        except Exception as e:
            logger.error(f"Gömme vektörü oluşturma işlemi sırasında hata: {e}")
            return None
