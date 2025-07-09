#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
from urllib.parse import urlparse
import yaml
from pathlib import Path
import sys

# Core modülüne erişim için path ekleme
sys.path.append(str(Path(__file__).parent.parent))

# Core config'den settings import et
try:
    from src.core.config import settings
    logger = logging.getLogger(__name__)
    logger.info("Settings modülü başarıyla import edildi.")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Settings modülü import edilemedi: {e}")
    raise ImportError(f"Settings modülü bulunamadı. Hata: {e}")

class NewsFetcher:
    """
    Kural tabanlı hibrit NewsFetcher modülü.
    
    NewsData.io (birincil) ve Finnhub (ikincil) API'lerinden finansal haberleri 
    fetching_rules.yaml dosyasında tanımlanan kurallara göre çeker.
    """
    
    def __init__(
            self, 
            newsdata_api_key: Optional[str] = None,
            finnhub_api_key: Optional[str] = None,
            language: str = "en",
            countries: List[str] = None
        ):
        """
        NewsFetcher sınıfı başlatıcısı.
        
        Args:
            newsdata_api_key: NewsData.io API anahtarı (opsiyonel, verilmezse settings'ten alınır)
            finnhub_api_key: Finnhub API anahtarı (opsiyonel, verilmezse settings'ten alınır)
            language: Haberlerin dili (varsayılan "en" - İngilizce)
            countries: Ülke kodları (us, gb, vb.)
        """
        # API anahtarlarını al - önce parametre olarak verilenleri kontrol et, yoksa settings'ten al
        self.newsdata_api_key = newsdata_api_key or settings.NEWSDATA_API_KEY
        self.finnhub_api_key = finnhub_api_key or settings.FINNHUB_API_KEY
        
        # API anahtarlarının boş olmadığından emin ol
        if not self.newsdata_api_key:
            raise ValueError("NewsData.io API anahtarı bulunamadı. Lütfen ayarlar dosyasına ekleyin veya parametre olarak verin.")
        if not self.finnhub_api_key:
            raise ValueError("Finnhub API anahtarı bulunamadı. Lütfen ayarlar dosyasına ekleyin veya parametre olarak verin.")
        
        self.language = language
        self.countries = countries or ["us", "gb", "eu"]
        
        self.newsdata_base_url = "https://newsdata.io/api/1/news"
        self.finnhub_base_url = "https://finnhub.io/api/v1/news"
        
        # Kural dosyasını yükle
        rules_path = Path(__file__).parent.parent / "rules" / "fetching_rules.yaml"
        try:
            with open(rules_path, 'r') as file:
                self.rules = yaml.safe_load(file)
            logger.info(f"Kural dosyası başarıyla yüklendi: {rules_path}")
        except Exception as e:
            logger.error(f"Kural dosyası yüklenirken hata: {e}")
            self.rules = {
                "finnhub": {"market_news": {"categories": ["general"]}},
                "newsdata": {
                    "category_queries": [{"category": "business", "keywords": ["market"]}],
                    "general_keyword_sweep": {"keywords": ["stock market", "inflation"]}
                }
            }
    
    def fetch_from_newsdata(self, category: Optional[str] = None, q: Optional[str] = None, days_back: int = 1, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        NewsData.io API'sinden haberleri belirli bir kategori ve anahtar kelime sorgusuyla çeker.
        
        Args:
            category: Haber kategorisi (business, politics, technology vb.) veya None
            q: Aranacak anahtar kelimeler ('kelime1 OR kelime2 OR kelime3' formatında)
            days_back: Kaç gün öncesine ait haberlerin çekileceği
            max_results: Maksimum sonuç sayısı
            
        Returns:
            Standart formatta haberler listesi
        """
        logger.info(f"Fetching news from NewsData.io - Category: {category}, Query: {q}")
        
        # Tarih parametrelerini hazırla
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # API parametrelerini hazırla
        params = {
            'apikey': self.newsdata_api_key,
            'country': ','.join(self.countries),
            'language': self.language,
            'from_date': from_date,
        }
        
        # Kategori varsa ekle
        if category:
            params['category'] = category
            
        # Sorgu string'i varsa ekle
        if q:
            params['q'] = q
        
        try:
            response = requests.get(self.newsdata_base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'success':
                logger.error(f"NewsData.io API error: {data.get('message', 'Unknown error')}")
                return []
            
            results = data.get('results', [])
            
            # Sonuçları standart formata dönüştür
            standardized_news = []
            for article in results[:max_results]:
                if not article.get('url') and not article.get('link'):
                    continue
                    
                news_item = {
                    "url": article.get('link') or article.get('url'),
                    "title": article.get('title', ''),
                    "publication_date": article.get('pubDate', ''),
                    "source": article.get('source_id', '') or self._extract_domain(article.get('link') or article.get('url', ''))
                }
                standardized_news.append(news_item)
            
            logger.info(f"Fetched {len(standardized_news)} news items from NewsData.io")
            return standardized_news
            
        except Exception as e:
            logger.error(f"Error fetching from NewsData.io: {e}")
            return []
    
    def fetch_from_finnhub(self, category: str, days_back: int = 1, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Finnhub API'sinden haberleri belirli bir kategoriyle çeker.
        
        Args:
            category: Haber kategorisi (general, forex, crypto, merger)
            days_back: Kaç gün öncesine ait haberlerin çekileceği
            max_results: Maksimum sonuç sayısı
            
        Returns:
            Standart formatta haberler listesi
        """
        logger.info(f"Fetching news from Finnhub - Category: {category}")
        
        # Tarih parametrelerini hazırla
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # API parametrelerini hazırla
        params = {
            'token': self.finnhub_api_key,
            'category': category,
            'from': from_date,
            'to': to_date
        }
        
        try:
            response = requests.get(f"{self.finnhub_base_url}", params=params)
            response.raise_for_status()
            data = response.json()
            
            # Sonuçları standart formata dönüştür
            standardized_news = []
            for article in data[:max_results]:
                if not article.get('url'):
                    continue
                    
                # Unix timestamp'i datetime'a dönüştür
                timestamp = article.get('datetime')
                if timestamp:
                    publication_date = datetime.fromtimestamp(timestamp).isoformat()
                else:
                    publication_date = ''
                
                news_item = {
                    "url": article.get('url', ''),
                    "title": article.get('headline', ''),
                    "publication_date": publication_date,
                    "source": article.get('source', '') or self._extract_domain(article.get('url', ''))
                }
                standardized_news.append(news_item)
            
            logger.info(f"Fetched {len(standardized_news)} news items from Finnhub - Category: {category}")
            return standardized_news
            
        except Exception as e:
            logger.error(f"Error fetching from Finnhub: {e}")
            return []
    
    def fetchAllSources(self, days_back: int = 1, max_per_source: int = 50) -> List[Dict[str, Any]]:
        """
        Kural dosyasında tanımlanan tüm kategorileri ve anahtar kelimeleri kullanarak tüm kaynaklardan haberleri çeker.
        
        Bu metod, kurallara göre şu sırayla çalışır:
        1. Finnhub'dan market_news kategorilerini çeker
        2. NewsData.io'dan belirli kategoriler ve anahtar kelimeler için sorgu yapar
        3. NewsData.io'dan genel anahtar kelimelerle kategori belirtmeden sorgu yapar
        
        Args:
            days_back: Kaç gün öncesine ait haberlerin çekileceği
            max_per_source: Her bir API çağrısı için maksimum sonuç sayısı
            
        Returns:
            URL bazında tekilleştirilmiş birleştirilmiş haberler listesi
        """
        logger.info("Başlatılıyor: Tüm kaynaklardan haber çekme işlemi (kural tabanlı)")
        all_results = []
        
        # Adım 1: Finnhub'dan market_news kategorilerini çek
        try:
            finnhub_categories = self.rules.get('finnhub', {}).get('market_news', {}).get('categories', [])
            logger.info(f"Finnhub kategorileri: {finnhub_categories}")
            
            for category in finnhub_categories:
                # Her kategori için API çağrısı yap
                finnhub_news = self.fetch_from_finnhub(
                    category=category,
                    days_back=days_back,
                    max_results=max_per_source
                )
                all_results.extend(finnhub_news)
                
                # API hız sınırlamaları için kısa bir bekleme
                time.sleep(1)
        except Exception as e:
            logger.error(f"Finnhub haberlerini çekerken hata: {e}")
        
        # Adım 2: NewsData.io'dan kategorili sorgular yap
        try:
            category_queries = self.rules.get('newsdata', {}).get('category_queries', [])
            logger.info(f"NewsData.io kategori sorguları: {len(category_queries)} adet")
            
            for query_config in category_queries:
                category = query_config.get('category')
                keywords = query_config.get('keywords', [])
                
                if category and keywords:
                    # Anahtar kelimeleri 'OR' ile birleştir
                    query_string = " OR ".join(keywords)
                    
                    # API çağrısı yap
                    newsdata_category_news = self.fetch_from_newsdata(
                        category=category,
                        q=query_string,
                        days_back=days_back,
                        max_results=max_per_source
                    )
                    all_results.extend(newsdata_category_news)
                    
                    # API hız sınırlamaları için kısa bir bekleme
                    time.sleep(1)
        except Exception as e:
            logger.error(f"NewsData.io kategori sorgularını çekerken hata: {e}")
        
        # Adım 3: NewsData.io'dan genel anahtar kelime taraması yap
        try:
            general_keywords = self.rules.get('newsdata', {}).get('general_keyword_sweep', {}).get('keywords', [])
            logger.info(f"NewsData.io genel anahtar kelimeler: {general_keywords}")
            
            if general_keywords:
                # Anahtar kelimeleri 'OR' ile birleştir
                query_string = " OR ".join(general_keywords)
                
                # Kategori belirtmeden API çağrısı yap
                newsdata_general_news = self.fetch_from_newsdata(
                    category=None,
                    q=query_string,
                    days_back=days_back,
                    max_results=max_per_source
                )
                all_results.extend(newsdata_general_news)
        except Exception as e:
            logger.error(f"NewsData.io genel anahtar kelime taraması yaparken hata: {e}")
        
        # URL bazında tekilleştir
        unique_results = self._deduplicate_by_url(all_results)
        
        logger.info(f"Toplam {len(all_results)} haber toplandı, tekilleştirme sonrası {len(unique_results)} haber kaldı")
        return unique_results
    
    def _extract_domain(self, url: str) -> str:
        """
        URL'den alan adını çıkarır.
        
        Args:
            url: İnternet URL'si
            
        Returns:
            Alan adı (örn. "example.com")
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            return domain
        except:
            return url
    
    def _deduplicate_by_url(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Haberleri URL bazında tekilleştirir.
        
        Args:
            news_list: Haberler listesi
            
        Returns:
            Tekilleştirilmiş haberler listesi
        """
        unique_urls = set()
        unique_news = []
        
        for news in news_list:
            url = news.get('url')
            if url and url not in unique_urls:
                unique_urls.add(url)
                unique_news.append(news)
        
        return unique_news


if __name__ == "__main__":
    # Test amaçlı basit kullanım örneği
    import time
    import sys
    
    # Loglama seviyesini ayarla
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        # NewsFetcher örneğini oluştur (Artık API anahtarları settings'ten alınıyor)
        print("Kural tabanlı NewsFetcher başlatılıyor...")
        fetcher = NewsFetcher()
        
        # Haberleri çek
        print("\nTüm kaynaklardan haberleri çekme işlemi başlatılıyor...")
        start_time = time.time()
        news = fetcher.fetchAllSources(days_back=1)
        end_time = time.time()
        
        # Sonuçları göster
        print(f"\nToplam {len(news)} tekil haber çekildi ({end_time - start_time:.2f} saniyede)")
        print("\nÖrnek haberler:")
        for idx, item in enumerate(news[:5]):
            print(f"\n{idx+1}. {item['title']}")
            print(f"   Kaynak: {item['source']}")
            print(f"   Tarih: {item['publication_date']}")
            print(f"   URL: {item['url']}")
    except Exception as e:
        print(f"Hata: {e}")
        sys.exit(1)
