#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM Parser Module

Bu modül, LLM yanıtlarını işlemek için gerekli ortak parser fonksiyonlarını ve
doğrulama modellerini içerir. LLMValidator ve StoryEnricher tarafından kullanılır.
"""

import json
import logging
from typing import Optional, Any, Dict, TypeVar, Type
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LLMOutputParser:
    """LLM çıktılarını güvenli bir şekilde işleyip yapılandırılmış veri formatına dönüştüren sınıf."""
    
    @staticmethod
    def extract_json_from_response(response_text: str) -> Optional[str]:
        """
        LLM yanıtından JSON kısmını çıkarır.
        
        Args:
            response_text: LLM'den gelen yanıt metni
            
        Returns:
            JSON metni veya None (bulunamazsa)
        """
        try:
            # JSON bloğunu bul (```json ve ``` arasındaki içerik)
            if "```json" in response_text:
                start_idx = response_text.find("```json") + len("```json")
                end_idx = response_text.find("```", start_idx)
                if start_idx > 0 and end_idx > start_idx:
                    return response_text[start_idx:end_idx].strip()
            
            # Direkt JSON içeriği olabilir
            if response_text.strip().startswith("{") and response_text.strip().endswith("}"):
                return response_text.strip()
                
            # JSON bloğunu bul (alternatif format: { ve } arasındaki içerik)
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}")
            if start_idx >= 0 and end_idx > start_idx:
                return response_text[start_idx:end_idx+1].strip()
                
            logger.warning("JSON içeriği bulunamadı")
            return None
        except Exception as e:
            logger.error(f"JSON çıkarma hatası: {e}")
            return None
    
    T = TypeVar('T', bound=BaseModel)
    
    @classmethod
    def parse_model_response(cls, response_text: str, model_class: Type[T]) -> Optional[T]:
        """
        LLM'den gelen yanıtı belirtilen Pydantic model sınıfı kullanarak işler.
        
        Args:
            response_text: LLM'den gelen yanıt metni
            model_class: Kullanılacak Pydantic model sınıfı
            
        Returns:
            Doğrulanmış model örneği veya None (hata durumunda)
        """
        try:
            json_text = cls.extract_json_from_response(response_text)
            if not json_text:
                return None
                
            # JSON'ı parse et
            raw_result = json.loads(json_text)
            
            # Model doğrulaması
            validated = model_class(**raw_result)
            return validated
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Model yanıtı işleme hatası: {model_class.__name__}: {e}")
            return None
