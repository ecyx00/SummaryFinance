"""
story_tracker.py

Hikaye gruplarının sürekliliğini tespit eden ve yöneten sınıfı içerir.
Bu modül, yeni bir hikaye grubunun, veritabanındaki geçmiş aktif hikayelerden 
birinin devamı olup olmadığını tespit eder ve sonucu story_relationships 
tablosuna kaydeder.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import google.generativeai as genai
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.paths import get_prompt_path
from src.db.persistence_manager import PersistenceManager
from src.llm.parser import LLMOutputParser

# Logging yapılandırması
logger = logging.getLogger(__name__)

# LLM yanıtı için Pydantic model
from pydantic import BaseModel, Field, field_validator


class ContinuityResponse(BaseModel):
    """LLM'den dönen süreklilik yanıtı için Pydantic model."""
    is_continuation: bool = Field(..., description="Yeni hikayenin eski bir hikayenin devamı olup olmadığı")
    parent_story_id: Optional[int] = Field(None, description="Eğer devamsa, ebeveyn hikaye ID'si")
    
    @field_validator("parent_story_id")
    def validate_parent_story_id(cls, v: Optional[int], info: Any) -> Optional[int]:
        """parent_story_id, is_continuation=true ise gereklidir."""
        values = info.data
        if values.get("is_continuation", False) and v is None:
            raise ValueError("is_continuation=true iken parent_story_id gereklidir")
        return v


