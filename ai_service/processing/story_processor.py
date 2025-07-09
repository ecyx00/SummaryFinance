"""
Story Processor Module

Bu modül, haber hikayelerinin analiz özetlerinden hafıza bileşenleri çıkarılması için
gereken sınıfları ve fonksiyonları içerir.
"""

import os
import json
import numpy as np
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from sentence_transformers import SentenceTransformer

from ..core.config import settings
from ..utils.prompt_helper import get_prompt_path

# Logger yapılandırması
logger = logging.getLogger(__name__)

# Pydantic model for validating LLM response
class MemoryComponents(BaseModel):
    """LLM'den alınan hafıza bileşenlerini doğrulamak için Pydantic modeli."""
    rolling_summary: str = Field(..., description="Hikayenin sürekli özeti")
    story_essence: str = Field(..., description="Hikayenin özü")
    context_snippets: List[str] = Field(..., description="Bağlam parçaları")
    
    @validator("rolling_summary")
    def validate_rolling_summary_length(cls, v):
        words = v.split()
        if len(words) > 100:
            logger.warning(f"Sürekli özet 100 kelimeyi aşıyor ({len(words)} kelime). Kırpılacak.")
            return " ".join(words[:100])
        return v
    
    @validator("context_snippets")
    def validate_context_snippets(cls, v):
        if len(v) < 3:
            logger.warning(f"Bağlam parçaları sayısı 3'ten az: {len(v)}. İsteğe uygun değil.")
        elif len(v) > 5:
            logger.warning(f"Bağlam parçaları sayısı 5'ten fazla: {len(v)}. İlk 5 parça alınacak.")
            return v[:5]
        return v


class StoryProcessor:
    """
    Haber hikayelerinden hafıza bileşenleri (özet, öz, bağlam parçaları, gömme vektörü)
    oluşturan sınıf.
    
    Bu sınıf, bir hikaye analiz özetini alır ve ondan kalıcı hafıza bileşenleri üretir:
    - story_essence_text: Hikayenin özü (1-2 cümle)
    - story_context_snippets: Anahtar bağlam parçaları (3-5 madde)
    - story_embedding_vector: Hikaye özünden üretilen gömme vektörü
    """
    
    def __init__(self):
        """
        StoryProcessor sınıfını başlatır ve gereken modelleri yükler.
        """
        try:
            # Gemini modeli için API anahtarını ayarla
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Gemini modelini yapılandır
            self.gemini_model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL_NAME
            )
            logger.info(f"Gemini modeli başlatıldı: {settings.GEMINI_MODEL_NAME}")
            
            # Sentence-transformers modelini yükle
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence transformer modeli başlatıldı: all-MiniLM-L6-v2")
            
            # Prompt şablonunu yükle
            self.memory_prompt_template = Path(get_prompt_path("memory_generation/v1.0.txt")).read_text(encoding="utf-8")
            logger.info("Hafıza üretimi prompt şablonu yüklendi")
            
        except Exception as e:
            logger.error(f"StoryProcessor başlatılırken hata: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _generate_memory_components(self, analysis_summary: str) -> Optional[Dict]:
        """
        Hikaye analiz özetinden metin bazlı hafıza bileşenlerini üretir.
        
        Args:
            analysis_summary: Haber hikayesinin detaylı analiz özeti
            
        Returns:
            Optional[Dict]: Hafıza bileşenlerini içeren sözlük veya None (hata durumunda)
        """
        try:
            # Prompt şablonunu doldur
            prompt = self.memory_prompt_template.format(
                analysis_summary=analysis_summary
            )
            
            # Gemini'ye istek gönder
            logger.info("Hafıza bileşenleri üretimi için LLM isteği gönderiliyor...")
            response = self.gemini_model.generate_content(prompt)
            
            # Yanıtı işle
            if not response.text:
                logger.error("LLM boş yanıt döndü")
                return None
            
            # JSON yanıtı ayıkla
            response_text = response.text
            
            # Yanıt bir JSON bloğu içeriyorsa (``` ile sarılıysa), sadece JSON kısmını al
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # JSON'ı parse et
            try:
                memory_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"LLM yanıtı geçerli JSON formatında değil: {e}")
                logger.debug(f"Alınan yanıt: {response_text}")
                return None
            
            # Pydantic modeli ile doğrula
            memory_components = MemoryComponents(**memory_data)
            
            logger.info("Hafıza bileşenleri başarıyla üretildi")
            return {
                "rolling_summary": memory_components.rolling_summary,
                "story_essence": memory_components.story_essence,
                "context_snippets": memory_components.context_snippets
            }
            
        except Exception as e:
            logger.error(f"Hafıza bileşenleri üretilirken hata: {e}")
            return None
    
    def _create_story_embedding(self, story_essence_text: str) -> Optional[np.ndarray]:
        """
        Hikaye özü metninden bir gömme vektörü üretir.
        
        Args:
            story_essence_text: Hikayenin özünü içeren kısa metin
            
        Returns:
            Optional[np.ndarray]: Gömme vektörü veya None (hata durumunda)
        """
        try:
            logger.info("Hikaye özü için gömme vektörü üretiliyor...")
            # Sentence-transformers ile gömme vektörü oluştur
            embedding_vector = self.embedding_model.encode(story_essence_text)
            
            logger.info(f"Gömme vektörü üretildi: boyut={embedding_vector.shape}")
            return embedding_vector
            
        except Exception as e:
            logger.error(f"Gömme vektörü oluşturulurken hata: {e}")
            return None
    
    def process_story_for_memory(self, analysis_summary: str) -> Optional[Dict[str, Any]]:
        """
        Hikaye analiz özetinden tüm hafıza bileşenlerini (metin ve vektör) üretir.
        
        Args:
            analysis_summary: Haber hikayesinin detaylı analiz özeti
            
        Returns:
            Optional[Dict]: Tüm hafıza bileşenlerini içeren sözlük:
                - story_essence_text: Hikayenin özü
                - story_context_snippets: Bağlam parçaları listesi
                - story_embedding_vector: Gömme vektörü
        """
        try:
            # Metin bazlı hafıza bileşenlerini üret
            memory_components = self._generate_memory_components(analysis_summary)
            if not memory_components:
                logger.error("Hafıza bileşenleri üretilemedi")
                return None
            
            # Gömme vektörünü oluştur
            story_essence_text = memory_components["story_essence"]
            embedding_vector = self._create_story_embedding(story_essence_text)
            
            if embedding_vector is None:
                logger.error("Hikaye gömme vektörü oluşturulamadı")
                return None
            
            # Tüm bileşenleri bir araya getir
            result = {
                "story_essence_text": story_essence_text,
                "story_context_snippets": memory_components["context_snippets"],
                "story_embedding_vector": embedding_vector.tolist()  # NumPy dizisini JSON'a uygun liste formatına dönüştür
            }
            
            logger.info("Hikaye işleme tamamlandı, tüm hafıza bileşenleri üretildi")
            return result
            
        except Exception as e:
            logger.error(f"Hikaye işlenirken hata: {e}")
            return None
