import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from ..src.db.persistence_manager import PersistenceManager

# Logger yapılandırması
logger = logging.getLogger(__name__)


class SurpriseScoreCalculator:
    """
    Ekonomik olayların piyasa beklentilerinden sapma derecesini ölçen bir sürpriz skoru hesaplayıcı.
    
    Bu sınıf, gerçekleşen (actual) ve tahmin edilen (forecast) değerler arasındaki farkı kullanarak
    0.0 ile 1.0 arasında normalize edilmiş bir sürpriz skoru hesaplar.
    """
    
    def __init__(self, persistence_manager: Optional[PersistenceManager] = None):
        """
        SurpriseScoreCalculator sınıfı constructor'ı.
        
        Args:
            persistence_manager: Veritabanı işlemleri için PersistenceManager nesnesi.
                                Eğer None ise yeni bir PersistenceManager oluşturulur.
        """
        if persistence_manager:
            self.persistence_manager = persistence_manager
        else:
            from ..src.db.persistence_manager import PersistenceManager
            self.persistence_manager = PersistenceManager()
    
    def calculate_score(self, event_type: str, publication_date: datetime) -> Optional[float]:
        """
        Verilen olay türü ve yayın tarihine göre sürpriz skoru hesaplar.
        
        Bu metod şu adımları uygular:
        1. Veritabanından belirtilen olay türü ve tarihe en yakın ekonomik olayı bulur
        2. Bulunan olayın actual_value ve forecast_value değerlerini karşılaştırır
        3. Bu değerler arasındaki normalize edilmiş farkı hesaplayarak 0.0-1.0 arası bir skor döndürür
        
        Args:
            event_type: Haberin olay türü (ör: INFLATION_DATA, INTEREST_RATE_DECISION vb.)
            publication_date: Haberin yayınlanma tarihi
            
        Returns:
            float: 0.0 ile 1.0 arasında hesaplanmış sürpriz skoru.
                  Eğer ilgili ekonomik olay bulunamazsa veya gerekli değerler eksikse None döner.
        """
        try:
            # Önce ilgili ekonomik olayı bulalım
            # publication_date'den önce ve sonra belirli bir zaman aralığında arama yapacağız
            # Genellikle ekonomik olaylar ve bunlarla ilgili haberler aynı gün veya 1-2 gün içinde yayınlanır
            date_range_before = publication_date - timedelta(days=2)
            date_range_after = publication_date + timedelta(days=2)
            
            # Olay türünden anahtar kelimeleri çıkar (örn: "INFLATION_DATA" -> "inflation")
            search_keywords = self._extract_keywords_from_event_type(event_type)
            
            # Veritabanında bu zaman aralığında ve olay türüne uygun ekonomik olayları ara
            economic_events = self.persistence_manager.find_economic_events_by_date_range_and_keywords(
                date_range_before, 
                date_range_after,
                search_keywords
            )
            
            if not economic_events:
                logger.info(f"Sürpriz skoru hesabı için {event_type} türüne uygun ekonomik olay bulunamadı")
                return None
            
            # En uygun olayı bul (tarih olarak en yakın)
            closest_event = self._find_closest_event_by_date(economic_events, publication_date)
            
            if not closest_event:
                return None
            
            # Actual ve forecast değerleri kontrol et
            actual_value = closest_event.get('actual_value')
            forecast_value = closest_event.get('forecast_value')
            
            if actual_value is None or forecast_value is None:
                logger.info(f"Olay ID {closest_event.get('id')} için actual_value veya forecast_value değeri yok")
                return None
            
            # Değerlerin sayı olduğundan emin ol
            try:
                actual_value = float(actual_value)
                forecast_value = float(forecast_value)
            except (ValueError, TypeError):
                logger.warning(f"Olay ID {closest_event.get('id')} için sayısal olmayan değerler: actual={actual_value}, forecast={forecast_value}")
                return None
            
            # Sürpriz skorunu hesapla (0.0 - 1.0 arasında normalize et)
            return self._calculate_normalized_surprise_score(actual_value, forecast_value)
            
        except Exception as e:
            logger.error(f"Sürpriz skoru hesaplanırken hata: {e}")
            return None
    
    def _extract_keywords_from_event_type(self, event_type: str) -> List[str]:
        """
        Olay türünden arama için anahtar kelimeleri çıkarır.
        
        Args:
            event_type: Olay türü (ör: "INFLATION_DATA")
            
        Returns:
            List[str]: Arama için anahtar kelimeler listesi
        """
        # Olay türünü alt çizgilerden ayırıp küçük harfe dönüştür
        keywords = event_type.lower().split('_')
        
        # DATA, REPORT gibi genel kelimeleri filtrele
        filtered_keywords = [k for k in keywords if k not in ('data', 'report', 'announcement')]
        
        # Bazı yaygın finansal terimler için eşleşmeler ekle
        term_mappings = {
            'inflation': ['cpi', 'consumer price', 'inflation'],
            'gdp': ['gdp', 'gross domestic', 'economic growth'],
            'employment': ['nonfarm', 'unemployment', 'job', 'employment'],
            'interest': ['rate', 'interest', 'fed', 'central bank'],
        }
        
        expanded_keywords = []
        for keyword in filtered_keywords:
            expanded_keywords.append(keyword)
            # İlgili anahtar kelime için ek terimleri ekle
            for key, mappings in term_mappings.items():
                if keyword in key:
                    expanded_keywords.extend(mappings)
        
        return list(set(expanded_keywords))  # Tekrarları kaldır
    
    def _find_closest_event_by_date(self, events: List[Dict[str, Any]], target_date: datetime) -> Optional[Dict[str, Any]]:
        """
        Verilen olaylar listesinde, hedef tarihe en yakın olayı bulur.
        
        Args:
            events: Ekonomik olaylar listesi
            target_date: Hedef tarih
            
        Returns:
            Dict: Hedef tarihe en yakın olay
        """
        if not events:
            return None
            
        closest_event = None
        min_time_diff = timedelta.max
        
        for event in events:
            event_time = event.get('event_time')
            if not event_time:
                continue
                
            time_diff = abs(event_time - target_date)
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_event = event
                
        return closest_event
    
    def _calculate_normalized_surprise_score(self, actual: float, forecast: float) -> float:
        """
        Actual ve forecast değerleri arasındaki farkı normalize ederek 0.0-1.0 arasında bir skor döndürür.
        
        Formül: abs(actual - forecast) / (abs(forecast) veya 1.0)
        Sonuç 1.0'dan büyükse (fark tahminden büyükse), 1.0 olarak sınırlandırılır.
        
        Args:
            actual: Gerçekleşen değer
            forecast: Tahmin edilen değer
            
        Returns:
            float: 0.0 ile 1.0 arasında normalize edilmiş sürpriz skoru
        """
        # Paydada 0'a bölünmeyi önle
        denominator = abs(forecast) if abs(forecast) > 0.001 else 1.0
        
        # Normalize edilmiş farkı hesapla
        surprise_score = abs(actual - forecast) / denominator
        
        # Skoru 0.0 ile 1.0 arasında sınırla
        return min(surprise_score, 1.0)
