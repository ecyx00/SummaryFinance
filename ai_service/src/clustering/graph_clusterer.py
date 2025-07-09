#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GraphClusterer Module

Bu modül, etkileşim skorlarını kullanarak graf oluşturur ve 
topluluk tespit algoritmaları uygulayarak aday hikaye kümeleri oluşturur.
"""

import logging
import time
from typing import List, Dict, Any, Set
from datetime import datetime, date
import networkx as nx
import community as community_louvain

from ..db.persistence_manager import PersistenceManager
from ..core.config import settings

logger = logging.getLogger(__name__)


class GraphClusterer:
    """
    Etkileşim skorlarını kullanarak graf kümeleme yapan sınıf.
    
    Bu sınıf, graph_edges tablosundaki etkileşim skorlarını kullanarak bir graf modeli oluşturur
    ve bu graf üzerinde Louvain topluluk saptama algoritması uygulayarak olası haber kümelerini tespit eder.
    """
    
    def __init__(self, persistence_manager: PersistenceManager = None, run_date: date = None):
        """
        GraphClusterer sınıfının başlatıcısı.
        
        Args:
            persistence_manager: Veritabanı işlemleri için PersistenceManager nesnesi
            run_date: Kümeleme için kullanılacak tarih (None ise bugünün tarihi kullanılır)
        """
        self.persistence_manager = persistence_manager or PersistenceManager()
        self.run_date = run_date or datetime.now().date()
        self.interaction_threshold = settings.INTERACTION_THRESHOLD
        
    def _fetch_edges(self) -> List[Dict]:
        """
        Veritabanından belirtilen tarih için eşik değerini aşan tüm etkileşim kenarlarını çeker.
        
        Returns:
            List[Dict]: Her kenar için source_news_id, target_news_id ve total_interaction_score içeren sözlüklerden oluşan liste
        """
        try:
            logger.info(f"{self.run_date} tarihli, {self.interaction_threshold} eşik değerini aşan kenarlar alınıyor...")
            edges = self.persistence_manager.fetch_graph_edges(
                run_date=self.run_date,
                interaction_threshold=self.interaction_threshold
            )
            logger.info(f"Toplam {len(edges)} adet kenar alındı.")
            return edges
        except Exception as e:
            logger.error(f"Kenarları alırken hata: {e}")
            raise
    
    def cluster_stories(self) -> List[List[int]]:
        """
        Graph_edges tablosundaki etkileşim skorlarını kullanarak aday hikaye kümeleri oluşturur.
        
        Returns:
            List[List[int]]: Her biri birbiriyle ilişkili haberlerin ID'lerinden oluşan küme listesi
        """
        start_time = time.time()
        logger.info("Aday hikaye kümeleri tespit ediliyor...")
        
        try:
            # 1. Kenarları veritabanından al
            edges = self._fetch_edges()
            if not edges:
                logger.warning("Eşik değerini aşan kenar bulunamadı. Kümeleme yapılamıyor.")
                return []
                
            # 2. NetworkX graf nesnesi oluştur
            G = nx.Graph()
            
            # 3. Kenarları grafa ekle - weighted_edges için (source, target, weight) formatında
            weighted_edges = [
                (edge["source_news_id"], edge["target_news_id"], edge["total_interaction_score"])
                for edge in edges
            ]
            G.add_weighted_edges_from(weighted_edges)
            
            logger.info(f"Graf oluşturuldu: {len(G.nodes())} düğüm, {len(G.edges())} kenar")
            
            # 4. Louvain algoritmasıyla topluluk tespiti
            partition = community_louvain.best_partition(G, weight='weight')
            
            # 5. Toplulukları düzenle ve kümeleri oluştur
            # {community_id: [node_id1, node_id2, ...]} formatına dönüştür
            communities = {}
            for node, community_id in partition.items():
                if community_id not in communities:
                    communities[community_id] = []
                communities[community_id].append(node)
            
            # 6. En az 2 haber içeren kümeleri filtrele
            story_clusters = [nodes for nodes in communities.values() if len(nodes) >= 2]
            
            # İşlem süresi ve sonuçları raporla
            duration = time.time() - start_time
            logger.info(f"Kümeleme tamamlandı: {len(story_clusters)} aday küme bulundu. " 
                       f"Süre: {duration:.2f}s")
            
            # İlk birkaç kümenin içeriğini loglama
            for i, cluster in enumerate(story_clusters[:3], 1):
                logger.info(f"Örnek Küme #{i}: {cluster}")
            
            return story_clusters
            
        except Exception as e:
            logger.error(f"Kümeleme sırasında hata: {e}")
            raise
