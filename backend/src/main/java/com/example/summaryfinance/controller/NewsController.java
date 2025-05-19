package com.example.summaryfinance.controller;

import com.example.summaryfinance.dto.NewsDTO;
import com.example.summaryfinance.service.NewsService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/news")
public class NewsController {

    private static final Logger logger = LoggerFactory.getLogger(NewsController.class);

    private final NewsService newsService;
    
    @Value("${ai.service.url:http://localhost:8000}")
    private String aiServiceBaseUrl;

    public NewsController(NewsService newsService) {
        this.newsService = newsService;
    }

    @GetMapping("/fetch-reactive")
    public Mono<ResponseEntity<String>> fetchNewsReactive() {
        // ---> DÜZELTME: NewsService'deki güncellenmiş metod adı çağrılıyor <---
        return newsService.fetchAndSaveAllConfiguredNewsReactive()
                .then(Mono.fromCallable(() -> {
                    // Haberler başarıyla çekildikten sonra AI servisini tetikle
                    triggerAiAnalysis();
                    return ResponseEntity.ok("Reactive news fetch process completed and AI analysis triggered.");
                }))
                .onErrorResume(e -> {
                    // Hata mesajını loglamak da iyi bir pratik olabilir burada
                    // logger.error("Error initiating news fetch from controller: {}", e.getMessage());
                    return Mono.just(ResponseEntity.status(500)
                            .body("Reactive news fetch failed: " + e.getMessage()));
                });
    }

    @GetMapping
    public ResponseEntity<List<NewsDTO>> getAllNews() {
        return ResponseEntity.ok(newsService.getAllNews());
    }

    @GetMapping("/section/{section}")
    public ResponseEntity<List<NewsDTO>> getNewsBySection(@PathVariable String section) {
        return ResponseEntity.ok(newsService.getNewsBySection(section));
    }

    @GetMapping("/date-range")
    public ResponseEntity<List<NewsDTO>> getNewsByDateRange(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime start,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime end) {
        return ResponseEntity.ok(newsService.getNewsByDateRange(start, end));
    }

    @GetMapping("/source/{source}")
    public ResponseEntity<List<NewsDTO>> getNewsBySource(@PathVariable String source) {
        return ResponseEntity.ok(newsService.getNewsBySource(source));
    }
    
    /**
     * Python AI servisinin /trigger-analysis endpoint'ine HTTP POST isteği gönderir.
     * Bu metod, haber çekme işlemi başarıyla tamamlandığında çağrılır.
     */
    private void triggerAiAnalysis() {
        // Explicit instance of WebClient with baseUrl to avoid any port issues
        WebClient explicitClient = WebClient.builder()
                .baseUrl(aiServiceBaseUrl)
                .build();
                
        String endpoint = "/trigger-analysis";
        logger.info("Triggering AI analysis at: {}{}", aiServiceBaseUrl, endpoint);
        
        // Use the explicit client to ensure the correct URL and port
        explicitClient.post()
                .uri(endpoint)
                .retrieve()
                .toBodilessEntity()
                .subscribe(
                        response -> {
                            if (response.getStatusCode() == HttpStatus.OK || response.getStatusCode() == HttpStatus.ACCEPTED) {
                                logger.info("AI analysis triggered successfully");
                            } else {
                                logger.warn("AI analysis trigger returned unexpected status: {}", response.getStatusCode());
                            }
                        },
                        error -> logger.error("Failed to trigger AI analysis", error)
                );
    }
}