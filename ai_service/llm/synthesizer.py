"""
LLM Synthesizer Module

Bu modül, haber hikayelerinin stratejik sinyal raporunu sentezleyen LLMSynthesizer
sınıfını içerir. Bu sınıf, bir hikaye grubu için tüm bağlamı alarak
Markdown formatında nihai bir rapor üretir.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai

from ..core.config import settings
from ..utils.prompt_helper import get_prompt_path

# Logger yapılandırması
logger = logging.getLogger(__name__)


class LLMSynthesizer:
    """
    Haber hikayesi grupları için stratejik sinyal raporları üreten sınıf.
    
    Bu sınıf, bir hikaye grubu hakkındaki tüm bağlamları (haber parçaları, 
    tarihsel bağlam, bağlantı gerekçesi vb.) alır ve bunları kullanarak 
    nihai bir Markdown formatında rapor üretir.
    """
    
    def __init__(self):
        """
        LLMSynthesizer sınıfını başlatır ve gereken LLM modelini yapılandırır.
        """
        try:
            # Gemini modeli için API anahtarını ayarla
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Gemini modelini yapılandır
            self.gemini_model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL_NAME
            )
            logger.info(f"Gemini modeli başlatıldı: {settings.GEMINI_MODEL_NAME}")
            
            # Prompt şablonunu yükle
            self.synthesis_prompt_template = Path(get_prompt_path("synthesis/v1.0.txt")).read_text(encoding="utf-8")
            logger.info("Sentez prompt şablonu yüklendi")
            
        except Exception as e:
            logger.error(f"LLMSynthesizer başlatılırken hata: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def synthesize_report(self, story_context: Dict) -> Optional[str]:
        """
        Verilen bağlam bilgilerine göre stratejik sinyal raporu sentezler.
        
        Args:
            story_context: Hikaye bağlam bilgilerini içeren sözlük. Şu anahtarları içermelidir:
                - group_label: Hikaye grubu etiketi
                - connection_rationale: Grubu bir araya getiren bağlantı açıklaması
                - salient_snippets: Hikayeyle ilgili önemli haber parçaları listesi
                - historical_context: (opsiyonel) Önceki hikayelerden tarihsel bağlam
                
        Returns:
            Optional[str]: Markdown formatında stratejik sinyal raporu metni, hata durumunda None
        """
        try:
            logger.info(f"'{story_context.get('group_label', 'Isimsiz grup')}' için stratejik sinyal raporu sentezleniyor...")
            
            # Gerekli alanların varlığını kontrol et
            if not story_context.get("group_label") or not story_context.get("salient_snippets"):
                logger.error("Eksik bağlam bilgisi: group_label ve salient_snippets gerekli")
                return None
                
            # Snippet'ları düzgün bir metin haline getir
            if isinstance(story_context.get("salient_snippets"), list):
                formatted_snippets = "\n\n".join([f"- {snippet}" for snippet in story_context["salient_snippets"]])
            else:
                formatted_snippets = story_context.get("salient_snippets", "")
            
            # Prompt şablonunu doldur
            prompt = self.synthesis_prompt_template.format(
                group_label=story_context.get("group_label", ""),
                connection_rationale=story_context.get("connection_rationale", ""),
                salient_snippets=formatted_snippets,
                historical_context=story_context.get("historical_context", "Önceki hikaye bağlamı mevcut değil."),
                macro_context=story_context.get("macro_context", "")  # MVP için boş bırakılabilir
            )
            
            # Gemini'ye istek gönder
            logger.info("LLM'e stratejik rapor üretimi isteği gönderiliyor...")
            response = self.gemini_model.generate_content(prompt)
            
            # Yanıtı kontrol et
            if not response.text or not response.text.strip():
                logger.error("LLM boş yanıt döndü")
                return None
            
            report_text = response.text.strip()
            logger.info(f"Stratejik sinyal raporu başarıyla üretildi ({len(report_text)} karakter)")
            return report_text
            
        except Exception as e:
            logger.error(f"Rapor sentezlenirken hata: {e}")
            return None
