"""
Pipeline Orchestrator Module

Bu modül, AI işleme boru hattının çalışmasını yöneten PipelineOrchestrator sınıfını içerir.
Veritabanından işlenmemiş haberleri çeker, özellikleri paralel olarak çıkarır
ve sonuçları veritabanına kaydeder.
"""

import logging
import concurrent.futures
from typing import Dict, List, Any, Tuple, Optional
import time
import numpy as np
# Direkt veritabanı işlemleri yerine PersistenceManager kullanılıyor
from ..processing.feature_extractor import FeatureExtractor
from ..processing.event_classifier import EventTypeClassifier
from ..db.persistence_manager import PersistenceManager, PROCESSING_SUCCESS, PROCESSING_PARTIAL_SUCCESS, PROCESSING_FAILED
from ..clustering.interaction_scorer import InteractionScorer
from ..clustering.graph_clusterer import GraphClusterer
from ..llm.validator import LLMValidator
from ..llm.enricher import StoryEnricher
from ..processing.asset_mapper import AssetMapper
from ..tracking.story_tracker import StoryTracker
from ..tracking.historical_context_retriever import HistoricalContextRetriever
from ..processing.story_processor import StoryProcessor
from ..llm.synthesizer import LLMSynthesizer
from ..llm.asset_filter import LLMAssetFilter
from ..processing.surprise_score_calculator import SurpriseScoreCalculator
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
    
    def __init__(self, 
                 persistence_manager: PersistenceManager,
                 feature_extractor: FeatureExtractor,
                 event_type_classifier: EventTypeClassifier,
                 asset_mapper: AssetMapper,
                 asset_filter: LLMAssetFilter,
                 interaction_scorer: InteractionScorer,
                 graph_clusterer: GraphClusterer,
                 llm_validator: LLMValidator,
                 story_enricher: StoryEnricher,
                 story_tracker: StoryTracker,
                 story_processor: StoryProcessor,
                 llm_synthesizer: LLMSynthesizer,
                 historical_context_retriever: HistoricalContextRetriever,
                 surprise_score_calculator: SurpriseScoreCalculator,
                 max_workers: int = 5):
        """
        PipelineOrchestrator sınıfını başlatır.
        
        Args:
            persistence_manager: Veritabanı işlemleri için PersistenceManager örneği
            feature_extractor: Özellikleri çıkaran FeatureExtractor örneği
            event_type_classifier: Olay türü sınıflandırıcısı
            asset_mapper: Varlıklara eşleyen AssetMapper örneği
            asset_filter: LLMAssetFilter örneği
            interaction_scorer: Etkileşim skorunu hesaplayan InteractionScorer örneği
            graph_clusterer: Graph tabanlı kümeleme yapan GraphClusterer örneği
            llm_validator: Kümeleri doğrulayan LLMValidator örneği
            story_enricher: Hikayeleri zenginleştiren StoryEnricher örneği
            story_tracker: Hikaye takibi yapan StoryTracker örneği
            story_processor: Hikayeleri işleyen StoryProcessor örneği
            llm_synthesizer: Hikayeleri sentezleyen LLMSynthesizer örneği
            historical_context_retriever: Geçmiş bağlam getiren HistoricalContextRetriever örneği
            surprise_score_calculator: Sürpriz skorunu hesaplayan SurpriseScoreCalculator örneği
            max_workers: Paralel işleyebilecek maksimum iş parçacığı sayısı
        """
        logger.info("PipelineOrchestrator başlatılıyor...")
        
        # Tüm bileşenleri zorunlu parametrelerden al (Dependency Injection)
        self.persistence_manager = persistence_manager
        self.feature_extractor = feature_extractor
        self.event_type_classifier = event_type_classifier
        self.asset_mapper = asset_mapper
        self.asset_filter = asset_filter
        
        # Faz 2 bileşenleri
        self.interaction_scorer = interaction_scorer
        self.graph_clusterer = graph_clusterer
        
        # Faz 3 bileşenleri
        self.llm_validator = llm_validator
        self.story_enricher = story_enricher
        self.story_tracker = story_tracker
        
        # Faz 4 bileşenleri
        self.story_processor = story_processor
        self.llm_synthesizer = llm_synthesizer
        self.historical_context_retriever = historical_context_retriever
        
        # Diğer bileşenler
        self.surprise_score_calculator = surprise_score_calculator
        
        # Genel ayarlar
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
            
            # Olay türünü sınıflandır
            event_info = None
            if enriched_item.get('full_text') and enriched_item.get('entities'):
                logger.info(f"Haber ID {news_id} için olay türü sınıflandırması başlatılıyor")
                event_info = self.event_type_classifier.classify(
                    enriched_item['full_text'], 
                    enriched_item.get('entities', {})
                )
                if event_info:
                    event_type = event_info.get('event_type')
                    priority = event_info.get('priority')
                    description = event_info.get('description')
                    rationale = event_info.get('rationale')
                    
                    logger.info(f"Haber ID {news_id} için olay türü belirlendi: {event_type} (öncelik: {priority})")
                    logger.debug(f"Olay açıklaması: {description}")
                    logger.debug(f"Olay gerekçesi: {rationale}")
                    
                    # Sadece event_type'ı enriched_item'a ekle - veritabanı şeması ile uyumlu olması için
                    enriched_item['event_type'] = event_type
                    
                    # Sürpriz skorunu hesapla
                    try:
                        publication_date = news_item.get('published_at') or datetime.now()
                        logger.info(f"Haber ID {news_id} için sürpriz skoru hesaplanıyor (olay türü: {event_type})")
                        surprise_score = self.surprise_score_calculator.calculate_score(
                            event_type=event_type,
                            publication_date=publication_date
                        )
                        
                        if surprise_score is not None:
                            logger.info(f"Haber ID {news_id} için sürpriz skoru hesaplandı: {surprise_score:.4f}")
                            enriched_item['surprise_score'] = surprise_score
                        else:
                            logger.info(f"Haber ID {news_id} için sürpriz skoru hesaplanamadı (ilgili ekonomik olay bulunamadı)")
                    except Exception as e:
                        logger.error(f"Haber ID {news_id} için sürpriz skoru hesaplanırken hata: {e}")
                    
                    # İsteğe bağlı olarak, gelecekte bu ek bilgileri de kaydetmek istenirse:
                    # enriched_item['event_info'] = event_info
                else:
                    logger.info(f"Haber ID {news_id} için olay türü belirlenemedi")
                    
            # Etkilenen finansal enstrümanları tespit et
            if enriched_item.get('entities'):
                logger.info(f"Haber ID {news_id} için etkilenen varlık analizi başlatılıyor")
                
                # 1. AssetMapper ile potansiyel varlıkları belirle
                candidate_assets = self.asset_mapper.map_assets(enriched_item.get('entities', {}))
                
                if candidate_assets:
                    # 2. LLMAssetFilter ile doğrulama yap
                    try:
                        logger.info(f"Haber ID {news_id} için {len(candidate_assets)} aday varlık LLM ile filtreleniyor")
                        affected_assets_info = self.asset_filter.filter_assets(
                            enriched_item['full_text'],
                            candidate_assets
                        )
                        
                        # Sonuçları değerlendir
                        if affected_assets_info:
                            # Sadece asset listesini al
                            affected_assets = [item.get("asset") for item in affected_assets_info if item.get("asset")]
                            
                            if affected_assets:
                                logger.info(f"Haber ID {news_id} için etkilenen {len(affected_assets)} varlık bulundu: {', '.join(affected_assets)}")
                                enriched_item['affected_assets'] = affected_assets
                                
                                # Detaylı analiz sonuçlarını loglama
                                for asset_info in affected_assets_info:
                                    asset = asset_info.get("asset")
                                    impact = asset_info.get("impact")
                                    reason = asset_info.get("reason")
                                    logger.debug(f"Varlık: {asset}, Etki: {impact}, Neden: {reason}")
                            else:
                                logger.info(f"Haber ID {news_id} için etkilenen varlık bulunamadı (LLM filtreleme sonrası)")
                        else:
                            logger.info(f"Haber ID {news_id} için etkilenen varlık bulunamadı (LLM yanıt hatası)")
                    except Exception as e:
                        logger.error(f"Haber ID {news_id} için varlık filtreleme hatası: {e}")
                else:
                    logger.info(f"Haber ID {news_id} için aday varlık bulunamadı")
            
            # Verileri veritabanına kaydet ve işlem durumunu al
            # PersistenceManager zaten doğru durum kodunu döndürüyor
            status = self.persistence_manager.save_features(enriched_item, model_version)
            
            # İşlem süresini hesapla
            process_time = time.time() - start_time
            
            # affected_assets ve diğer meta veriler enriched_item içinde saklanıyor
            # Bu veriler Faz 2/3'te analiz ve hikaye oluşturma süreçleri sırasında kullanılacak
            # NOT: Bu meta veriler bu aşamada analyzed_stories tablosuna kaydedilmemeli
                
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
        
    def run_phase2(self) -> Dict[str, Any]:
        """
        Faz 2 boru hattını çalıştırır: haberler arasındaki etkileşim skorlarını hesaplar 
        ve graph_edges tablosuna kaydeder.
        
        Önce işlenmiş ve embedding vektörü içeren haberleri veritabanından çeker, 
        ardından InteractionScorer ile aralarındaki etkileşim skorlarını hesaplar.
        
        Returns:
            Dict[str, Any]: İşlem sonuçlarının özeti
                - processed_news_count: İşlenmiş haber sayısı
                - candidate_pairs: Bulunan aday çift sayısı
                - saved_edges: Kaydedilen kenar sayısı
                - success: İşlemin başarılı olup olmadığı
                - duration: İşlem süresi (saniye)
        """
        start_time = time.time()
        results = {
            "processed_news_count": 0,
            "candidate_pairs": 0,
            "saved_edges": 0,
            "success": False,
            "duration": 0
        }
        
        try:
            logger.info("Faz 2: Haber etkileşimleri hesaplanıyor...")
            
            # İşlenmiş haberleri çek (embedding_vector ve entities içeren)
            processed_news = self.persistence_manager.fetch_processed_news(limit=1000)
            results["processed_news_count"] = len(processed_news)
            
            if not processed_news:
                logger.warning("Etkileşim hesaplamak için işlenmiş haber bulunamadı")
                results["duration"] = time.time() - start_time
                return results
                
            logger.info(f"{len(processed_news)} işlenmiş haber için etkileşimler hesaplanacak")
            
            # Etkileşimleri hesapla ve kaydet
            self.interaction_scorer.calculate_and_save_scores(processed_news)
            
            results["success"] = True
            results["duration"] = time.time() - start_time
            logger.info(f"Faz 2 tamamlandı. Süre: {results['duration']:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Faz 2 işlemi sırasında hata oluştu: {e}")
            results["duration"] = time.time() - start_time
            return results
            
    def run_full_pipeline(self, limit: int = 50) -> Dict[str, Any]:
        """
        Tüm pipeline fazlarını sırayla çalıştırır. Bu metod, veri zenginleştirmeden başlayarak
        kümeleme, doğrulama, izleme ve sentezleme adımlarını içeren tam iş akışını uygular.
        
        Args:
            limit: İşlenecek maksimum haber kümesi sayısı
            
        Returns:
            Dict[str, Any]: Pipeline sonuçlarının özeti
        """
        
        # NOT: Ekonomik takvim verilerinin güncellenmesi pipeline'dan bağımsız
        # olarak bir zamanlayıcı (cron job) tarafından gerçekleştirilmelidir.
        # Pipeline, veritabanındaki mevcut ekonomik verileri kullanır,
        # veri güncelleme işlemlerini tetiklemekle sorumlu değildir.
        pipeline_start_time = time.time()
        pipeline_results = {
            "phase1_results": None,
            "phase2_results": None,
            "clusters_found": 0,
            "validated_clusters": 0,
            "created_stories": 0,
            "linked_stories": 0,
            "duration_seconds": 0
        }
        
        try:
            logger.info("================ TAM PİPELINE BAŞLIYOR =================")
            
            # Faz 1: Özellikleri çıkar ve verileri kaydet
            logger.info("Faz 1: Veri zenginleştirme başlıyor...")
            phase1_results = self.run_phase1()
            pipeline_results["phase1_results"] = phase1_results
            logger.info(f"Faz 1 tamamlandı: {phase1_results['success']} haber başarıyla işlendi")
            
            # Faz 2a: Etkileşim skorlarını hesapla ve kaydet
            logger.info("Faz 2a: Etkileşim hesaplama başlıyor...")
            processed_news = self.persistence_manager.fetch_processed_news(limit=1000)
            
            if not processed_news:
                logger.warning("Faz 2a atlanıyor: Skorlanacak işlenmiş haber bulunamadı.")
            else:
                self.interaction_scorer.calculate_and_save_scores(processed_news)
                logger.info(f"Faz 2a tamamlandı: {len(processed_news)} haber için etkileşim skorları hesaplandı")
            
            # Faz 2b: Haber kümelerini oluştur
            logger.info("Faz 2b: Kümeleme başlıyor...")
            candidate_clusters = self.graph_clusterer.cluster_stories()
            pipeline_results["clusters_found"] = len(candidate_clusters)
            logger.info(f"Faz 2b tamamlandı: {len(candidate_clusters)} potansiyel haber kümesi bulundu")
            
            # İşlenecek küme sayısını sınırla
            if len(candidate_clusters) > limit:
                candidate_clusters = candidate_clusters[:limit]
                logger.info(f"İşlenecek küme sayısı {limit} ile sınırlandı")
            
            # Faz 3 ve 4: Her bir aday küme için doğrulama, zenginleştirme, izleme ve analiz
            for cluster_index, news_cluster in enumerate(candidate_clusters):
                cluster_id = f"C{cluster_index+1}"
                cluster_size = len(news_cluster)
                
                logger.info(f"Küme {cluster_id} işleniyor ({cluster_size} haber)...")
                
                try:
                    # a. Kümeyi doğrula
                    validation_result = self.llm_validator.validate_cluster(news_cluster)
                    
                    if not validation_result or not validation_result.get("is_story", False):
                        logger.info(f"Küme {cluster_id} doğrulama başarısız: Geçerli bir hikaye değil")
                        continue
                        
                    pipeline_results["validated_clusters"] += 1
                    logger.info(f"Küme {cluster_id} doğrulandı: '{validation_result.get('story_type', 'Bilinmeyen Hikaye')}' türünde")
                    
                    # b. Hikayeyi zenginleştir (etiket ve gerekçe üret)
                    enrichment_result = self.story_enricher.enrich_story_cluster(news_cluster)
                    if not enrichment_result:
                        logger.error(f"Küme {cluster_id} zenginleştirilemedi")
                        continue
                        
                    story_label = enrichment_result.get("label")
                    story_rationale = enrichment_result.get("rationale")
                    logger.info(f"Küme {cluster_id} zenginleştirildi: '{story_label}'")
                    
                    # Temsilci vektörünü bir kere hesapla ve tüm işlemlerde kullan
                    # Tüm gerekli detayları (embedding, entities dahil) içeren haber öğelerini çek
                    processed_news_items = self.persistence_manager.fetch_news_by_ids(news_cluster)
                    
                    if not processed_news_items:
                        logger.warning(f"Küme {cluster_id} için haber detayları alınamadı")
                        processed_news_items = []
                    
                    # Bu hikaye kümesi için temsil vektörünü hesapla - sadece bir kez
                    representative_vector = None
                    if len(news_cluster) >= 2 and processed_news_items:  # En az 2 haber olmalı
                        embedding_vectors = []
                        for news in processed_news_items:  # Zaten çekilmiş haber verilerini kullan
                            if news.get("embedding_vector") is not None:
                                embedding_vectors.append(np.array(news["embedding_vector"]))
                        
                        if embedding_vectors:
                            representative_vector = np.mean(embedding_vectors, axis=0)
                            logger.info(f"Küme {cluster_id} için temsilci vektör hesaplandı")
                    
                    # c. Hikayenin bir önceki hikaye ile ilişkisi var mı kontrol et
                    # Önceden hesaplanan temsilci vektörü kullan
                    parent_story_id = self.story_tracker.track_story(
                        {
                            "news_ids": news_cluster,
                            "label": story_label,
                            "rationale": story_rationale
                        },
                        representative_vector=representative_vector  # Önceden hesaplanan vektörü geç
                    )
                    
                    # d. RAG adımı - Şimdilik basit bir birleştirme yapıyoruz
                    # Önemli haber parçalarını oluştur
                    salient_snippets = [f"{news.get('title', '')} - {news.get('source_name', '')} ({news.get('published_at', '')})" 
                                        for news in processed_news_items]
                    
                    # e. Benzer geçmiş hikayeleri bul - önceden hesaplanan vektörü kullan
                    historical_context = ""
                    similar_stories = []
                    
                    if representative_vector is not None:
                        similar_stories = self.historical_context_retriever.retrieve_similar_stories(
                            representative_vector, k=3
                        )
                    
                    # Tarihsel bağlam oluştur
                    if similar_stories:
                        historical_context = "Geçmiş benzer hikayeler:\n"
                        for idx, story in enumerate(similar_stories):
                            historical_context += f"\n{idx+1}. {story.get('story_title', 'Başlıksız Hikaye')} (ID: {story.get('story_id')})\n"
                            historical_context += f"   Özet: {story.get('story_essence_text', 'Özet bilgi yok')}\n"
                    elif parent_story_id:
                        # Benzer hikayeler bulunamadıysa ancak bir parent hikaye varsa
                        historical_context = f"Bu hikaye, ID'si {parent_story_id} olan önceki bir hikayenin devamı niteliğindedir."
                    
                    # Stratejik sinyal raporu sentezle
                    analysis_summary = self.llm_synthesizer.synthesize_report({
                        "group_label": story_label,
                        "connection_rationale": story_rationale,
                        "salient_snippets": salient_snippets,
                        "historical_context": historical_context
                    })
                    
                    if not analysis_summary:
                        logger.error(f"Küme {cluster_id} için analiz özeti oluşturulamadı")
                        continue
                        
                    # f. Hikaye için hafıza bileşenlerini üret
                    memory_components = self.story_processor.process_story_for_memory(analysis_summary)
                    
                    if not memory_components:
                        logger.error(f"Küme {cluster_id} için hafıza bileşenleri oluşturulamadı")
                        continue
                        
                    # g. Tüm verileri hikaye veri sözlüğünde topla
                    story_data = {
                        "news_ids": news_cluster,
                        "label": story_label,
                        "rationale": story_rationale,
                        "analysis_summary": analysis_summary,
                        "story_essence_text": memory_components.get("story_essence_text"),
                        "story_context_snippets": memory_components.get("story_context_snippets"),
                        "story_embedding_vector": memory_components.get("story_embedding_vector")
                    }
                    
                    # h. Hikayeyi veritabanına kaydet
                    story_id = self.persistence_manager.save_story(story_data)
                    
                    if not story_id:
                        logger.error(f"Küme {cluster_id} veritabanına kaydedilemedi")
                        continue
                        
                    pipeline_results["created_stories"] += 1
                    logger.info(f"Küme {cluster_id} veritabanına kaydedildi: Story ID={story_id}")
                    
                    # i. Eğer bir parent hikaye varsa, ilişkiyi kaydet
                    if parent_story_id:
                        relationship_saved = self.persistence_manager.save_story_relationship(
                            source_story_id=story_id,
                            target_story_id=parent_story_id,
                            relationship_type="EVOLVED_FROM",
                            created_by="PipelineOrchestrator"
                        )
                        
                        if relationship_saved:
                            pipeline_results["linked_stories"] += 1
                            logger.info(f"Hikaye ilişkisi kaydedildi: {story_id} -> {parent_story_id} (EVOLVED_FROM)")
                        else:
                            logger.error(f"Hikaye ilişkisi kaydedilemedi: {story_id} -> {parent_story_id}")
                    
                except Exception as e:
                    logger.error(f"Küme {cluster_id} işlenirken hata: {e}")
                    continue
            
            # Pipeline tamamlandı, sonuçları topla
            pipeline_end_time = time.time()
            pipeline_duration = pipeline_end_time - pipeline_start_time
            pipeline_results["duration_seconds"] = pipeline_duration
            
            # Özet rapor
            logger.info("================ TAM PİPELINE SONUÇLARI =================")
            logger.info(f"Toplam süre: {pipeline_duration:.2f} saniye")
            logger.info(f"Bulunan kümeler: {pipeline_results['clusters_found']}")
            logger.info(f"Doğrulanan kümeler: {pipeline_results['validated_clusters']}")
            logger.info(f"Oluşturulan hikayeler: {pipeline_results['created_stories']}")
            logger.info(f"İlişkilendirilen hikayeler: {pipeline_results['linked_stories']}")
            logger.info("=======================================================")
            
            return pipeline_results
            
        except Exception as e:
            logger.error(f"Tam pipeline çalıştırılırken hata: {e}")
            pipeline_results["duration_seconds"] = time.time() - pipeline_start_time
            return pipeline_results
