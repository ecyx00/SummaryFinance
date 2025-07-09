"""
Event Type Classification Module

Bu modül, haber metinlerini önceden tanımlanmış finansal olay türlerine göre 
otomatik olarak etiketleyen EventTypeClassifier sınıfını içerir.
"""

import os
import logging
import yaml
from typing import Dict, List, Optional, Any

# Logger yapılandırması
logger = logging.getLogger(__name__)


class EventTypeClassifier:
    """
    Haber metinlerini olay türlerine göre sınıflandıran sınıf.

    Bu sınıf, bir YAML dosyasından olay türleri ve bunları tetikleyen anahtar kelime/varlık 
    listelerini yükler ve bir metin ve varlıklar sözlüğüne göre olay türünü belirler.
    Genişletilmiş yapı ile birlikte öncelik (priority) ve gerekçe (rationale) bilgilerini de işler.
    """

    def __init__(self, rules_path: str = None):
        """
        EventTypeClassifier sınıfını başlatır.
        
        Args:
            rules_path: Olay türü kurallarını içeren YAML dosyasının yolu.
                       None ise varsayılan konum kullanılır.
        """
        logger.info("EventTypeClassifier başlatılıyor...")

        # Eğer özel bir dosya yolu belirtilmemişse varsayılan konumu kullan
        if not rules_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rules_path = os.path.join(base_dir, "rules", "event_rules.yaml")
        
        try:
            # YAML dosyasını yükle
            logger.info(f"Olay türü kuralları yükleniyor: {rules_path}")
            with open(rules_path, 'r', encoding='utf-8') as file:
                rules_data = yaml.safe_load(file)
            
            # Kuralları sınıf değişkenine kaydet ve önceliğe göre sırala
            self.rules = rules_data.get('events', [])
            
            # Öncelik bilgisini loglama
            priority_counts = {}
            for rule in self.rules:
                priority = rule.get('priority', 999)
                event_type = rule.get('event_type')
                if priority not in priority_counts:
                    priority_counts[priority] = 0
                priority_counts[priority] += 1
                
            priority_info = ', '.join([f"P{p}: {c} kural" for p, c in sorted(priority_counts.items())])
            logger.info(f"{len(self.rules)} olay türü kuralı başarıyla yüklendi ({priority_info})")
        
        except Exception as e:
            logger.error(f"Olay türü kuralları yüklenirken hata oluştu: {e}")
            self.rules = []

    def classify(self, text: str, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Bir haber metnini ve varlıkları analiz ederek olay türünü belirler.
        
        Args:
            text: Haber metni
            entities: FeatureExtractor'dan gelen varlıklar sözlüğü
                     Örn: {'ORG': ['Federal Reserve', 'ECB'], 'GPE': ['USA', 'EU']}
        
        Returns:
            Dict[str, Any]: Eşleşen olay türü bilgilerini içeren sözlük veya None (eşleşme bulunamazsa)
                            {'event_type': str, 'description': str, 'priority': int, 'rationale': str}
        """
        if not text or not self.rules:
            logger.warning("Sınıflandırma yapılamıyor: Metin veya kurallar boş")
            return None
        
        # Metni küçük harfe çevir (arama için)
        text_lower = text.lower()
        
        # En yüksek öncelikli (düşük priority değeri) eşleşmeleri bulmak için
        matching_rules = []
        
        # Her bir olay türü kuralını kontrol et
        for rule in self.rules:
            event_type = rule.get('event_type')
            priority = rule.get('priority', 999)  # Öncelik belirtilmemişse en düşük önceliği ver
            
            # 1. Anahtar kelime kontrolü
            keywords = rule.get('keywords', [])
            for keyword in keywords:
                # Anahtar kelimelerde liste içindeki elemanlar veya doğrudan string olabilir
                keyword_str = keyword.lower() if isinstance(keyword, str) else keyword.lower()
                if keyword_str in text_lower:
                    logger.info(f"Olay türü belirlendi: {event_type} (anahtar kelime: {keyword_str})")
                    matching_rules.append({
                        'rule': rule,
                        'match_type': 'keyword',
                        'match_value': keyword_str,
                        'priority': priority
                    })
            
            # 2. Varlık kontrolü
            rule_entities = rule.get('entities', {})
            if entities and rule_entities:
                for entity_type, entity_values in rule_entities.items():
                    # Metinde bulunan varlık türü kuralda var mı?
                    if entity_type in entities:
                        # Metin varlıkları ile kural varlıkları arasında eşleşme var mı?
                        for entity in entities[entity_type]:
                            # Her bir varlık adını kuralda belirtilen varlık değerleriyle karşılaştır
                            for rule_entity in entity_values:
                                if rule_entity.lower() in entity.lower():
                                    logger.info(f"Olay türü belirlendi: {event_type} (varlık: {entity}, tür: {entity_type})")
                                    matching_rules.append({
                                        'rule': rule,
                                        'match_type': 'entity',
                                        'match_value': entity,
                                        'entity_type': entity_type,
                                        'priority': priority
                                    })
        
        # Eşleşme bulunamazsa
        if not matching_rules:
            logger.info("Metin için olay türü belirlenemedi")
            return None
            
        # En yüksek öncelikli (düşük priority değeri) kuralı bul
        best_match = min(matching_rules, key=lambda x: x['priority'])
        rule = best_match['rule']
        
        # Eşleşen kuraldan olay bilgilerini oluştur
        event_info = {
            'event_type': rule.get('event_type'),
            'description': rule.get('description', ''),
            'priority': rule.get('priority', 999),
            'rationale': rule.get('rationale', '')
        }
        
        logger.info(f"Seçilen olay türü: {event_info['event_type']} (öncelik: {event_info['priority']})")
        return event_info
