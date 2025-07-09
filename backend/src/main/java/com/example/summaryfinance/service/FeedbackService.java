package com.example.summaryfinance.service;

import com.example.summaryfinance.dto.FeedbackDTO;
import com.example.summaryfinance.entity.AnalyzedStory;
import com.example.summaryfinance.entity.UserFeedback;
import com.example.summaryfinance.repository.UserFeedbackRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityNotFoundException;
import jakarta.servlet.http.HttpServletRequest;
import java.time.ZonedDateTime;

/**
 * Kullanıcı geri bildirimlerini işleyen servis
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class FeedbackService {

    private final UserFeedbackRepository userFeedbackRepository;
    private final EntityManager entityManager;

    /**
     * Kullanıcıdan gelen geri bildirimi işler ve kaydeder
     *
     * @param feedbackDTO Kullanıcı geri bildirimi
     * @param remoteAddr Kullanıcı IP adresi
     * @param userAgent Kullanıcı tarayıcı bilgisi
     * @return Kaydedilen geri bildirim
     * @throws IllegalArgumentException Geçersiz veya eksik veri durumunda
     * @throws EntityNotFoundException Hikaye bulunamadığında
     */
    @Transactional
    public UserFeedback processFeedback(FeedbackDTO feedbackDTO, String remoteAddr, String userAgent) {
        // Veri doğrulama
        validateFeedbackData(feedbackDTO);
        
        // Hikayeyi kontrol et
        AnalyzedStory story = entityManager.find(AnalyzedStory.class, feedbackDTO.getStoryId());
        if (story == null) {
            log.warn("Hikaye bulunamadı: {}", feedbackDTO.getStoryId());
            throw new EntityNotFoundException("Belirtilen ID ile hikaye bulunamadı: " + feedbackDTO.getStoryId());
        }

        // Aynı IP + hikaye için daha önce geri bildirim var mı?
        userFeedbackRepository.findByStory_IdAndIpAddress(story.getId(), remoteAddr)
                .ifPresent(existingFeedback -> {
                    log.warn("Bu hikaye için zaten geri bildirim mevcut: {} (IP: {})", 
                            story.getId(), remoteAddr);
                    throw new IllegalStateException("Bu hikaye için zaten geri bildirim gönderdiniz");
                });

        // Yeni geri bildirim oluştur
        UserFeedback feedback = new UserFeedback();
        feedback.setStory(story);
        feedback.setIpAddress(remoteAddr);
        feedback.setUserAgent(userAgent);
        feedback.setRating(feedbackDTO.getRating() != null ? feedbackDTO.getRating().shortValue() : null);
        feedback.setIsHelpful(feedbackDTO.getIsHelpful());
        feedback.setComment(feedbackDTO.getComment()); // Yorum bilgisini ekle
        feedback.setFeedbackTimestamp(ZonedDateTime.now());

        // Kaydet ve dön
        UserFeedback savedFeedback = userFeedbackRepository.save(feedback);
        log.info("Yeni geri bildirim kaydedildi: {} (Hikaye ID: {})", savedFeedback.getId(), story.getId());
        
        return savedFeedback;
    }
    
    /**
     * Geçerli HTTP isteğinden IP adresini alır
     *
     * @return IP adresi
     */
    public String getClientIpAddress() {
        HttpServletRequest request = ((ServletRequestAttributes) RequestContextHolder.currentRequestAttributes()).getRequest();
        String ipAddress = request.getHeader("X-Forwarded-For");
        
        if (ipAddress == null || ipAddress.isEmpty() || "unknown".equalsIgnoreCase(ipAddress)) {
            ipAddress = request.getHeader("Proxy-Client-IP");
        }
        if (ipAddress == null || ipAddress.isEmpty() || "unknown".equalsIgnoreCase(ipAddress)) {
            ipAddress = request.getHeader("WL-Proxy-Client-IP");
        }
        if (ipAddress == null || ipAddress.isEmpty() || "unknown".equalsIgnoreCase(ipAddress)) {
            ipAddress = request.getHeader("HTTP_CLIENT_IP");
        }
        if (ipAddress == null || ipAddress.isEmpty() || "unknown".equalsIgnoreCase(ipAddress)) {
            ipAddress = request.getHeader("HTTP_X_FORWARDED_FOR");
        }
        if (ipAddress == null || ipAddress.isEmpty() || "unknown".equalsIgnoreCase(ipAddress)) {
            ipAddress = request.getRemoteAddr();
        }
        
        // Virgülle ayrılmış ip adreslerinden ilkini al (proxy zinciri durumunda)
        if (ipAddress != null && ipAddress.contains(",")) {
            ipAddress = ipAddress.split(",")[0].trim();
        }
        
        return ipAddress;
    }
    
    /**
     * Geri bildirim verilerini doğrular
     *
     * @param feedbackDTO Doğrulanacak geri bildirim verisi
     * @throws IllegalArgumentException Eksik veya geçersiz veri
     */
    private void validateFeedbackData(FeedbackDTO feedbackDTO) {
        if (feedbackDTO == null) {
            throw new IllegalArgumentException("Geri bildirim verisi boş olamaz");
        }
        
        if (feedbackDTO.getStoryId() == null) {
            throw new IllegalArgumentException("Hikaye ID zorunludur");
        }
        
        // En az bir değerlendirme türü gerekli
        if (feedbackDTO.getRating() == null && feedbackDTO.getIsHelpful() == null) {
            throw new IllegalArgumentException("Puan veya yararlılık değerlendirmesi zorunludur");
        }
        
        // Puan belirtilmişse aralığı kontrol et
        if (feedbackDTO.getRating() != null && (feedbackDTO.getRating() < 1 || feedbackDTO.getRating() > 5)) {
            throw new IllegalArgumentException("Puan 1-5 aralığında olmalıdır");
        }
    }
}
