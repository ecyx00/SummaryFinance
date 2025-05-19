import logging
import httpx
from typing import Dict, Optional, List, Any
from pprint import pformat

# Logger oluştur
logger = logging.getLogger(__name__)


async def send_results_to_spring_boot(payload: Dict[str, Any], spring_boot_submit_url: str) -> bool:
    """
    Analiz sonuçlarını Spring Boot backend'ine gönderir.
    
    Args:
        payload: Gönderilecek veri, iki anahtar içermeli:
                - analyzed_stories: List[Dict] - Analiz edilmiş hikayeler listesi
                - ungrouped_news_ids: List[str] - Herhangi bir gruba dahil edilemeyen haber ID'leri listesi
        spring_boot_submit_url: Spring Boot API endpoint URL'i
        
    Returns:
        Gönderme başarılıysa True, başarısızsa False
    """
    # Payload özeti hazırlama
    analyzed_count = len(payload.get('analyzed_stories', []))
    ungrouped_count = len(payload.get('ungrouped_news_ids', []))
    
    # İlk 3 analiz edilmiş hikayenin başlıklarını logla
    story_previews = []
    for idx, story in enumerate(payload.get('analyzed_stories', [])):
        if idx >= 3:  # Sadece ilk 3 hikayeyi göster
            break
        title = story.get('story_title', 'Başlık bulunamadı')
        categories = story.get('main_categories', [])
        story_previews.append(f"{title} (Kategoriler: {', '.join(categories)})")
    
    # Detaylı loglama
    logger.info(f"Analiz sonuçları Spring Boot'a gönderiliyor: {spring_boot_submit_url}")
    logger.info(f"Payload Özeti: {analyzed_count} analiz edilmiş hikaye, {ungrouped_count} gruplanamayan haber ID'si")
    
    if story_previews:
        logger.info("Gönderilecek analiz örnekleri:")
        for idx, preview in enumerate(story_previews):
            logger.info(f"  {idx+1}. {preview}")
    
    # HTTP headers
    headers = {"Content-Type": "application/json"}
    
    try:
        # Asenkron HTTP client'ı async with kullanarak oluştur (otomatik kapatma için)
        # Bağlantı sorunlarını daha iyi yönetmek için yeniden deneme ve timeout ayarları
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),  # Bağlantı kurma için 10 saniye, toplam 30 saniye
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            transport=httpx.AsyncHTTPTransport(retries=3)  # Bağlantı hatalarında 3 kez yeniden deneme
        ) as client:
            logger.info(f"Spring Boot servisine bağlantı kurulmaya çalışılıyor: {spring_boot_submit_url}")
            # POST isteğini gönder
            response = await client.post(
                spring_boot_submit_url,
                json=payload,
                headers=headers
            )
            
            # HTTP hata kodlarını kontrol et
            response.raise_for_status()
            
            # Yanıtı işle
            status_code = response.status_code
            
            try:
                response_body = response.json()
                response_summary = pformat(response_body) if response_body else "(Boş yanıt gövdesi)"
            except Exception as e:
                # JSON parse hatası durumunda
                response_summary = f"(JSON olarak parse edilemedi: {str(e)})"
                response_body = response.text
            
            if 200 <= status_code < 300:  # Başarılı yanıtlar
                logger.info(f"Spring Boot'a gönderme başarılı. Durum kodu: {status_code}")
                logger.info(f"Spring Boot yanıtı: {response_summary}")
                return True
            else:  # Beklenmeyen başarısız yanıt (raise_for_status'ten kaçmış olabilir)
                logger.error(f"Spring Boot'a gönderme başarısız. Durum kodu: {status_code}")
                logger.error(f"Spring Boot yanıtı: {response_summary}")
                return False
                
    except httpx.HTTPStatusError as http_err:
        # HTTP hata kodları için (4xx, 5xx)
        logger.error(f"Spring Boot'a gönderme sırasında HTTP hatası: {http_err}")
        return False
        
    except httpx.RequestError as req_err:
        # Bağlantı hataları, timeout vs.
        logger.error(f"Spring Boot'a gönderme sırasında istek hatası: {req_err}")
        if "connection" in str(req_err).lower():
            logger.error("Bağlantı hatası! Spring Boot servisinin çalıştığından emin olun (http://localhost:8888).")
            logger.error("Spring Boot uygulamaması çalışmıyorsa, 'mvn spring-boot:run' komutuyla başlatmanız gerekebilir.")
        elif "timeout" in str(req_err).lower():
            logger.error("Bağlantı zaman aşımına uğradı! Spring Boot servisinin yanıt verme süresi çok uzun.")
        return False
        
    except Exception as e:
        # Diğer tüm hatalar
        logger.error(f"Spring Boot'a gönderme sırasında beklenmeyen hata: {str(e)}")
        return False
