"""
Pipeline Orchestrator Module

Bu modül, AI işleme boru hattının çalışmasını yöneten PipelineOrchestrator sınıfını içerir.
Veritabanından işlenmemiş haberleri çeker, özellikleri paralel olarak çıkarır
ve sonuçları veritabanına kaydeder.
"""

import logging
import concurrent.futures
from typing import Dict, List, Any, Tuple
import time
# Direkt veritabanı işlemleri yerine PersistenceManager kullanılıyor
from ..processing.feature_extractor import FeatureExtractor
from ..db.persistence_manager import PersistenceManager, PROCESSING_SUCCESS, PROCESSING_PARTIAL_SUCCESS, PROCESSING_FAILED
from ..core.config import settings

# Logger yapılandırması
logger = logging.getLogger(__name__)

# İşlem durum sabitleri artık PersistenceManager'da tanımlı


class PipelineOrchestrator:
    """
    AI özellik çıkarma ve veri kaydetme işlemlerini düzenleyen sınıf.
    
    Bu sınıf, FeatureExtractor ve PersistenceManager bileşenlerini kullanarak
    işlenmemiş haberleri işler ve sonuçları veritabanına kaydeder.
    """
    
    def __init__(self, max_workers: int = 5):
        """
        PipelineOrchestrator sınıfını başlatır.
        
        Args:
            max_workers: Paralel işleyebilecek maksimum iş parçacığı sayısı
        """
        logger.info("PipelineOrchestrator başlatılıyor...")
        self.feature_extractor = FeatureExtractor()
        self.persistence_manager = PersistenceManager()
        self.max_workers = max_workers
        logger.info(f"PipelineOrchestrator başlatıldı (max_workers: {max_workers})")
        
    # _fetch_unprocessed_news metodu kaldırıldı, sorumluluk PersistenceManager'a devredildi
    
    def _process_news(self, news_item: Dict[str, Any]) -> str:
        """
        Bir haber öğesini işleyerek özelliklerini çıkarır ve sonuçları kaydeder.
        
        Args:
            news_item: İşlenecek haber öğesi (id ve url içermeli)
            
        Returns:
            str: İşlemin durumu (PROCESSING_SUCCESS, PROCESSING_PARTIAL_SUCCESS, PROCESSING_FAILED)
        """
        news_id = news_item["id"]
        try:
            # Başlama zamanını kaydet
            start_time = time.time()
            
            # Özellikleri çıkar
            logger.info(f"Haber ID {news_id} için özellik çıkarma başlatılıyor")
            enriched_item = self.feature_extractor.extract_features(news_item)
            
            # Modelin adını al
            model_version = settings.EMBEDDING_MODEL_NAME
            
            # Sonuçları veritabanına kaydet ve işlem durumunu al
            # PersistenceManager zaten doğru durum kodunu döndürüyor
            status = self.persistence_manager.save_features(enriched_item, model_version)
            
            # İşlem süresini hesapla
            process_time = time.time() - start_time
                
            logger.info(f"Haber ID {news_id} işlendi. Durum: {status}, Süre: {process_time:.2f}s")
            return status
            
        except Exception as e:
            logger.error(f"Haber ID {news_id} işlenirken hata: {e}")
            return PROCESSING_FAILED
            
    def run_phase1(self) -> Dict[str, int]:
        """
        Faz 1 boru hattını çalıştırır: özellikleri çıkarır ve verileri kaydeder.
        
        Returns:
            Dict[str, int]: İşlem sonuçlarının özeti
                - total: Toplam işlenen haber sayısı
                - success: Tamamen başarılı işlenen haber sayısı
                - partial: Kısmen başarılı işlenen haber sayısı
                - failed: Başarısız işlenen haber sayısı
        """
        # Özet sonuçları tutacak sözlük
        results = {
            "total": 0,
            "success": 0,
            "partial": 0,
            "failed": 0
        }
        
        # İşlenmemiş haberleri doğrudan PersistenceManager'dan al
        unprocessed_news = self.persistence_manager.fetch_unprocessed_news(limit=100)
        results["total"] = len(unprocessed_news)
        
        if not unprocessed_news:
            logger.info("İşlenecek haber bulunamadı")
            return results
            
        logger.info(f"{len(unprocessed_news)} haber paralel olarak işlenecek (max_workers: {self.max_workers})")
        
        # İş parçacığı havuzu oluştur
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Her bir haber için _process_news metodunu çağır
            future_to_news = {executor.submit(self._process_news, news): news for news in unprocessed_news}
            
            # Tamamlanan işleri bekle ve sonuçları topla
            for future in concurrent.futures.as_completed(future_to_news):
                news = future_to_news[future]
                try:
                    # _process_news artık doğrudan durum kodu döndürüyor
                    status = future.result()
                    
                    # PersistenceManager'dan dönen duruma göre sayaçları güncelle
                    if status == PROCESSING_SUCCESS:
                        results["success"] += 1
                    elif status == PROCESSING_PARTIAL_SUCCESS:
                        results["partial"] += 1
                    else:
                        results["failed"] += 1
                        
                except Exception as e:
                    logger.error(f"Haber ID {news.get('id')} için Executor hatası: {e}")
                    results["failed"] += 1
                    
        # Özet sonuçları logla
        logger.info(f"İşlem tamamlandı: {results['success']} başarılı, " + 
                   f"{results['partial']} kısmi başarılı, {results['failed']} başarısız " +
                   f"(Toplam: {results['total']})")
                   
        return results
