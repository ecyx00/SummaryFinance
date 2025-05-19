package com.example.summaryfinance.controller;

import com.example.summaryfinance.entity.AnalyzedNewsLink;
import com.example.summaryfinance.entity.AnalyzedSummaryOutput;
import com.example.summaryfinance.entity.News;
import com.example.summaryfinance.repository.AnalyzedNewsLinkRepository;
import com.example.summaryfinance.repository.AnalyzedSummaryOutputRepository;
import com.example.summaryfinance.repository.NewsRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * Frontend'e analiz edilmiş özet verileri sunan Controller sınıfı.
 * Özetlerin listelenmesi ve tekil özet detaylarının sunulması için API endpoint'leri sağlar.
 */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*", allowedHeaders = "*")
public class SummaryDisplayController {

    private final AnalyzedSummaryOutputRepository analyzedSummaryOutputRepository;
    private final AnalyzedNewsLinkRepository analyzedNewsLinkRepository;
    private final NewsRepository newsRepository;

    @Autowired
    public SummaryDisplayController(
            AnalyzedSummaryOutputRepository analyzedSummaryOutputRepository,
            AnalyzedNewsLinkRepository analyzedNewsLinkRepository,
            NewsRepository newsRepository) {
        this.analyzedSummaryOutputRepository = analyzedSummaryOutputRepository;
        this.analyzedNewsLinkRepository = analyzedNewsLinkRepository;
        this.newsRepository = newsRepository;
    }

    /**
     * Analiz edilmiş tüm özetleri listeler.
     * Opsiyonel filtreler (tarih ve kategori) ve sayfalama parametreleri desteklenir.
     *
     * @param publicationDate Belirli bir tarihe göre filtreleme
     * @param category Belirli bir kategoriye göre filtreleme
     * @param page Sayfa numarası (0'dan başlar)
     * @param size Sayfa başına öğe sayısı
     * @return Filtrelenmiş ve sayfalanmış özet listesi
     */
    // Logger tanımla
    private static final org.slf4j.Logger logger = org.slf4j.LoggerFactory.getLogger(SummaryDisplayController.class);
    
    @GetMapping("/stories")
    public ResponseEntity<?> getAllSummaries(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate publicationDate,
            @RequestParam(required = false) String category,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {

        try {
            Pageable pageable = PageRequest.of(page, size, Sort.by("id").descending());
            Page<AnalyzedSummaryOutput> summariesPage;

            // Filtreleme kriterleri
            if (publicationDate != null && category != null) {
                summariesPage = analyzedSummaryOutputRepository.findByPublicationDateAndAssignedCategoriesContaining(
                        publicationDate, category, pageable);
            } else if (publicationDate != null) {
                summariesPage = analyzedSummaryOutputRepository.findByPublicationDate(publicationDate, pageable);
            } else if (category != null) {
                summariesPage = analyzedSummaryOutputRepository.findByAssignedCategoriesContaining(category, pageable);
            } else {
                summariesPage = analyzedSummaryOutputRepository.findAll(pageable);
            }

            List<AnalyzedSummaryOutput> summaries = summariesPage.getContent();

            // UNGROUPED_PLACEHOLDER başlıklı özetleri filtrele
            summaries = summaries.stream()
                    .filter(summary -> !summary.getStoryTitle().equals("UNGROUPED_PLACEHOLDER"))
                    .collect(Collectors.toList());

            if (summaries.isEmpty()) {
                return ResponseEntity.noContent().build();
            }

            return ResponseEntity.ok(summaries);
        } catch (Exception e) {
            logger.error("Özet verileri getirilirken hata oluştu: ", e);
            return ResponseEntity.badRequest()
                    .body(java.util.Map.of("error", "Özet verileri getirilirken hata oluştu: " + e.getMessage()));
        }
    }

    /**
     * Belirli bir özet ID'sine göre detaylı bilgi getirir
     *
     * @param id Özet ID'si
     * @return Özet detayları ve ilişkili referanslar
     */
    @GetMapping("/story/{id}")
    public ResponseEntity<?> getSummaryById(@PathVariable Long id) {
        Optional<AnalyzedSummaryOutput> summaryOptional = analyzedSummaryOutputRepository.findById(id);

        if (!summaryOptional.isPresent()) {
            return ResponseEntity.notFound().build();
        }

        AnalyzedSummaryOutput summary = summaryOptional.get();

        // İlişkili haberleri bul
        List<AnalyzedNewsLink> links = analyzedNewsLinkRepository.findByAnalyzedSummaryOutput(summary);
        List<String> referenceUrls = new ArrayList<>();

        // Her bir link için orijinal haber URL'sini al
        for (AnalyzedNewsLink link : links) {
            News originalNews = link.getOriginalNews();
            if (originalNews != null && originalNews.getUrl() != null) {
                referenceUrls.add(originalNews.getUrl());
            } else if (originalNews != null) {
                // URL boşsa, veritabanından en güncel bilgiyi alma (newsRepository kullanımı)
                News fullNews = newsRepository.findById(originalNews.getId()).orElse(null);
                if (fullNews != null && fullNews.getUrl() != null) {
                    referenceUrls.add(fullNews.getUrl());
                }
            }
        }

        // Yanıta hem özeti hem de referans URL'leri ekle
        // Burada basitlik için sadece özeti döndürüyoruz,
        // gerçek uygulamada bir DTO kullanılabilir
        return ResponseEntity.ok(summary);
    }
}
