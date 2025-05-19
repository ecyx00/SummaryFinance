package com.example.summaryfinance.service;

import com.example.summaryfinance.dto.AiProcessingResultDTO;
import com.example.summaryfinance.dto.AnalyzedStoryPayloadDTO;
import com.example.summaryfinance.entity.AnalyzedNewsLink;
import com.example.summaryfinance.entity.AnalyzedSummaryOutput;
import com.example.summaryfinance.entity.News;
import com.example.summaryfinance.repository.AnalyzedNewsLinkRepository;
import com.example.summaryfinance.repository.AnalyzedSummaryOutputRepository;
import com.example.summaryfinance.repository.NewsRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * AI servisinden gelen analiz sonuçlarını işleyen ve veritabanına kaydeden servis sınıfı.
 * Yeni analiz sonuçları kaydedildiğinde NotificationService aracılığıyla istemcilere bildirim gönderir.
 */
@Service
@Slf4j
public class ProcessedAiResultsService {

    private final AnalyzedSummaryOutputRepository analyzedSummaryOutputRepository;
    private final AnalyzedNewsLinkRepository analyzedNewsLinkRepository;
    private final NewsRepository newsRepository;
    private final NotificationService notificationService;
    
    // Gruplanamayan haberler için sabit placeholder başlık
    private static final String UNGROUPED_PLACEHOLDER_TITLE = "UNGROUPED_PLACEHOLDER";
    
    @Autowired
    public ProcessedAiResultsService(
        AnalyzedSummaryOutputRepository analyzedSummaryOutputRepository,
        AnalyzedNewsLinkRepository analyzedNewsLinkRepository,
        NewsRepository newsRepository,
        NotificationService notificationService) {
            
        this.analyzedSummaryOutputRepository = analyzedSummaryOutputRepository;
        this.analyzedNewsLinkRepository = analyzedNewsLinkRepository;
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
        int totalSaved = 0;
        
        if (resultDto.getAnalyzedStories() != null && !resultDto.getAnalyzedStories().isEmpty()) {
            for (AnalyzedStoryPayloadDTO storyDto : resultDto.getAnalyzedStories()) {
                saveAnalyzedStory(storyDto);
                totalSaved++;
            }
            log.info("{} adet analiz edilmiş haber başarıyla kaydedildi", totalSaved);
            
            // Tüm veritabanı işlemleri tamamlandıktan sonra bildirim gönder
            notificationService.sendNewSummariesNotification(LocalDateTime.now());
        }
        
        // Gruplanamayan haberleri işle
        if (resultDto.getUngroupedNewsIds() != null && !resultDto.getUngroupedNewsIds().isEmpty()) {
            saveUngroupedNewsIds(resultDto.getUngroupedNewsIds());
            log.info("{} adet gruplanamayan haber başarıyla işlendi", resultDto.getUngroupedNewsIds().size());
        }
        
        return totalSaved;
    }
    
    /**
     * Tek bir analiz edilmiş haber grubunu veritabanına kaydeder.
     * 
     * @param storyDto Analiz edilmiş haber grubu
     * @return Kaydedilen AnalyzedSummaryOutput nesnesi
     */
    private AnalyzedSummaryOutput saveAnalyzedStory(AnalyzedStoryPayloadDTO storyDto) {
        // Özeti veritabanına kaydet
        AnalyzedSummaryOutput summaryOutput = new AnalyzedSummaryOutput();
        summaryOutput.setStoryTitle(storyDto.getStoryTitle());
        summaryOutput.setSummaryText(storyDto.getSummaryText());
        summaryOutput.setPublicationDate(storyDto.getPublicationDate());
        summaryOutput.setAssignedCategories(storyDto.getAssignedCategories() != null 
                                           ? storyDto.getAssignedCategories() 
                                           : new ArrayList<>());
        
        // Özeti veritabanına kaydet
        AnalyzedSummaryOutput savedSummary = analyzedSummaryOutputRepository.save(summaryOutput);
        log.debug("Özet kaydedildi: {}", savedSummary.getStoryTitle());
        
        // İlişkili haberleri özete bağla
        if (storyDto.getNewsIds() != null && !storyDto.getNewsIds().isEmpty()) {
            for (String newsIdStr : storyDto.getNewsIds()) {
                try {
                    Long newsId = Long.parseLong(newsIdStr);
                    Optional<News> newsOpt = newsRepository.findById(newsId);
                    
                    if (newsOpt.isPresent()) {
                        AnalyzedNewsLink newsLink = new AnalyzedNewsLink(savedSummary, newsOpt.get());
                        analyzedNewsLinkRepository.save(newsLink);
                        log.debug("Haber-özet ilişkisi kaydedildi. SummaryID: {}, NewsID: {}", 
                                 savedSummary.getId(), newsId);
                    } else {
                        log.warn("Haber bulunamadı, ID: {}", newsId);
                    }
                } catch (NumberFormatException e) {
                    log.error("Geçersiz haber ID formatı: {}", newsIdStr, e);
                }
            }
        }
        
        return savedSummary;
    }
    
