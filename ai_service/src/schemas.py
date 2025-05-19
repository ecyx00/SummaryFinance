from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, RootModel


class GeminiGroupItemSchema(BaseModel):
    """
    Gemini API'dan dönen tek bir haber grubu için şema (Aşama 1 - Gruplama).
    """
    group_label: str = Field(..., description="Haber grubu için tanımlayıcı etiket")
    related_news_ids: List[str] = Field(..., description="Bu gruba ait haber ID'lerinin listesi")

    model_config = {
        "json_schema_extra": {
            "example": {
                "group_label": "Ekonomi: Merkez Bankası Faiz Kararı",
                "related_news_ids": ["1", "4", "7"]
            }
        }
    }


class GeminiGroupResponseSchema(RootModel[List[GeminiGroupItemSchema]]):
    """
    Gemini API'dan dönen tüm haber grupları için şema (Aşama 1 - Gruplama).
    Pydantic v2 için RootModel kullanılır.
    """
    
    model_config = {
        "json_schema_extra": {
            "example": [
                {
                    "group_label": "Ekonomi: Merkez Bankası Faiz Kararı",
                    "related_news_ids": ["1", "4", "7"]
                },
                {
                    "group_label": "Dış Politika: AB Zirvesi",
                    "related_news_ids": ["2", "5"]
                }
            ]
        }
    }


class AnalyzedStorySchema(BaseModel):
    """
    Gemini API'dan dönen detaylı analiz edilmiş hikaye için şema (Aşama 2 - Detaylı Analiz).
    """
    story_title: str = Field(..., description="Haber grubu için geliştirilmiş başlık")
    related_news_ids: List[str] = Field(..., description="Bu hikayeye ait haber ID'lerinin listesi")
    analysis_summary: str = Field(..., description="Detaylı analiz özeti (disclaimer metni dahil)")
    main_categories: List[str] = Field(..., description="Ana kategoriler")

    model_config = {
        "json_schema_extra": {
            "example": {
                "story_title": "Merkez Bankası'nın Beklenmeyen Faiz Artırımı Piyasalarda Çalkantı Yarattı",
                "related_news_ids": ["1", "4", "7"],
                "analysis_summary": "Merkez Bankası'nın bugün yaptığı beklenmedik faiz artırımı, enflasyonla mücadelede daha sert bir tutum sergileme niyetinin işareti olarak görüldü. Piyasalar bu karara sürpriz bir şekilde olumlu tepki gösterdi. Uzmanlar, bu hamlenin kısa vadede ekonomik büyümeyi yavaşlatabileeğini ancak uzun vadede daha sağlıklı bir enflasyon profiline yol açabileceğini düşünüyor.\n\nUYARI: Bu içerik yapay zeka ile otomatik olarak üretilmiş olup, sağlanan haberlere dayanmaktadır ve genel bilgilendirme amaçlıdır. Yatırım tavsiyesi niteliği taşımaz.",
                "main_categories": ["EKONOMİ", "PİYASALAR"]
            }
        }
    }