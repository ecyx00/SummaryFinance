#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Interaction Scorer Module

Bu modül, haberler arasındaki etkileşim potansiyelini çeşitli metriklere dayanarak hesaplar:
- Semantik benzerlik (embedding vektörleri arasındaki kosinüs benzerliği)
- Varlık benzerliği (ortak varlıkların Jaccard benzerliği)
- Zamansal yakınlık (yayın tarihleri arasındaki mesafe)

Hesaplanan skorlar, graf oluşturma işlemleri için graph_edges tablosuna kaydedilir.
"""

import logging
import time
from typing import Dict, List, Tuple, Set, Optional
import numpy as np
import faiss
from datetime import datetime
from ..core.config import settings
from ..db.persistence_manager import PersistenceManager

# Logger konfigürasyonu
logger = logging.getLogger(__name__)


class InteractionScorer:
    """
    Haberler arasındaki etkileşim potansiyelini hesaplayan sınıf.
    
    Bu sınıf, faiss kütüphanesini kullanarak verimli bir şekilde aday haber çiftleri bulur
    ve her bir çift için semantik, varlık ve zamansal skorları hesaplayarak bunları
    birleştirir. Sonuçlar graph_edges tablosuna kaydedilir.
    """
    
    def __init__(self, persistence_manager: Optional[PersistenceManager] = None):
        """
        InteractionScorer sınıfının başlatıcısı.
        
        Args:
            persistence_manager: Veritabanı işlemleri için PersistenceManager nesnesi.
                                 None ise yeni bir nesne oluşturulur.
        """
        # Yapılandırma değerlerini al
        self.semantic_weight = settings.INTERACTION_SCORER_SEMANTIC_WEIGHT
        self.entity_weight = settings.INTERACTION_SCORER_ENTITY_WEIGHT
        self.temporal_weight = settings.INTERACTION_SCORER_TEMPORAL_WEIGHT
        self.interaction_threshold = settings.INTERACTION_THRESHOLD
        self.k_neighbors = settings.INTERACTION_SCORER_K_NEIGHBORS
        
        # Veritabanı yöneticisini ayarla
        self.persistence_manager = persistence_manager or PersistenceManager()
        
        logger.info(f"InteractionScorer başlatıldı. Ağırlıklar: semantik={self.semantic_weight}, "
                   f"varlık={self.entity_weight}, zamansal={self.temporal_weight}, "
                   f"eşik={self.interaction_threshold}, k={self.k_neighbors}")
    
    def _find_candidate_pairs(self, news_list: List[Dict]) -> List[Tuple[int, int]]:
        """
        Her bir haber için en yakın k komşuyu bularak aday çiftlerini oluşturur.
        
        FAISS kütüphanesi, büyük vektör setleri arasında etkili benzerlik araması yapar.
        Böylece O(n²) karşılaştırması yerine vektör tabanlı en yakın komşu araması yapılır.
        
        Args:
            news_list: İşlenecek haberler listesi. 
                      Her haber sözlüğünde 'id' ve 'embedding_vector' olmalı.
                      
        Returns:
            List[Tuple[int, int]]: (kaynak_haber_id, hedef_haber_id) şeklinde aday çiftlerin listesi.
        """
        start_time = time.time()
        candidate_pairs = []
        
        # Yeterli haber yoksa boş liste döndür
        if len(news_list) < 2:
            logger.warning("Aday çift oluşturmak için yeterli haber yok")
            return []
        
        # Embedding vektörlerini numpy dizisine dönüştür
        embeddings = []
        ids = []
        
        for news in news_list:
            if news.get('embedding_vector') is None:
                continue
            
            embeddings.append(news['embedding_vector'])
            ids.append(news['id'])
        
        if len(embeddings) < 2:
            logger.warning("Yeterli embedding vektörü bulunamadı")
            return []
        
        # numpy dizisine dönüştür
        embeddings_np = np.array(embeddings, dtype=np.float32)
        
        # FAISS indeksi oluştur (L2 mesafesi için)
        dimension = embeddings_np.shape[1]
        index = faiss.IndexFlatL2(dimension)
        
        # Vektörleri indekse ekle
        index.add(embeddings_np)
        
        # En yakın k komşuyu bul (kendisi hariç)
        k = min(self.k_neighbors + 1, len(embeddings))  # +1 çünkü kendisi de sonuçta olacak
        distances, neighbors = index.search(embeddings_np, k)
        
        # Aday çiftleri oluştur
        for i, neighbor_indices in enumerate(neighbors):
            source_id = ids[i]
            
            # İlk sonuç kendisi olacaktır, onu atla
            for j in neighbor_indices[1:]:  # 0. indeksi atla
                if j < len(ids):  # Geçerli indeks kontrolü
                    target_id = ids[j]
                    # Çift sıralamasını normalize et (küçük ID her zaman önce)
                    if source_id < target_id:
                        candidate_pairs.append((source_id, target_id))
                    else:
                        candidate_pairs.append((target_id, source_id))
        
        # Tekrarlanan çiftleri kaldır
        unique_pairs = list(set(candidate_pairs))
        
        logger.info(f"{len(unique_pairs)} aday çift belirlendi (işlem süresi: {time.time() - start_time:.2f}s)")
        return unique_pairs
    
    def _calculate_semantic_score(self, news1: Dict, news2: Dict) -> float:
        """
        İki haber arasındaki semantik benzerlik skorunu hesaplar (kosinüs benzerliği).
        
        Args:
            news1: Birinci haber
            news2: İkinci haber
            
        Returns:
            float: 0-1 arasında semantik benzerlik skoru
        """
        # Embedding vektörleri kontrolü
        if (not news1.get('embedding_vector')) or (not news2.get('embedding_vector')):
            return 0.0
        
        # Vektörleri numpy dizileri olarak al
        vec1 = np.array(news1['embedding_vector'])
        vec2 = np.array(news2['embedding_vector'])
        
        # Kosinüs benzerliğini hesapla: cos(θ) = (vec1·vec2)/(|vec1|·|vec2|)
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        # Sıfıra bölme hatalarını önle
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        cosine_similarity = dot_product / (norm1 * norm2)
        
        # Değerin 0-1 arasında olduğundan emin ol
        return max(0.0, min(1.0, cosine_similarity))
    
    def _calculate_entity_score(self, news1: Dict, news2: Dict) -> float:
        """
        İki haber arasındaki varlık benzerliği skorunu hesaplar (Jaccard benzerliği).
        
        Args:
            news1: Birinci haber
            news2: İkinci haber
            
        Returns:
            float: 0-1 arasında varlık benzerlik skoru
        """
        # Entities listelerini kontrol et
        if (not news1.get('entities')) or (not news2.get('entities')):
            return 0.0
        
        # Entity setlerini oluştur
        entities1 = {entity['name'].lower() for entity in news1['entities']}
        entities2 = {entity['name'].lower() for entity in news2['entities']}
        
        # Boş set kontrolü
        if not entities1 or not entities2:
            return 0.0
        
        # Jaccard benzerliğini hesapla: |A ∩ B| / |A ∪ B|
        intersection = len(entities1.intersection(entities2))
        union = len(entities1.union(entities2))
        
        if union == 0:
            return 0.0
            
        return intersection / union
    
    def _calculate_temporal_score(self, news1: Dict, news2: Dict) -> float:
        """
        İki haber arasındaki zamansal yakınlık skorunu hesaplar.
        
        Yayın tarihleri arasındaki farkın üstel azalma formülüyle hesaplanır:
        score = e^(-abs(date_diff) / scale_factor)
        
        Args:
            news1: Birinci haber
            news2: İkinci haber
            
        Returns:
            float: 0-1 arasında zamansal yakınlık skoru (1: çok yakın, 0: çok uzak)
        """
        # Published_at alanlarını kontrol et
        if (not news1.get('published_at')) or (not news2.get('published_at')):
            return 0.5  # Yayın tarihi yoksa orta değer döndür
        
        # Tarihleri datetime nesnelerine dönüştür
        try:
            if isinstance(news1['published_at'], str):
                date1 = datetime.fromisoformat(news1['published_at'].replace('Z', '+00:00'))
            else:
                date1 = news1['published_at']
            
            if isinstance(news2['published_at'], str):
                date2 = datetime.fromisoformat(news2['published_at'].replace('Z', '+00:00'))
            else:
                date2 = news2['published_at']
            
            # Tarih farkını gün olarak hesapla
            date_diff = abs((date1 - date2).total_seconds() / (24 * 3600))
            
            # Üstel azalma fonksiyonu kullan
            # Scale_factor değeri, yarı değer süresidir (bu değerde skor 0.5 olur)
            # Örneğin 7 gün için: 7 gün fark varsa skor 0.5 olur
            scale_factor = 7.0
            temporal_score = np.exp(-date_diff / scale_factor)
            
            return temporal_score
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Zamansal skor hesaplama hatası: {e}")
            return 0.5  # Hata durumunda orta değer döndür
    
    def calculate_and_save_scores(self, news_list: List[Dict]) -> None:
        """
        Haberler arasındaki etkileşim skorlarını hesaplar ve veritabanına kaydeder.
        
        Args:
            news_list: İşlenecek haberler listesi
        """
        start_time = time.time()
        
        logger.info(f"{len(news_list)} haber için etkileşim skorları hesaplanıyor")
        
        # Haber listesinden indeks oluştur (ID -> haber sözlüğü)
        news_dict = {news['id']: news for news in news_list}
        
        # Aday çiftleri bul
        candidate_pairs = self._find_candidate_pairs(news_list)
        
        if not candidate_pairs:
            logger.warning("Etkileşim için uygun aday çift bulunamadı")
            return
        
        # Her çift için skorları hesapla
        edge_records = []
        skipped_count = 0
        
        for source_id, target_id in candidate_pairs:
            # Haberleri bul
            source_news = news_dict.get(source_id)
            target_news = news_dict.get(target_id)
            
            if not source_news or not target_news:
                skipped_count += 1
                continue
            
            # Skorları hesapla
            semantic_score = self._calculate_semantic_score(source_news, target_news)
            entity_score = self._calculate_entity_score(source_news, target_news)
            temporal_score = self._calculate_temporal_score(source_news, target_news)
            
            # Toplam skoru ağırlıklı ortalama ile hesapla
            total_score = (
                self.semantic_weight * semantic_score +
                self.entity_weight * entity_score +
                self.temporal_weight * temporal_score
            )
            
            # Eşik değerini geçenleri kaydet
            if total_score >= self.interaction_threshold:
                edge_records.append({
                    'source_news_id': source_id,
                    'target_news_id': target_id,
                    'semantic_score': float(semantic_score),
                    'entity_score': float(entity_score),
                    'temporal_score': float(temporal_score),
                    'total_score': float(total_score)
                })
        
        # Veritabanına toplu olarak kaydet
        if edge_records:
            self.persistence_manager.save_graph_edges(edge_records)
            logger.info(f"{len(edge_records)} kenar kaydedildi (toplam çift: {len(candidate_pairs)}, "
                      f"atlanan: {skipped_count}, işlem süresi: {time.time() - start_time:.2f}s)")
        else:
            logger.warning("Eşik değerini geçen etkileşim bulunamadı")