    /**
     * Gruplanamayan haberleri özel bir placeholder özete bağlar.
     * 
     * @param ungroupedNewsIds Gruplanamayan haber ID'leri listesi
     */
    private void saveUngroupedNewsIds(List<String> ungroupedNewsIds) {
        // Önce UNGROUPED_PLACEHOLDER özetini bul veya oluştur
        AnalyzedSummaryOutput ungroupedPlaceholder = getOrCreateUngroupedPlaceholder();
        
        // Her bir gruplanamayan haberi bu placeholder özete bağla
        for (String newsIdStr : ungroupedNewsIds) {
            try {
                Long newsId = Long.parseLong(newsIdStr);
                Optional<News> newsOpt = newsRepository.findById(newsId);
                
                if (newsOpt.isPresent()) {
                    // Önce bu haberin zaten placeholder'a bağlı olup olmadığını kontrol et
                    List<AnalyzedNewsLink> existingLinks = 
                            analyzedNewsLinkRepository.findByAnalyzedSummaryOutputAndOriginalNews(
                                    ungroupedPlaceholder, newsOpt.get());
                    
                    if (existingLinks.isEmpty()) {
                        AnalyzedNewsLink newsLink = new AnalyzedNewsLink(ungroupedPlaceholder, newsOpt.get());
                        analyzedNewsLinkRepository.save(newsLink);
                        log.debug("Gruplanamayan haber kaydedildi. NewsID: {}", newsId);
                    } else {
                        log.debug("Haber zaten gruplanamayan olarak işaretlenmiş. NewsID: {}", newsId);
                    }
                } else {
                    log.warn("Gruplanamayan haber bulunamadı, ID: {}", newsId);
                }
            } catch (NumberFormatException e) {
                log.error("Geçersiz haber ID formatı: {}", newsIdStr, e);
            }
        }
    }
    
    /**
     * Gruplanamayan haberler için placeholder özeti bulur veya oluşturur.
     * 
     * @return Gruplanamayan haberler için placeholder özet
     */
    private AnalyzedSummaryOutput getOrCreateUngroupedPlaceholder() {
        List<AnalyzedSummaryOutput> placeholders = 
                analyzedSummaryOutputRepository.findByStoryTitle(UNGROUPED_PLACEHOLDER_TITLE);
        
        if (!placeholders.isEmpty()) {
            return placeholders.get(0);
        }
        
        // Placeholder yoksa yeni oluştur
        AnalyzedSummaryOutput placeholder = new AnalyzedSummaryOutput();
        placeholder.setStoryTitle(UNGROUPED_PLACEHOLDER_TITLE);
        placeholder.setSummaryText("Bu haberler gruplanamadı");
        placeholder.setPublicationDate(java.time.LocalDate.now()); // Bugünün tarihi
        placeholder.setAssignedCategories(List.of("ungrouped"));
        
        return analyzedSummaryOutputRepository.save(placeholder);
    }
}
