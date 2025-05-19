package com.example.summaryfinance.service;

import com.example.summaryfinance.dto.SummaryDTO;
import com.example.summaryfinance.entity.AnalyzedNewsLink;
import com.example.summaryfinance.entity.AnalyzedSummaryOutput;
import com.example.summaryfinance.entity.News;
import com.example.summaryfinance.repository.AnalyzedNewsLinkRepository;
import com.example.summaryfinance.repository.AnalyzedSummaryOutputRepository;
import com.example.summaryfinance.repository.NewsRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * Özet işlemleri için servis sınıfı.
 * Analiz edilmiş özet verilerini alma, detay görüntüleme ve filtreleme işlemlerini gerçekleştirir.
 */
@Service
public class SummaryService {
    
    private static final Logger logger = LoggerFactory.getLogger(SummaryService.class);
    
    private final AnalyzedSummaryOutputRepository summaryRepository;
    private final AnalyzedNewsLinkRepository newsLinkRepository;
    private final NewsRepository newsRepository;
    
    public SummaryService(
            AnalyzedSummaryOutputRepository summaryRepository,
            AnalyzedNewsLinkRepository newsLinkRepository,
            NewsRepository newsRepository) {
        this.summaryRepository = summaryRepository;
        this.newsLinkRepository = newsLinkRepository;
        this.newsRepository = newsRepository;
    }
    
    /**
     * Tüm özet verilerini döndürür
     * @return Özet listesi
     */
    public List<SummaryDTO> getAllSummaries() {
        logger.debug("Tüm özet verileri çekiliyor");
        List<AnalyzedSummaryOutput> summaries = summaryRepository.findAll();
        return summaries.stream().map(this::convertToDTO).collect(Collectors.toList());
    }
    
    /**
     * Belirli bir ID'ye sahip özet detayını getirir
     * @param id Özet ID'si
     * @return Özet detay bilgisi
     */
    public Optional<SummaryDTO> getSummaryById(Long id) {
        logger.debug("ID'si {} olan özet verisi çekiliyor", id);
        return summaryRepository.findById(id).map(summary -> {
            SummaryDTO dto = convertToDTO(summary);
            enrichWithSourceUrls(dto);
            return dto;
        });
    }
    
    /**
     * Belirli bir kategoriye sahip özetleri filtreler
     * @param category Kategori
     * @return Filtrelenmiş özet listesi
     */
    public List<SummaryDTO> getSummariesByCategory(String category) {
        logger.debug("Kategori {} için özetler filtreleniyor", category);
        List<AnalyzedSummaryOutput> allSummaries = summaryRepository.findAll();
        
        return allSummaries.stream()
                .filter(summary -> summary.getAssignedCategories().contains(category))
                .map(this::convertToDTO)
                .collect(Collectors.toList());
    }
    
    /**
     * Belirli bir tarihe ait özetleri getirir
     * @param date Tarih
     * @return Özet listesi
     */
    public List<SummaryDTO> getSummariesByDate(LocalDate date) {
        logger.debug("Tarih {} için özetler filtreleniyor", date);
        List<AnalyzedSummaryOutput> summaries = summaryRepository.findByPublicationDate(date);
        return summaries.stream().map(this::convertToDTO).collect(Collectors.toList());
    }
    
    /**
     * Özet entity'sini DTO'ya dönüştürür
     */
    private SummaryDTO convertToDTO(AnalyzedSummaryOutput summary) {
        SummaryDTO dto = new SummaryDTO();
        dto.setId(summary.getId());
        dto.setStoryTitle(summary.getStoryTitle());
        dto.setSummaryText(summary.getSummaryText());
        dto.setPublicationDate(summary.getPublicationDate());
        dto.setGeneratedAt(summary.getGeneratedAt());
        dto.setAssignedCategories(new ArrayList<>(summary.getAssignedCategories()));
        return dto;
    }
    
    /**
     * DTO'yu kaynak URL'leriyle zenginleştirir
     */
    private void enrichWithSourceUrls(SummaryDTO dto) {
        // İlgili haber bağlantılarını bul
        List<AnalyzedNewsLink> newsLinks = newsLinkRepository.findBySummaryId(dto.getId());
        
        // Haber URL'lerini getir ve DTO'ya ekle
        List<String> sourceUrls = newsLinks.stream()
                .map(link -> {
                    Long newsId = link.getOriginalNews().getId();
                    return newsRepository.findById(newsId)
                            .map(News::getUrl)
                            .orElse(null);
                })
                .filter(url -> url != null)
                .collect(Collectors.toList());
        
        dto.setSourceUrls(sourceUrls);
    }
}
