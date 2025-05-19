import logging
from fastapi import FastAPI, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Set, Optional, Any

# Mutlak import kullanarak
from src.core.logging_config import setup_logging
from src.core.config import settings, DEFAULT_DISCLAIMER
from src.db.database import SessionLocal
from src.processing.data_preparer import prepare_news_for_analysis
from src.processing.gemini_analyzer import group_news_stories_with_gemini, analyze_individual_story_group
from src.processing.result_sender import send_results_to_spring_boot

# Loglama sistemini başlat
setup_logging()

# Logger oluştur
logger = logging.getLogger(__name__)

# FastAPI uygulamasını oluştur
app = FastAPI(title="AI Servisi", description="Finans haberleri analiz servisi")

@app.on_event("startup")
async def startup_event():
    """Uygulama başladığında çalışacak fonksiyon."""
    logger.info("AI Servisi Başlatılıyor...")
    logger.info(f"Veritabanı kullanıcısı: {settings.POSTGRES_USER}")
    logger.info(f"Veritabanı: {settings.POSTGRES_DB}")
    logger.info(f"Haber parti boyutu: {settings.NEWS_BATCH_SIZE}")
    logger.info(f"Log seviyesi: {settings.LOG_LEVEL}")
    logger.info(f"Spring Boot submit URL: {settings.SPRING_BOOT_SUBMIT_URL}")
    logger.info(f"Gemini API kullanılıyor: {'EVET' if settings.GEMINI_API_KEY else 'HAYIR - API KEY EKSIK!'}")
    logger.info(f"Gemini Model: {settings.GEMINI_MODEL_NAME}")

@app.get("/")
async def root():
    """Kök endpoint."""
    logger.info("Kök endpoint çağrıldı")
    return {"message": "AI Servisi Çalışıyor"}

