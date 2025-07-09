#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
StoryEnricher Module

Bu modül, LLMValidator tarafından onaylanmış haber kümelerini zenginleştirmek için
etiket (label) ve gerekçe (rationale) bilgilerini üreten StoryEnricher sınıfını içerir.
"""

import logging
from typing import Dict, List, Optional
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, Field, validator

from ..core.config import settings
from ..core.paths import get_prompt_path
from ..db.persistence_manager import PersistenceManager
from .parser import LLMOutputParser

logger = logging.getLogger(__name__)


# Pydantic Validation Models
class LabelResponse(BaseModel):
    """Etiketleme LLM yanıtı için model."""
    label: str = Field(..., description="Haber grubunun kısa etiketi (4-8 kelime)")
    
    @validator('label')
    def validate_label(cls, v):
        """Label alanını doğrula."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Etiket boş olamaz")
        return v


class RationaleResponse(BaseModel):
    """Gerekçe LLM yanıtı için model."""
    rationale: str = Field(..., description="Haber grubunun bağlantı gerekçesi")
    
    @validator('rationale')
    def validate_rationale(cls, v):
        """Rationale alanını doğrula."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Gerekçe boş olamaz")
        return v
    
class StoryEnricher:
    """
    LLMValidator tarafından onaylanmış haber kümelerini zenginleştiren sınıf.
    
    Her bir haber kümesi için iki ayrı LLM çağrısı yapar:
    1. Haber grubuna kısa bir etiket (label) üretir
    2. Haber grubunun neden bağlantılı olduğuna dair bir gerekçe (rationale) üretir
    """
    
    def __init__(self, persistence_manager: PersistenceManager):
        """
        StoryEnricher sınıfının başlatıcısı.
        
        Args:
            persistence_manager: Veritabanından haber verilerini çekmek için kullanılacak PersistenceManager örneği
        """
        if persistence_manager is None:
            raise ValueError("PersistenceManager zorunlu bir parametredir ve None olamaz")
            
        # API anahtarını ayarla ve Gemini modeli oluştur
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
        
        # PersistenceManager'ı kaydet
        self.persistence_manager = persistence_manager
        
        # Prompt şablonlarını yükle (paths yardımcı modülü ile)
        labeling_prompt_path = get_prompt_path("labeling", "v1.0")
        
        try:
            with open(labeling_prompt_path, "r", encoding="utf-8") as f:
                self.labeling_prompt_template = f.read()
            logger.info(f"Etiketleme prompt şablonu yüklendi: {labeling_prompt_path}")
        except Exception as e:
            logger.error(f"Etiketleme prompt şablonu yüklenirken hata: {e}")
            self.labeling_prompt_template = "# HATA: Etiketleme prompt şablonu yüklenemedi"
            
        # Gerekçelendirme prompt şablonunu yükle
        justification_prompt_path = get_prompt_path("justification", "v1.0")
        
        try:
            with open(justification_prompt_path, "r", encoding="utf-8") as f:
                self.justification_prompt_template = f.read()
            logger.info(f"Gerekçelendirme prompt şablonu yüklendi: {justification_prompt_path}")
        except Exception as e:
            logger.error(f"Gerekçelendirme prompt şablonu yüklenirken hata: {e}")
            self.justification_prompt_template = "# HATA: Gerekçelendirme prompt şablonu yüklenemedi"
    
    def _prepare_headlines_text(self, news_items: List[Dict]) -> str:
        """
        Haber başlıklarını birleştirip formatlı metin oluşturur.
        
        Args:
            news_items: Haberlerin detaylarını içeren liste
            
        Returns:
            Formatlı başlık listesi metni
        """
        headlines = []
        for news in news_items:
            headlines.append(f"- {news.get('title', 'Başlık yok')} ({news.get('id', 'ID yok')})")
        
        return "\n".join(headlines)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _generate_label(self, headlines_text: str) -> Optional[str]:
        """
        Haber başlıklarını kullanarak bir etiket üretir.
        
        Args:
            headlines_text: Formatlı haber başlıkları metni
            
        Returns:
            Üretilen etiket veya None (hata durumunda)
        """
        try:
            # Prompt'u doldur
            filled_prompt = self.labeling_prompt_template.format(headlines=headlines_text)
            
            # Gemini API'sine istek gönder
            response = self.model.generate_content(filled_prompt)
            response_text = response.text
            
            # Yanıtı parse et - ortak parser modülünü kullan
            validated_response = LLMOutputParser.parse_model_response(response_text, LabelResponse)
            
            if validated_response:
                logger.info(f"Etiket üretildi: \"{validated_response.label}\"")
                return validated_response.label
            else:
                logger.error("Etiket üretilemedi")
                return None
                
        except Exception as e:
            logger.error(f"Etiket üretirken hata: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _generate_rationale(self, headlines_text: str, label: str) -> Optional[str]:
        """
        Haber başlıkları ve etiketi kullanarak bir gerekçe üretir.
        
        Args:
            headlines_text: Formatlı haber başlıkları metni
            label: Önceden üretilmiş etiket
            
        Returns:
            Üretilen gerekçe veya None (hata durumunda)
        """
        try:
            # Prompt'u doldur
            filled_prompt = self.justification_prompt_template.format(
                headlines=headlines_text,
                label=label
            )
            
            # Gemini API'sine istek gönder
            response = self.model.generate_content(filled_prompt)
            response_text = response.text
            
            # Yanıtı parse et - ortak parser modülünü kullan
            validated_response = LLMOutputParser.parse_model_response(response_text, RationaleResponse)
            
            if validated_response:
                logger.info(f"Gerekçe üretildi: \"{validated_response.rationale}\"")
                return validated_response.rationale
            else:
                logger.error("Gerekçe üretilemedi")
                return None
                
        except Exception as e:
            logger.error(f"Gerekçe üretirken hata: {e}")
            return None
    
    def enrich_story_cluster(self, news_ids: List[int]) -> Optional[Dict]:
        """
        Bir haber kümesini etiket ve gerekçe ile zenginleştirir.
        
        Args:
            news_ids: Zenginleştirilecek haber ID'leri listesi
            
        Returns:
            Optional[Dict]: Zenginleştirilmiş haber kümesi veya None (hata durumunda)
        """
        try:
            if not news_ids or len(news_ids) < 2:
                logger.warning(f"Zenginleştirme için yetersiz haber sayısı: {len(news_ids) if news_ids else 0}")
                return None
                
            # Veritabanından tüm haber detaylarını tek bir sorguda çek
            news_details = self.persistence_manager.fetch_news_by_ids(news_ids)
            
            # En az 2 haber detayı olup olmadığını kontrol et
            if len(news_details) < 2:
                logger.warning(f"Veritabanından yeterli haber detayı çekilemedi. Bulunan: {len(news_details)}")
                return None
                
            # Başlıkları formatlı metne dönüştür
            headlines_text = self._prepare_headlines_text(news_details)
            
            # 1. Adım: Etiket üret
            label = self._generate_label(headlines_text)
            if not label:
                return None
                
            # 2. Adım: Gerekçe üret
            rationale = self._generate_rationale(headlines_text, label)
            if not rationale:
                return None
                
            # Zenginleştirilmiş kümeyi döndür
            enriched_cluster = {
                "news_ids": news_ids,
                "label": label,
                "rationale": rationale
            }
            
            logger.info(f"Haber kümesi zenginleştirildi: {len(news_ids)} haber, etiket=\"{label}\"")
            return enriched_cluster
            
        except Exception as e:
            logger.error(f"Haber kümesi zenginleştirme hatası: {e}")
            return None
