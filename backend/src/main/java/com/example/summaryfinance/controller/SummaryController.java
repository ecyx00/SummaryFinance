package com.example.summaryfinance.controller;

import com.example.summaryfinance.dto.SummaryDTO;
import com.example.summaryfinance.service.SummaryService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
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
    public ResponseEntity<List<SummaryDTO>> getSummaries(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date) {
        
        List<SummaryDTO> summaries;
        
        if (category != null && !category.isEmpty()) {
            logger.info("Kategori filtresi uygulanıyor: {}", category);
            summaries = summaryService.getSummariesByCategory(category);
        } else if (date != null) {
            logger.info("Tarih filtresi uygulanıyor: {}", date);
            summaries = summaryService.getSummariesByDate(date);
        } else {
            logger.info("Tüm özet listesi alınıyor");
            summaries = summaryService.getAllSummaries();
        }
        
        return ResponseEntity.ok(summaries);
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
