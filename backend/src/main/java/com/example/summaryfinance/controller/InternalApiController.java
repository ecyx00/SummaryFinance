package com.example.summaryfinance.controller;

import com.example.summaryfinance.dto.AiProcessingResultDTO;
import com.example.summaryfinance.service.ProcessedAiResultsService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

/**
 * Sistem içi kullanılan API endpoint'lerini içeren Controller sınıfı.
 * Python AI servisi gibi dahili servislerden gelen istekleri işler.
 */
@RestController
@RequestMapping("/api/internal")
@RequiredArgsConstructor
@Slf4j
public class InternalApiController {

    private final ProcessedAiResultsService processedAiResultsService;
    
    /**
     * Python AI servisinden gelen analiz edilmiş haber sonuçlarını kaydeder.
     * 
     * @param resultDto AI servisi tarafından gönderilen işlenmiş veri
     * @return Kayıt işleminin sonucu
     */
    @PostMapping("/submit-ai-results")
    public ResponseEntity<Map<String, Object>> submitAiResults(@RequestBody AiProcessingResultDTO resultDto) {
        log.info("AI işleme sonuçları alındı: {} özet, {} gruplanamayan haber", 
                resultDto.getAnalyzedStories() != null ? resultDto.getAnalyzedStories().size() : 0,
                resultDto.getUngroupedNewsIds() != null ? resultDto.getUngroupedNewsIds().size() : 0);
        
        try {
            int savedCount = processedAiResultsService.saveAiResults(resultDto);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "AI işleme sonuçları başarıyla kaydedildi");
            response.put("savedStoriesCount", savedCount);
            response.put("ungroupedNewsCount", 
                    resultDto.getUngroupedNewsIds() != null ? resultDto.getUngroupedNewsIds().size() : 0);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("AI işleme sonuçları kaydedilirken bir hata oluştu", e);
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("message", "İşleme hatası: " + e.getMessage());
            
            return ResponseEntity.badRequest().body(errorResponse);
        }
    }
}