class StoryTracker:
    """
    Hikaye gruplarının sürekliliğini tespit eden ve yöneten sınıf.
    
    Bu sınıf, yeni bir hikaye grubunun geçmiş aktif hikayelerden birinin devamı olup 
    olmadığını tespit eder ve ilişkileri yönetir.
    """
    
    def __init__(self, persistence_manager: PersistenceManager):
        """
        StoryTracker sınıfının başlatıcısı.
        
        Args:
            persistence_manager: Veritabanı işlemleri için PersistenceManager örneği
        """
        if persistence_manager is None:
            raise ValueError("PersistenceManager zorunlu bir parametredir ve None olamaz")
            
        # PersistenceManager'ı kaydet
        self.persistence_manager = persistence_manager
        
        # API anahtarını ayarla ve Gemini modelini oluştur
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
        
        # Süreklilik prompt şablonunu yükle
        continuity_prompt_path = get_prompt_path("continuity", "v1.0")
        
        try:
            with open(continuity_prompt_path, "r", encoding="utf-8") as f:
                self.continuity_prompt_template = f.read()
            logger.info(f"Süreklilik prompt şablonu yüklendi: {continuity_prompt_path}")
        except Exception as e:
            logger.error(f"Süreklilik prompt şablonu yüklenirken hata: {e}")
            self.continuity_prompt_template = "# HATA: Süreklilik prompt şablonu yüklenemedi"
            
    def _calculate_representative_vector(self, news_ids: List[int]) -> Optional[np.ndarray]:
        """
        Haber ID'leri için temsilci vektör hesaplar.
        
        Verilen haber ID'leri için veritabanından embedding'leri çeker ve
        ortalamasını alarak tek bir temsilci vektör oluşturur.
        
        Args:
            news_ids: Temsil edilecek haberlerin ID listesi
            
        Returns:
            numpy.ndarray: Hesaplanan temsilci vektör veya None (hata durumunda)
        """
        try:
            if not news_ids or len(news_ids) < 2:
                logger.warning(f"Temsilci vektör hesaplamak için yetersiz haber sayısı: {len(news_ids) if news_ids else 0}")
                return None
                
            # Tüm haberleri tek bir sorguda çek
            news_details = self.persistence_manager.fetch_news_by_ids(news_ids)
            
            # Embedding'leri topla
            embeddings = []
            for news in news_details:
                if news.get("embedding_vector") is not None:
                    # PostgreSQL'den gelen vektörü numpy dizisine dönüştür
                    embedding = np.array(news["embedding_vector"])
                    embeddings.append(embedding)
            
            if not embeddings:
                logger.warning("Hiçbir haber için embedding bulunamadı")
                return None
                
            # Ortalama vektörü hesapla
            rep_vector = np.mean(embeddings, axis=0)
            logger.info(f"Temsilci vektör hesaplandı, boyut: {rep_vector.shape}")
            return rep_vector
            
        except Exception as e:
            logger.error(f"Temsilci vektör hesaplama hatası: {e}")
            return None
            
    def _find_candidate_past_stories(self, rep_vector: np.ndarray, k: int = 3) -> List[Dict]:
        """
        Temsilci vektörü kullanarak veritabanında benzer geçmiş hikayeleri arar.
        
        Args:
            rep_vector: Aranacak temsilci vektör
            k: Dönülecek en yakın hikaye sayısı (varsayılan: 3)
            
        Returns:
            List[Dict]: En yakın k aday hikaye bilgilerini içeren liste
        """
        conn = None
        try:
            # Son 14 günü hesapla
            cutoff_date = datetime.now() - timedelta(days=14)
            cutoff_date_str = cutoff_date.isoformat()
            
            # pgvector kullanarak ANN araması yap
            query = """
            SELECT id, story_essence_text, story_context_snippets, 
                   story_embedding_vector <-> %s AS distance
            FROM analyzed_stories
            WHERE is_active = true 
              AND last_update_date >= %s
            ORDER BY distance
            LIMIT %s
            """
            
            # Bağlantı havuzundan bir bağlantı al
            conn = self.persistence_manager.conn_pool.getconn()
            
            with conn.cursor() as cur:
                # pgvector.psycopg2, NumPy dizilerini doğrudan kabul ettiği için dönüştürme yapmadan kullan
                cur.execute(query, (rep_vector, cutoff_date_str, k))
                results = cur.fetchall()
                
                # Sonuçları dict olarak formatla
                candidates = []
                for result in results:
                    candidates.append({
                        "story_id": result[0],
                        "story_essence_text": result[1],
                        "story_context_snippets": result[2],
                        "distance": result[3]
                    })
                    
                logger.info(f"{len(candidates)} aday hikaye bulundu")
                return candidates
                
        except Exception as e:
            logger.error(f"Aday geçmiş hikayeleri arama hatası: {e}")
            return []
            
        finally:
            # Bağlantıyı her durumda havuza geri ver
            if conn:
                self.persistence_manager.conn_pool.putconn(conn)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _check_story_continuity(self, new_story: Dict, candidate_stories: List[Dict]) -> Optional[ContinuityResponse]:
        """
        Yeni hikayenin aday geçmiş hikayelerden birinin devamı olup olmadığını kontrol eder.
        
        Args:
            new_story: Yeni hikaye verisi (label ve rationale içermeli)
            candidate_stories: Aday geçmiş hikaye bilgileri listesi
            
        Returns:
            Optional[ContinuityResponse]: Süreklilik yanıtı veya None (hata durumunda)
        """
        try:
            if not candidate_stories:
                logger.info("Karşılaştırılacak aday hikaye yok, süreklilik kontrolü atlanıyor")
                return ContinuityResponse(is_continuation=False, parent_story_id=None)
                
            # Aday hikayeleri formatla
            formatted_candidates = []
            for i, candidate in enumerate(candidate_stories):
                candidate_text = f"""
Hikaye {i+1}:
- ID: {candidate['story_id']}
- Özet: {candidate['story_essence_text'] or 'Özet yok'}
- Bağlam Parçaları: {', '.join(candidate['story_context_snippets'] or ['Bağlam yok'])}
"""
                formatted_candidates.append(candidate_text)
                
            candidates_text = "\n".join(formatted_candidates)
            
            # Prompt'u doldur
            filled_prompt = self.continuity_prompt_template.format(
                new_story_label=new_story["label"],
                new_story_rationale=new_story["rationale"],
                candidate_stories=candidates_text
            )
            
            # Gemini API'sine istek gönder
            response = self.model.generate_content(filled_prompt)
            response_text = response.text
            
            # Yanıtı parse et
            validated_response = LLMOutputParser.parse_model_response(response_text, ContinuityResponse)
            
            if validated_response:
                logger.info(f"Süreklilik kontrolü tamamlandı: is_continuation={validated_response.is_continuation}")
                return validated_response
            else:
                logger.error("Süreklilik yanıtı işlenemedi")
                return None
                
        except Exception as e:
            logger.error(f"Süreklilik kontrolü hatası: {e}")
            return None
    
    def track_story(self, new_story_cluster: Dict, representative_vector: Optional[np.ndarray] = None) -> Optional[int]:
        """
        Yeni bir hikaye kümesinin sürekliliğini tespit eder ve eğer bir bağlantı bulunursa
        ebeveyn hikaye ID'sini döndürür.
        
        Args:
            new_story_cluster: Yeni, doğrulanmış ve zenginleştirilmiş hikaye kümesi
                { "news_ids": [...], "label": "...", "rationale": "..." }
            representative_vector: Önceden hesaplanmış temsil vektörü (opsiyonel)
                Belirtilmezse, fonksiyon kendi hesaplar
                
        Returns:
            Optional[int]: Ebeveyn hikaye ID'si veya None (bağlantı yoksa)
        """
        try:
            # Gerekli alanları kontrol et
            if not new_story_cluster.get("news_ids") or not new_story_cluster.get("label") or not new_story_cluster.get("rationale"):
                logger.error("Geçersiz hikaye kümesi formatı: news_ids, label ve rationale gerekli")
                return None
                
            # 1. Temsilci vektörü kullan veya hesapla
            rep_vector = representative_vector
            if rep_vector is None:
                # Önceden hesaplanmış vektör yoksa yeni hesapla
                rep_vector = self._calculate_representative_vector(new_story_cluster["news_ids"])
                
            if rep_vector is None:
                logger.error("Temsilci vektör hesaplanamadı veya sağlanmadı")
                return None
                
            # 2. Aday geçmiş hikayeleri bul
            candidate_stories = self._find_candidate_past_stories(rep_vector)
            
            # 3. Süreklilik kontrolü yap
            continuity_response = self._check_story_continuity(new_story_cluster, candidate_stories)
            if not continuity_response:
                logger.error("Süreklilik kontrolü yapılamadı")
                return None
                
            # 4. Süreklilik yoksa sonlandır
            if not continuity_response.is_continuation:
                logger.info("Yeni hikaye, önceki hikayelerin devamı değil")
                return None
                
            # 5. Ebeveyn hikaye ID'sini al ve döndür
            parent_story_id = continuity_response.parent_story_id
            
            # Ebeveyn hikaye ID'sinin geçerliliğini doğrula
            if not parent_story_id or parent_story_id <= 0:
                logger.error(f"Geçersiz ebeveyn hikaye ID'si: {parent_story_id}")
                return None
                
            logger.info(f"Hikaye sürekliliği tespit edildi: parent_story_id={parent_story_id}")
            return parent_story_id
                    
        except Exception as e:
            logger.error(f"Hikaye takibi hatası: {e}")
            return None
