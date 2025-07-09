#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLMValidator Module

Bu modül, GraphClusterer tarafından oluşturulan aday kümelerin kalitesini değerlendirmek için
LLM (Language Learning Model) kullanan bir validator sınıfı içerir.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any, Union, Literal
from datetime import date
from pathlib import Path
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, Field, validator

from ..core.config import settings
from ..db.persistence_manager import PersistenceManager

logger = logging.getLogger(__name__)

# Pydantic Validation Models
class ClusterValidationSuccess(BaseModel):
    """LLM cluster validation'ın başarılı sonucu için model."""
    is_story: bool = Field(..., description="Haberlerin aynı hikayeye ait olup olmadığı")
    signal_strength: Literal["strong", "medium", "weak"] = Field(..., description="Hikaye bağlantısının gücü")
    confidence_score: float = Field(..., description="LLM'in değerlendirmesine olan güveni (0-1)", ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Değerlendirmenin kısa gerekçesi")
    
    @validator('is_story')
    def validate_is_story(cls, v):
        """is_story alanı mutlaka True olmalıdır"""
        if not v:
            raise ValueError("Bu model için is_story değeri her zaman True olmalıdır")
        return v

class ClusterValidationFailure(BaseModel):
    """LLM cluster validation'ın başarısız sonucu için model."""
    is_story: bool = Field(..., description="Haberlerin aynı hikayeye ait olup olmadığı")
    reasoning: Optional[str] = Field(None, description="Değerlendirmenin kısa gerekçesi")
    
    @validator('is_story')
    def validate_is_story(cls, v):
        """is_story alanı mutlaka False olmalıdır"""
        if v:
            raise ValueError("Bu model için is_story değeri her zaman False olmalıdır")
        return v

class ValidationResult(BaseModel):
    """Tüm validasyon sonuçları için birleşik model."""
    __root__: Union[ClusterValidationSuccess, ClusterValidationFailure]

class LLMOutputParser:
    """LLM çıktısını güvenli bir şekilde işleyip yapılandırılmış veri formatına dönüştüren sınıf."""
    
    @staticmethod
    def extract_json_from_response(text: str) -> Optional[str]:
        """LLM yanıtından JSON formatındaki metni çıkarır."""
        try:
            # JSON bloğunu bulmak için başlangıç ve bitiş etiketlerini ara
            start_index = text.find('{')
            end_index = text.rfind('}') + 1
            
            if start_index == -1 or end_index == 0:
                logger.warning("LLM yanıtında JSON formatında veri bulunamadı.")
                return None
            
            json_text = text[start_index:end_index]
            return json_text
        except Exception as e:
            logger.error(f"JSON çıkarma hatası: {e}")
            return None
    
    @staticmethod
    def parse_validation_response(response_text: str) -> Optional[Dict[str, Any]]:
        """
        LLM'den gelen metni Pydantic model kullanarak JSON nesnesine dönüştürür ve doğrular.
        
        Args:
            response_text: LLM'den gelen yanıt metni
            
        Returns:
            Doğrulanmış ve yapılandırılmış JSON nesnesi veya None (hata durumunda)
        """
        try:
            json_text = LLMOutputParser.extract_json_from_response(response_text)
            if not json_text:
                return None
                
            # JSON'ı parse et
            raw_result = json.loads(json_text)
            
            # "is_story" alanının varlığını kontrol et
            if "is_story" not in raw_result:
                logger.error("JSON yanıtında 'is_story' alanı yok")
                return None
            
            # is_story değerine göre uygun modeli seç
            try:
                if raw_result["is_story"] is True:
                    # Başarılı validasyon için model
                    result = ClusterValidationSuccess(**raw_result).dict()
                    logger.info(f"Başarılı küme doğrulaması: {result['signal_strength']} (confidence: {result['confidence_score']})")
                else:
                    # Başarısız validasyon için model
                    result = ClusterValidationFailure(**raw_result).dict()
                    logger.info("Küme geçerli bir hikaye olarak değerlendirilmedi.")
                
                return result
            except ValueError as ve:
                logger.error(f"Model doğrulama hatası: {ve}")
                
                # Eksik alanı olmayan basit bir sonuç oluştur
                if raw_result["is_story"] is True and not all(field in raw_result for field in ["signal_strength", "confidence_score", "reasoning"]):
                    logger.warning("'is_story': true için gerekli tüm alanlar bulunamadı, varsayılan değerler kullanılıyor")
                    return {
                        "is_story": True,
                        "signal_strength": raw_result.get("signal_strength", "medium"),
                        "confidence_score": raw_result.get("confidence_score", 0.5),
                        "reasoning": raw_result.get("reasoning", "Gerekçe belirtilmemiş")
                    }
                elif raw_result["is_story"] is False:
                    return {"is_story": False, "reasoning": raw_result.get("reasoning", None)}
                
                return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Yanıt işleme hatası: {e}")
            return None


class LLMValidator:
    """
    Aday haber kümelerini LLM kullanarak doğrulayan sınıf.
    
    Bu sınıf, GraphClusterer tarafından oluşturulan aday kümeleri değerlendirmek için
    Gemini API'sini kullanır ve kümenin gerçek bir haber hikayesine ait olup olmadığını belirler.
    """
    
    def __init__(self, persistence_manager: PersistenceManager):
        """
        LLMValidator sınıfının başlatıcısı.
        
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
        
        # Prompt şablonunu yükle - Path kullanarak daha güvenli yol hesaplama
        # Proje ana dizinini bul
        project_root = Path(__file__).parent.parent.parent.parent
        prompt_path = project_root / "prompts" / "validation" / "v1.1.txt"
        
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.prompt_template = f.read()
            logger.info(f"Prompt şablonu yüklendi: {prompt_path}")
        except Exception as e:
            logger.error(f"Prompt şablonu yüklenirken hata: {e}")
            self.prompt_template = "# HATA: Prompt şablonu yüklenemedi"
    
    def _prepare_input(self, news_cluster: List[Dict]) -> Dict:
        """
        Bir haber kümesi için LLM girdisini hazırlar.
        
        Args:
            news_cluster: Değerlendirilecek haber kümeleri listesi (veritabanından çekilmiş)
            
        Returns:
            Dict: LLM prompt'unda kullanılacak formatlanmış veri
        """
        # Başlıkları topla
        headlines = []
        all_entities = []
        
        for news in news_cluster:
            headlines.append(f"- {news.get('title', 'Başlık yok')} ({news.get('id', 'ID yok')})")
            
            # Varlıkları topla
            entities = news.get("entities", [])
            if entities:
                all_entities.extend([entity.get("text", "") for entity in entities])
        
        # En sık geçen ortak varlıkları bul
        entity_counts = {}
        for entity in all_entities:
            if entity.strip():
                entity_counts[entity] = entity_counts.get(entity, 0) + 1
        
        # En az 2 haberde geçen varlıkları seç
        shared_entities = [entity for entity, count in entity_counts.items() if count >= 2]
        
        # Sonuç sözlüğünü oluştur
        result = {
            "headlines": "\n".join(headlines),
            "shared_entities": "- " + "\n- ".join(shared_entities) if shared_entities else "Ortak varlık bulunamadı."
        }
        
        return result
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def validate_cluster(self, news_ids: List[int]) -> Optional[Dict]:
        """
        Bir haber kümesini LLM kullanarak doğrular.
        
        Args:
            news_ids: Değerlendirilecek haber ID'leri listesi
            
        Returns:
            Optional[Dict]: LLM'in değerlendirme sonucu veya None (hata durumunda)
        """
        try:
            if not news_ids or len(news_ids) < 2:
                logger.warning(f"Doğrulama için yetersiz haber sayısı: {len(news_ids) if news_ids else 0}")
                return None
                
            # Veritabanından haber detaylarını çek
            news_details = []
            for news_id in news_ids:
                try:
                    # PersistenceManager'dan haber detaylarını al
                    news_detail = self.persistence_manager.fetch_news_by_id(news_id)
                    if news_detail:
                        # Haberin varlıklarını çek
                        entities = self.persistence_manager.fetch_entities_by_news_id(news_id)
                        if entities:
                            news_detail["entities"] = entities
                        news_details.append(news_detail)
                except Exception as fetch_error:
                    logger.error(f"Haber detayları çekilirken hata (ID={news_id}): {fetch_error}")
            
            # En az 2 haber detayı olup olmadığını kontrol et
            if len(news_details) < 2:
                logger.warning(f"Veritabanından yeterli haber detayı çekilemedi. Bulunan: {len(news_details)}")
                return None
                
            # Girdiyi hazırla
            input_data = self._prepare_input(news_details)
            
            # Prompt'u doldur
            filled_prompt = self.prompt_template.format(
                headlines=input_data["headlines"],
                shared_entities=input_data["shared_entities"]
            )
            
            # Gemini API'sine istek gönder
            response = self.model.generate_content(filled_prompt)
            response_text = response.text
            
            # Yanıtı parse et
            result = LLMOutputParser.parse_validation_response(response_text)
            
            if result:
                logger.info(f"Küme doğrulama sonucu: is_story={result.get('is_story')}")
                if result.get("is_story"):
                    logger.info(f"Signal strength: {result.get('signal_strength')}, "
                                f"Confidence: {result.get('confidence_score')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Küme doğrulama hatası: {e}")
            return None
