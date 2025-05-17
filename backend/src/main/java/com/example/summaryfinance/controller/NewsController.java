package com.example.summaryfinance.controller;

import com.example.summaryfinance.dto.NewsDTO;
import com.example.summaryfinance.service.NewsService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;
import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/news")
public class NewsController {

    private final NewsService newsService;

    public NewsController(NewsService newsService) {
        this.newsService = newsService;
    }

    @GetMapping("/fetch-reactive")
    public Mono<ResponseEntity<String>> fetchNewsReactive() {
        // ---> DÜZELTME: NewsService'deki güncellenmiş metod adı çağrılıyor <---
        return newsService.fetchAndSaveAllConfiguredNewsReactive()
                .then(Mono.just(ResponseEntity.ok("Reactive news fetch process initiated successfully.")))
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
}