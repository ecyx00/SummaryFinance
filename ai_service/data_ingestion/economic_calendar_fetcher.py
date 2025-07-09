"""
Economic Calendar Fetcher Module

Bu modül, Financial Modeling Prep (FMP) API'sinden ekonomik takvim verilerini çekmek için
EconomicCalendarFetcher sınıfını içerir.
"""

import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
from ..src.core.config import settings

# Logger yapılandırması
logger = logging.getLogger(__name__)

class EconomicCalendarFetcher:
    """
    Financial Modeling Prep (FMP) API'sinden ekonomik takvim verilerini çekmek için kullanılan sınıf.
    
    Bu sınıf, belirtilen tarih aralığındaki ekonomik olayları (GDP yayınları, faiz oranı kararları,
    istihdam raporları vb.) çeker ve formatlı bir liste olarak döndürür.
    """
    
    def __init__(self):
        """EconomicCalendarFetcher sınıfını başlatır ve API anahtarını ayarlar."""
        self.api_key = settings.FMP_API_KEY
        self.base_url = "https://financialmodelingprep.com/api/v3/economic_calendar"
        
        if not self.api_key:
            logger.error("FMP API anahtarı bulunamadı. settings.FMP_API_KEY kontrol edin.")
            raise ValueError("FMP API anahtarı gereklidir.")
        
        logger.info("EconomicCalendarFetcher başlatıldı.")
        
    async def fetch_data_async(self, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Belirtilen tarih aralığındaki ekonomik takvim verilerini asenkron olarak çeker.
        
        Args:
            from_date: Başlangıç tarihi (YYYY-MM-DD formatında)
            to_date: Bitiş tarihi (YYYY-MM-DD formatında)
            
        Returns:
            List[Dict]: Ekonomik olayların listesi
        """
        url = f"{self.base_url}?from={from_date}&to={to_date}&apikey={self.api_key}"
        logger.info(f"Ekonomik takvim verileri çekiliyor: {from_date} - {to_date}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"{len(data)} ekonomik olay başarıyla çekildi.")
                return self._process_events(data)
                
        except httpx.RequestError as e:
            logger.error(f"API isteği sırasında hata: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"API yanıtı hata kodu döndürdü: {e}")
            return []
        except Exception as e:
            logger.error(f"Ekonomik takvim verileri çekilirken beklenmeyen hata: {e}")
            return []
    
    def run_fetch_job(self, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Belirtilen tarih aralığındaki ekonomik takvim verilerini senkron olarak çeker.
        
        Args:
            from_date: Başlangıç tarihi (YYYY-MM-DD formatında)
            to_date: Bitiş tarihi (YYYY-MM-DD formatında)
            
        Returns:
            List[Dict]: İşlenmiş ekonomik olayların listesi
        """
        url = f"{self.base_url}?from={from_date}&to={to_date}&apikey={self.api_key}"
        logger.info(f"Ekonomik takvim verileri çekiliyor: {from_date} - {to_date}")
        
        try:
            with httpx.Client() as client:
                response = client.get(url, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"{len(data)} ekonomik olay başarıyla çekildi.")
                return self._process_events(data)
                
        except httpx.RequestError as e:
            logger.error(f"API isteği sırasında hata: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"API yanıtı hata kodu döndürdü: {e}")
            return []
        except Exception as e:
            logger.error(f"Ekonomik takvim verileri çekilirken beklenmeyen hata: {e}")
            return []
    
    def _process_events(self, events_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        API'den alınan ham verileri işler ve standartlaştırır.
        
        Args:
            events_data: API'den alınan ham ekonomik olay verileri
            
        Returns:
            List[Dict]: İşlenmiş ve standartlaştırılmış ekonomik olayların listesi
        """
        processed_events = []
        
        for event in events_data:
            # Zorunlu alanları kontrol et
            if not all(k in event for k in ('event', 'country', 'date')):
                logger.warning(f"Eksik zorunlu alanlar içeren olay atlanıyor: {event}")
                continue
            
            # Datetime nesnesini parse et
            try:
                event_time = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                logger.warning(f"Geçersiz tarih formatı, olay atlanıyor: {event['date']}")
                continue
            
            # Sayısal değerleri dönüştür
            actual = self._parse_numeric(event.get('actual'))
            forecast = self._parse_numeric(event.get('estimate'))
            previous = self._parse_numeric(event.get('prev'))
            
            # İşlenmiş olayı oluştur
            processed_event = {
                'event_name': event['event'],
                'country': event['country'],
                'event_time': event_time,
                'actual_value': actual,
                'forecast_value': forecast,
                'previous_value': previous,
                'impact': event.get('impact', '').lower().capitalize(),
                'unit': event.get('unit', '')
            }
            
            processed_events.append(processed_event)
            
        return processed_events
    
    def _parse_numeric(self, value: Any) -> Optional[float]:
        """
        Bir değeri sayısal değere dönüştürmeye çalışır.
        
        Args:
            value: Dönüştürülecek değer
            
        Returns:
            Optional[float]: Dönüştürülmüş sayısal değer veya None
        """
        if value is None:
            return None
            
        try:
            # Yüzde işaretini kaldır
            if isinstance(value, str):
                value = value.replace('%', '').strip()
            
            # Boş string kontrolü
            if value == '' or value == 'null':
                return None
                
            return float(value)
        except (ValueError, TypeError):
            return None
