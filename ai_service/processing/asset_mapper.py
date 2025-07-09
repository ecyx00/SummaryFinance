"""
Asset Mapper Module

Bu modül, haber metinlerinde tespit edilen varlıkları (entities) kullanarak
potansiyel olarak etkilenebilecek finansal enstrümanları (assets) eşleştiren
AssetMapper sınıfını içerir.
"""

import os
import logging
import yaml
from typing import Dict, List, Set, Any, Optional

# Logger yapılandırması
logger = logging.getLogger(__name__)


class AssetMapper:
    """
    Varlıklar (entities) ve finansal enstrümanlar (assets) arasında eşleştirme yapan sınıf.

    Bu sınıf, bir YAML dosyasından varlık-enstrüman eşleştirme kurallarını yükler ve
    FeatureExtractor'dan gelen varlık listesini kullanarak potansiyel olarak etkilenebilecek
    finansal enstrümanların bir listesini oluşturur.
    """

    def __init__(self, rules_path: str = None):
        """
        AssetMapper sınıfını başlatır.
        
        Args:
            rules_path: Varlık-enstrüman eşleştirme kurallarını içeren YAML dosyasının yolu.
                       None ise varsayılan konum kullanılır.
        """
        logger.info("AssetMapper başlatılıyor...")

        # Eğer özel bir dosya yolu belirtilmemişse varsayılan konumu kullan
        if not rules_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rules_path = os.path.join(base_dir, "rules", "asset_rules.yaml")
        
        try:
            # YAML dosyasını yükle
            logger.info(f"Varlık-enstrüman eşleştirme kuralları yükleniyor: {rules_path}")
            with open(rules_path, 'r', encoding='utf-8') as file:
                rules_data = yaml.safe_load(file)
            
            # Kuralları sınıf değişkenine kaydet
            self.mappings = rules_data.get('mappings', [])
            
            # İstatistiksel bilgi
            entity_types = set()
            entity_count = 0
            asset_count = 0
            
            for mapping in self.mappings:
                entity_types.add(mapping.get('entity_type', ''))
                entity_count += len(mapping.get('entity_names', []))
                asset_count += len(mapping.get('assets', []))
            
            logger.info(f"{len(self.mappings)} eşleştirme kuralı yüklendi")
            logger.info(f"Toplam {len(entity_types)} varlık türü, {entity_count} varlık adı ve {asset_count} finansal enstrüman tanımlandı")
        
        except Exception as e:
            logger.error(f"Varlık-enstrüman eşleştirme kuralları yüklenirken hata oluştu: {e}")
            self.mappings = []

    def map_assets(self, entities: Dict[str, List[str]]) -> List[str]:
        """
        Bir haber metninden çıkarılan varlıkları (entities) kullanarak potansiyel olarak 
        etkilenebilecek finansal enstrümanların (assets) listesini oluşturur.
        
        Args:
            entities: FeatureExtractor'dan gelen varlıklar sözlüğü
                     Örn: {'ORG': ['Federal Reserve', 'ECB'], 'GPE': ['USA', 'EU']}
        
        Returns:
            List[str]: Eşleştirilen finansal enstrümanların (assets) listesi
        """
        if not entities or not self.mappings:
            logger.warning("Varlık eşleştirmesi yapılamıyor: Varlıklar veya kurallar boş")
            return []
        
        # Eşleşen varlıkları ve finansal enstrümanları kaydetmek için kümeler kullan
        candidate_assets: Set[str] = set()
        matched_entities: List[str] = []
        
        # Her bir eşleştirme kuralını kontrol et
        for mapping in self.mappings:
            entity_type = mapping.get('entity_type')
            entity_names = mapping.get('entity_names', [])
            assets = mapping.get('assets', [])
            
            # Eğer varlık türü (ORG, GPE, vb.) metinde varsa
            if entity_type in entities:
                # Metindeki bu türdeki her bir varlığı kontrol et
                for entity in entities[entity_type]:
                    # Kural listesindeki her bir varlık adıyla karşılaştır
                    for rule_entity in entity_names:
                        # Tam eşleşme veya alt dize olarak içerme kontrolü
                        if (rule_entity.lower() == entity.lower() or 
                            rule_entity.lower() in entity.lower() or 
                            entity.lower() in rule_entity.lower()):
                            
                            # Eşleşme bulundu, finansal enstrümanları listeye ekle
                            candidate_assets.update(assets)
                            matched_entities.append(f"{entity} ({entity_type})")
                            
                            # Eşleşme bilgisini logla
                            logger.debug(f"Eşleşme: '{entity}' -> {assets}")
                            break  # Bir eşleşme bulunduğunda sonraki rule_entity'e geçme
        
        # Sonuçları logla
        if candidate_assets:
            logger.info(f"{len(matched_entities)} varlık eşleşti: {', '.join(matched_entities)}")
            logger.info(f"{len(candidate_assets)} aday finansal enstrüman bulundu: {', '.join(sorted(candidate_assets))}")
        else:
            logger.info("Hiçbir finansal enstrüman eşleşmesi bulunamadı")
        
        return sorted(list(candidate_assets))  # Kümeyi sıralı listeye dönüştür
