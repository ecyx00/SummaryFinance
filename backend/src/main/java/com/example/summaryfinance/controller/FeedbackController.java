package com.example.summaryfinance.controller;

import com.example.summaryfinance.dto.FeedbackDTO;
import com.example.summaryfinance.entity.UserFeedback;
import com.example.summaryfinance.service.FeedbackService;
import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.Refill;
import jakarta.persistence.EntityNotFoundException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Kullanıcı geri bildirimlerini işleyen API controller'ı
 */
@RestController
@RequestMapping("/api/feedback")
@RequiredArgsConstructor
@Slf4j
public class FeedbackController {

    private final FeedbackService feedbackService;
    
    // IP başına rate limiting için bucket'lar
    private final Map<String, Bucket> ipBuckets = new ConcurrentHashMap<>();
    
    /**
     * Yeni kullanıcı geri bildirimi alır ve kaydeder
     * 
     * @param feedbackDTO Kullanıcı geri bildirimi
     * @param request HTTP isteği (IP adresi ve User-Agent bilgisi için)
     * @return İşlem sonucu
     */
    @PostMapping
    public ResponseEntity<?> submitFeedback(@Valid @RequestBody FeedbackDTO feedbackDTO, HttpServletRequest request) {
        // IP adresini al
        String ipAddress = feedbackService.getClientIpAddress();
        
        // Rate limiting uygula
        Bucket bucket = resolveBucket(ipAddress);
        if (!bucket.tryConsume(1)) {
            log.warn("Rate limit aşıldı: IP={}", ipAddress);
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                    .body(Map.of(
                            "error", "Too many requests",
                            "message", "Kısa sürede çok fazla istek gönderdiniz. Lütfen birkaç dakika sonra tekrar deneyin."
                    ));
        }
        
        try {
            // Geri bildirimi işle
            UserFeedback savedFeedback = feedbackService.processFeedback(
                    feedbackDTO, 
                    ipAddress, 
                    request.getHeader("User-Agent")
            );
            
            // Başarılı yanıt
            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "message", "Geri bildiriminiz için teşekkür ederiz!",
                    "feedbackId", savedFeedback.getId()
            ));
            
        } catch (EntityNotFoundException e) {
            // Hikaye bulunamadı
            log.warn("Hikaye bulunamadı: {}", feedbackDTO.getStoryId());
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of(
                            "error", "Story not found",
                            "message", "Belirtilen hikaye bulunamadı."
                    ));
                    
        } catch (IllegalStateException e) {
            // Zaten geri bildirim var
            log.warn("Tekrarlanan geri bildirim: IP={}, StoryId={}", ipAddress, feedbackDTO.getStoryId());
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of(
                            "error", "Duplicate feedback",
                            "message", "Bu hikaye için zaten geri bildirim gönderdiniz."
                    ));
                    
        } catch (IllegalArgumentException e) {
            // Geçersiz veri
            return ResponseEntity.badRequest()
                    .body(Map.of(
                            "error", "Invalid data",
                            "message", e.getMessage()
                    ));
                    
        } catch (Exception e) {
            // Diğer hatalar
            log.error("Geri bildirim işlenirken hata: ", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of(
                            "error", "Server error",
                            "message", "Geri bildiriminiz işlenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
                    ));
        }
    }
    
    /**
     * IP adresi için rate-limiting bucket'ı oluşturur veya mevcut olanı döndürür
     * 
     * @param ipAddress IP adresi
     * @return Rate limiting bucket'ı
     */
    private Bucket resolveBucket(String ipAddress) {
        return ipBuckets.computeIfAbsent(ipAddress, ip -> {
            // Dakikada 10 istek limiti
            Bandwidth limit = Bandwidth.classic(10, Refill.greedy(10, Duration.ofMinutes(1)));
            return Bucket.builder().addLimit(limit).build();
        });
    }
}
