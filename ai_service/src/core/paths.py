#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Path Utilities Module

Bu modül, proje genelinde kullanılacak dosya yolu yardımcı fonksiyonlarını içerir.
"""

from pathlib import Path

# Proje kök dizini (bir kez hesaplanır)
# Burada __file__, bu dosyanın yoludur: src/core/paths.py
# parent.parent ile iki seviye yukarı çıkarak proje kökünü buluruz
PROJECT_ROOT = Path(__file__).parent.parent.parent

def get_project_root() -> Path:
    """
    Proje kök dizinini döndürür.
    
    Returns:
        Path: Proje kök dizinin Path nesnesi
    """
    return PROJECT_ROOT

def get_prompt_path(prompt_type: str, version: str) -> Path:
    """
    Belirtilen prompt türü ve versiyonu için dosya yolunu döndürür.
    
    Args:
        prompt_type: Prompt türü (örn. 'validation', 'labeling', 'justification')
        version: Prompt versiyonu (örn. 'v1.0', 'v1.1')
        
    Returns:
        Path: Prompt dosyasının tam yolu
    """
    return PROJECT_ROOT / "prompts" / prompt_type / f"{version}.txt"
