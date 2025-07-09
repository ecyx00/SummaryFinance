"""
Asset Filter Module

Bu modül, aday finansal enstrüman listesini haber içeriği bağlamında filtreleyen 
ve gerçekten etkilenebilecek enstrümanları belirleyen LLMAssetFilter sınıfını içerir.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

from pydantic import BaseModel, Field, ValidationError
from typing import List, Literal

from ..core.llm_client import LLMClient
from ..core.config import settings
# Mutlak import yolunu kullanarak modul yapisi sorununu cozume
from ai_service.src.llm.parser import LLMOutputParser

# Logger yapılandırması
logger = logging.getLogger(__name__)


class AffectedAsset(BaseModel):
    """Etkilenen finansal enstrüman modelini temsil eder."""
    asset: str
    reason: str
    impact: Literal["positive", "negative", "neutral"]


class AssetImpactResponse(BaseModel):
    """LLM'den dönen etkilenen finansal enstrümanlar listesini temsil eder."""
    __root__: List[AffectedAsset]


class LLMAssetFilter:
    """
    Aday finansal enstrüman listesini haber içeriği bağlamında filtreleyen sınıf.
    
    Bu sınıf, AssetMapper tarafından belirlenen aday enstrüman listesini alır, 
    haberin içeriğini analiz eder ve gerçekten etkilenebilecek finansal enstrümanları belirler.
    """

    def __init__(self, prompt_path: str = None):
        """
        LLMAssetFilter sınıfını başlatır.
        
        Args:
            prompt_path: LLM prompt şablonunu içeren dosyanın yolu.
                       None ise varsayılan konum kullanılır.
        """
        logger.info("LLMAssetFilter başlatılıyor...")
        
        # LLM istemcisini başlat
        self.llm_client = LLMClient()
        
        # Eğer özel bir dosya yolu belirtilmemişse varsayılan konumu kullan
        if not prompt_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            prompt_path = os.path.join(base_dir, "prompts", "ASSET_IMPACT_ANALYSIS_V1.0.txt")
        
        try:
            # Prompt şablonunu yükle
            logger.info(f"LLM prompt şablonu yükleniyor: {prompt_path}")
            with open(prompt_path, 'r', encoding='utf-8') as file:
                self.prompt_template = file.read()
            
            logger.info("LLM prompt şablonu başarıyla yüklendi")
        
        except Exception as e:
            logger.error(f"LLM prompt şablonu yüklenirken hata oluştu: {e}")
            self.prompt_template = """
                Sana bir haber metni ve potansiyel olarak etkilenebilecek finansal enstrümanların bir listesi verilecek.
                Haberin içeriğini analiz ederek, hangi finansal enstrümanların gerçekten etkilenebileceğini belirle.
                
                Haber metni: {text}
                
                Potansiyel finansal enstrümanlar: {candidate_assets}
                
                Lütfen etkilenecek finansal enstrümanları, etkilenme nedeniyle birlikte JSON formatında döndür:
                [
                    {{"asset": "XXX", "reason": "...", "impact": "positive|negative|neutral"}}
                ]
                
                Yalnızca haberin içeriğiyle doğrudan ilişkili finansal enstrümanları dahil et.
            """
            logger.warning("Varsayılan prompt şablonu kullanılıyor")

    def filter_assets(self, text: str, candidate_assets: List[str]) -> List[Dict[str, Any]]:
        """
        Aday finansal enstrüman listesini haber içeriği bağlamında filtreler.
        
        Args:
            text: Haber metni
            candidate_assets: AssetMapper tarafından belirlenen aday finansal enstrüman listesi
        
        Returns:
            List[Dict[str, Any]]: Etkilenebilecek finansal enstrümanlar ve etki bilgileri
                                 [{"asset": "XXX", "reason": "...", "impact": "positive|negative|neutral"}, ...]
        """
        if not text or not candidate_assets:
            logger.warning("Filtreleme yapılamıyor: Metin veya aday enstrümanlar boş")
            return []
        
        try:
            # Prompt hazırlama
            prompt = self.prompt_template.format(
                text=text[:3000],  # Metin çok uzunsa kısalt
                candidate_assets=", ".join(candidate_assets)
            )
            
            logger.info(f"LLM isteği gönderiliyor: {len(candidate_assets)} aday enstrüman ile")
            
            # LLM isteği
            response = self.llm_client.generate_text(prompt)
            
            if not response:
                logger.error("LLM yanıt vermedi")
                return []
            
            # JSON yanıtını merkezi parser kullanarak ayıkla
            json_str = LLMOutputParser.extract_json_from_response(response)
            
            if not json_str:
                logger.error(f"JSON yapısı bulunamadı: {response}")
                return []
                
            try:
                # JSON verilerini yükle
                raw_result = json.loads(json_str)
                
                # Pydantic model ile doğrulama
                try:
                    validated_response = AssetImpactResponse(__root__=raw_result)
                    affected_assets_info = validated_response.__root__
                    
                    # Etkilenen varlıkların adlarını loglamak için
                    affected_assets = [item.asset for item in affected_assets_info]
                    
                    logger.info(f"Filtreleme sonucu {len(affected_assets)} finansal enstrüman belirlendi: {', '.join(affected_assets)}")
                    
                    # Sözlük formatına dönüştürerek döndür
                    return [item.dict() for item in affected_assets_info]
                
                except ValidationError as ve:
                    logger.error(f"Yanıt doğrulama hatası: {ve}")
                    return []
            
            except json.JSONDecodeError as e:
                logger.error(f"JSON ayrıştırma hatası: {e}, yanıt: {response}")
                return []
            
        except Exception as e:
            logger.error(f"Varlık filtreleme sırasında hata oluştu: {e}")
            return []
    

