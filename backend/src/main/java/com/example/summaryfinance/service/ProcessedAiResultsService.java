package com.example.summaryfinance.service;

import com.example.summaryfinance.dto.AiProcessingResultDTO;
// import com.example.summaryfinance.dto.AnalyzedStoryPayloadDTO; // Kullanılmıyor
// import com.example.summaryfinance.entity.News; // Kullanılmıyor
import com.example.summaryfinance.repository.NewsRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.ZonedDateTime;
// import java.util.List; // Kullanılmıyor
// import java.util.Optional; // Kullanılmıyor

/**
 * AI servisinden gelen analiz sonuçlarını işleyen ve veritabanına kaydeden servis sınıfı.
 * Yeni analiz sonuçları kaydedildiğinde NotificationService aracılığıyla istemcilere bildirim gönderir.
 */
@Service
@Slf4j
public class ProcessedAiResultsService {

    @SuppressWarnings("unused") // Şimdilik kullanılmıyor, ileride kullanılacak
    private final NewsRepository newsRepository;
    private final NotificationService notificationService;
    
    @Autowired
    public ProcessedAiResultsService(
        NewsRepository newsRepository,
        NotificationService notificationService) {
            
        this.newsRepository = newsRepository;
        this.notificationService = notificationService;
    }
    
    /**
     * AI servisinden gelen analiz sonuçlarını işler ve veritabanına kaydeder.
     * 
     * @param resultDto AI servisinden gelen işlem sonuçları
     * @return Kaydedilen özet sayısı
     */
    @Transactional
    public int saveAiResults(AiProcessingResultDTO resultDto) {
        /* Yeni yapıya uygun şekilde implementasyon yapılacak */
        log.info("Analiz sonuçları yeni yapıya göre kaydedilecek.");
        
        // Bildirim gönderme
        notificationService.sendNewSummariesNotification(ZonedDateTime.now());
        
        return 0; // Geçici olarak 0 dönüyoruz
    }
}