async def analysis_process_background():
    """Analiz sürecini arka planda çalıştıracak fonksiyon."""
    logger.info("Arka plan analiz süreci başlatıldı.")
    
    # Veritabanı oturumu oluştur
    db = SessionLocal()
    try:
        # ADIM 1: Veritabanından veri çek ve scraping yap
        prepared_news_list = prepare_news_for_analysis(db)
        
        if not prepared_news_list:
            logger.info("Analiz edilecek yeni haber bulunamadı veya içerikleri çekilemedi.")
            return
        
        logger.info(f"Toplam {len(prepared_news_list)} adet haber scrape edildi ve Gemini için hazırlandı.")
        
        # İlk birkaç haberin detaylarını logla
        max_preview = min(2, len(prepared_news_list))
        for i in range(max_preview):
            news = prepared_news_list[i]
            logger.info(f"Örnek Haber {i+1}:")
            logger.info(f"  ID: {news['id']}")
            logger.info(f"  Başlık: {news['title']}")
            # Eğer extracted_keywords varsa göster
            if 'extracted_keywords' in news and news['extracted_keywords']:
                logger.info(f"  Anahtar Kelimeler: {', '.join(news['extracted_keywords'][:5])}" + 
                          ("..." if len(news['extracted_keywords']) > 5 else ""))
            # İçeriğin ilk 200 karakterini göster
            content_preview = news['content'][:200] + "..." if len(news['content']) > 200 else news['content']
            logger.info(f"  İçerik Önizleme: {content_preview}")
        
        # ADIM 2: Gemini ile haberleri gruplandır (Aşama 1 - Gruplama)
        logger.info("Gemini Aşama 1 (Gruplama) başlatılıyor...")
        
        # Gemini API anahtarını al
        gemini_api_key = settings.GEMINI_API_KEY
        if not gemini_api_key:
            logger.error("GEMINI_API_KEY ayarlanmamış. Lütfen .env dosyanızı kontrol edin.")
            return
        
        # Haberleri gruplandır
        grouped_stories_info = group_news_stories_with_gemini(
            news_batch_to_group=prepared_news_list,
            api_key=gemini_api_key
        )
        
        # Gruplandırma sonuçlarını işle
        if grouped_stories_info and len(grouped_stories_info) > 0:
            logger.info(f"Gemini Aşama 1 (Gruplama) başarılı. {len(grouped_stories_info)} adet grup bulundu.")
            
            # Her bir grubun detaylarını logla
            for idx, group in enumerate(grouped_stories_info):
                group_label = group.get('group_label', 'Bilinmeyen Grup')
                related_ids = group.get('related_news_ids', [])
                
                logger.info(f"Grup {idx+1}: {group_label}")
                logger.info(f"  İçerdiği Haber Sayısı: {len(related_ids)}")
                logger.info(f"  Haber ID'leri: {', '.join(related_ids)}")
                
                # Gruba dahil edilen haberlerin başlıklarını da göster
                if len(related_ids) > 0:
                    related_titles = []
                    for news_id in related_ids:
                        # prepared_news_list içinde bu ID'yi ara
                        for news in prepared_news_list:
                            if news['id'] == news_id:
                                related_titles.append(news['title'])
                                break
                    
                    if related_titles:
                        logger.info(f"  Haber Başlıkları:")
                        for title_idx, title in enumerate(related_titles):
                            logger.info(f"    {title_idx+1}. {title}")
            
            # Aşama 2 (Detaylı Analiz) - Her grup için detaylı analiz yap
            logger.info("Aşama 2'ye (Detaylı Analiz) geçiliyor...")
            
            # Başarılı analizleri tutacak liste
            final_analyzed_stories: List[Dict] = []
            
            # Herhangi bir gruba dahil edilen tüm haber ID'lerini takip et
            processed_news_ids_in_groups: Set[str] = set()
            
            # Her grup için Aşama 2 analizini yap
            for idx, group_info in enumerate(grouped_stories_info):
                group_label = group_info.get("group_label", "Bilinmeyen Grup")
                related_ids = group_info.get("related_news_ids", [])
                
                # Eğer grup boşsa atla
                if not related_ids:
                    logger.warning(f"Grup {idx+1}: '{group_label}' için haber ID'leri bulunamadı, atlanıyor.")
                    continue
                
                # İkinci prompt için veri hazırla: bu gruptaki haberlerin detaylarını topla
                current_group_news_details: List[Dict] = []
                for news_id in related_ids:
                    for news in prepared_news_list:
                        if news['id'] == news_id:
                            # Yalnızca analize gereken alanları ekle
                            current_group_news_details.append({
                                'id': news['id'],
                                'title': news['title'],
                                'extracted_keywords': news.get('extracted_keywords', []),
                                'content': news['content']
                            })
                            break
                
                # Eğer haberler bulunamadıysa atla
                if not current_group_news_details:
                    logger.warning(f"Grup {idx+1}: '{group_label}' için haber detayları bulunamadı, atlanıyor.")
                    continue
                
                logger.info(f"Grup {idx+1}: '{group_label}' için detaylı analiz yapılıyor...")
                
                # Detaylı analizi çağır (Aşama 2)
                analyzed_story_result = analyze_individual_story_group(
                    news_group_details=current_group_news_details,
                    group_label_from_phase1=group_label,
                    api_key=gemini_api_key
                )
                
                # Analiz sonuçlarını kontrol et
                if analyzed_story_result:
                    # Disclaimer'ı analysis_summary'nin sonuna ekle
                    if analyzed_story_result and "analysis_summary" in analyzed_story_result:
                        analyzed_story_result["analysis_summary"] = f"{analyzed_story_result['analysis_summary']}\n\nUYARI: {DEFAULT_DISCLAIMER}"
                    
                    # Zenginleştirilmiş analizi listeye ekle
                    final_analyzed_stories.append(analyzed_story_result)
                    
                    # Bu hikayeye dahil olan haberleri işlenmiş olarak işaretle
                    for news_id in analyzed_story_result.get("related_news_ids", []):
                        processed_news_ids_in_groups.add(news_id)
                    
                    logger.info(f"Grup {idx+1}: '{group_label}' için detaylı analiz başarılı:")
                    logger.info(f"  Hikaye Başlığı: {analyzed_story_result.get('story_title', 'Başlık bulunamadı')}")
                    logger.info(f"  Kategori(ler): {', '.join(analyzed_story_result.get('main_categories', ['Kategori bulunamadı']))}")
                    
                    # Analiz özetinin ilk 200 karakterini göster
                    summary = analyzed_story_result.get('analysis_summary', '')
                    summary_preview = summary[:200] + "..." if len(summary) > 200 else summary
                    logger.info(f"  Analiz Önizleme: {summary_preview}")
                    
                    # Disclaimer'in eklendiğini logla
                    logger.info("  Disclaimer: Analysis summary'in sonuna eklenmiştir")
                else:
                    logger.error(f"Grup {idx+1}: '{group_label}' için detaylı analiz başarısız oldu.")
            
            # Gruplandırılamayan haberleri belirle
            all_scraped_ids = {news["id"] for news in prepared_news_list}
            ungrouped_ids = list(all_scraped_ids - processed_news_ids_in_groups)
            
            # Sonuçları logla
            logger.info(f"Analiz tamamlandı: {len(final_analyzed_stories)} grup başarıyla analiz edildi.")
            logger.info(f"Gruplara dahil edilemeyen haber sayısı: {len(ungrouped_ids)}")
            
            if ungrouped_ids:
                logger.info(f"Gruplanamayan haber ID'leri: {', '.join(ungrouped_ids)}")
                
                # İlk birkaç gruplanamayan haberin başlıklarını göster
                max_ungrouped_preview = min(3, len(ungrouped_ids))
                logger.info("Gruplanamayan haberlerin örnekleri:")
                preview_count = 0
                
                for news in prepared_news_list:
                    if news["id"] in ungrouped_ids:
                        logger.info(f"  - {news['title']}")
                        preview_count += 1
                        if preview_count >= max_ungrouped_preview:
                            break
            
            # Sonuçları Spring Boot'a gönder
            logger.info(f"Analiz sonuçları hazır: {len(final_analyzed_stories)} grup, {len(ungrouped_ids)} gruplanamayan haber.")
            
            # Payload'u hazırla
            payload: Dict[str, Any] = {
                "analyzed_stories": final_analyzed_stories,
                "ungrouped_news_ids": ungrouped_ids
            }
            
            # Spring Boot'a gönder
            if settings.SPRING_BOOT_SUBMIT_URL:
                send_result = await send_results_to_spring_boot(
                    payload=payload,
                    spring_boot_submit_url=settings.SPRING_BOOT_SUBMIT_URL
                )
                
                if send_result:
                    logger.info("Analiz sonuçları Spring Boot'a başarıyla gönderildi.")
                else:
                    logger.error("Analiz sonuçları Spring Boot'a gönderilemedi.")
            else:
                logger.warning("SPRING_BOOT_SUBMIT_URL ayarlanmamış, sonuçlar gönderilemedi.")
        else:
            logger.error("Gemini Aşama 1 (Gruplama) başarısız oldu veya hiç grup bulunamadı.")
    
    finally:
        # Veritabanı oturumunu kapat
        db.close()
    
    logger.info("Arka plan analiz süreci tamamlandı.")

@app.post("/trigger-analysis")
async def trigger_analysis(background_tasks: BackgroundTasks):
    """Haber analiz sürecini tetikleyen endpoint."""
    logger.info("/trigger-analysis endpoint'i çağrıldı")
    
    # Analiz sürecini arka planda başlat
    background_tasks.add_task(analysis_process_background)
    
    return {"message": "Analiz süreci başlatıldı"}
