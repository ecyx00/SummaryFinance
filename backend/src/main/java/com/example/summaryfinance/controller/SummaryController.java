package com.example.summaryfinance.controller;

import com.example.summaryfinance.dto.SummaryDTO;
import com.example.summaryfinance.service.SummaryService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.ZonedDateTime;
// import java.time.format.DateTimeFormatter; // Kullanılmıyor
import java.util.List;

/**
 * Özet API'leri için controller sınıfı.
 * Frontend uygulaması bu endpoint'leri kullanarak özet listesi ve detay bilgilerini görüntüler.
 */
@RestController
@RequestMapping("/api/news")
@CrossOrigin(origins = "*") // CORS sorunlarını önlemek için
public class SummaryController {
    
    private static final Logger logger = LoggerFactory.getLogger(SummaryController.class);
    
    private final SummaryService summaryService;
    
    public SummaryController(SummaryService summaryService) {
        this.summaryService = summaryService;
    }
    
    /**
     * Tüm özet listesini döndürür veya filtreleme parametreleri ile filtrelenmiş liste döndürür
     */
    @GetMapping("/summaries")
    public ResponseEntity<?> getSummaries(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String date) {
        
        try {
            List<SummaryDTO> summaries;
            
            if (category != null && !category.isEmpty()) {
                logger.info("Kategori filtresi uygulanıyor: {}", category);
                summaries = summaryService.getSummariesByCategory(category);
            } else if (date != null && !date.isEmpty()) {
                logger.info("Tarih filtresi uygulanıyor (ham değer): {}", date);
                
                // Tarih string'ini ZonedDateTime'e çevir
                try {
                    // Önce ISO tarih formatını deneyelim (ISO_ZONED_DATE_TIME)
                    ZonedDateTime parsedDate;
                    try {
                        parsedDate = ZonedDateTime.parse(date);
                    } catch (Exception e) {
                        // Eğer tam ISO formatı değilse, tarih kısmını ayrıştırıp günün başlangıcı olarak kabul edelim
                        parsedDate = ZonedDateTime.parse(date + "T00:00:00Z[UTC]");
                    }
                    
                    logger.info("Tarih başarıyla ayrıştırıldı: {}", parsedDate);
                    summaries = summaryService.getSummariesByDate(parsedDate);
                } catch (Exception e) {
                    logger.error("Tarih ayrıştırma hatası: {}", e.getMessage());
                    return ResponseEntity.badRequest()
                            .body("Tarih formatı geçersiz. Lütfen ISO formatında bir tarih girin (YYYY-MM-DD veya tam ISO-8601).");
                }
            } else {
                logger.info("Tüm özet listesi alınıyor");
                summaries = summaryService.getAllSummaries();
            }
            
            return ResponseEntity.ok(summaries);
        } catch (Exception e) {
            logger.error("Özetler alınırken beklenmeyen hata: {}", e.getMessage());
            return ResponseEntity.internalServerError()
                    .body("Veriler işlenirken bir hata oluştu: " + e.getMessage());
        }
    }
    
    /**
     * Belirli bir ID'ye sahip özet detayını döndürür
     */
    @GetMapping("/summary/{id}")
    public ResponseEntity<?> getSummaryById(@PathVariable Long id) {
        logger.info("Özet detayı talep edildi. ID: {}", id);
        
        return summaryService.getSummaryById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
