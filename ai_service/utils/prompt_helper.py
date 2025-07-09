"""
Prompt Helper Module

Bu modül, prompt dosyalarının yüklenmesi ve işlenmesi için yardımcı fonksiyonlar içerir.
"""

import os
import logging
from pathlib import Path
from typing import Optional

# Logger yapılandırması
logger = logging.getLogger(__name__)

def get_prompt_path(prompt_relative_path: str) -> str:
    """
    Prompt dosyası için tam dosya yolunu döndürür.
    
    Verilen göreceli yolu kullanarak, projenin prompts klasöründeki
    dosyaların tam yolunu oluşturur.
    
    Args:
        prompt_relative_path: Prompt dosyasının prompts klasörüne göre göreceli yolu
            (örn. "labeling/v1.0.txt" veya "continuity/v1.0.txt")
            
    Returns:
        str: Prompt dosyasının tam yolu
        
    Raises:
        FileNotFoundError: Eğer dosya bulunamazsa
    """
    try:
        # AI service kök dizinini bul
        base_dir = Path(__file__).parent.parent
        
        # Prompt dosyasının tam yolunu oluştur
        prompt_path = base_dir / "prompts" / prompt_relative_path
        
        # Dosyanın varlığını kontrol et
        if not prompt_path.exists():
            logger.error(f"Prompt dosyası bulunamadı: {prompt_path}")
            raise FileNotFoundError(f"Prompt dosyası bulunamadı: {prompt_path}")
        
        logger.debug(f"Prompt dosyası bulundu: {prompt_path}")
        return str(prompt_path)
        
    except Exception as e:
        logger.error(f"Prompt dosyası yolu oluştururken hata: {e}")
        raise
