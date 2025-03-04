package com.summaryfinance.backend.controller;

import com.summaryfinance.backend.dto.NewsDTO;
import com.summaryfinance.backend.model.News;
import com.summaryfinance.backend.model.News.AnalysisStatus;
import com.summaryfinance.backend.service.NewsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/news")
@CrossOrigin(origins = "*")  // CORS için
public class NewsController {

    private final NewsService newsService;

    @Autowired
    public NewsController(NewsService newsService) {
        this.newsService = newsService;
    }

    // Tüm haberleri getir
    @GetMapping
    public ResponseEntity<List<News>> getAllNews() {
        return ResponseEntity.ok(newsService.getAllNews());
    }

    // ID'ye göre haber getir
    @GetMapping("/{id}")
    public ResponseEntity<News> getNewsById(@PathVariable Long id) {
        return ResponseEntity.ok(newsService.getNewsById(id));
    }

    // Yeni haber ekle
    @PostMapping
    public ResponseEntity<News> createNews(@RequestBody News news) {
        return ResponseEntity.ok(newsService.saveNews(news));
    }

    // Haber güncelle
    @PutMapping("/{id}")
    public ResponseEntity<News> updateNews(@PathVariable Long id, @RequestBody News news) {
        return ResponseEntity.ok(newsService.updateNews(id, news));
    }

    // Haber sil
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteNews(@PathVariable Long id) {
        newsService.deleteNews(id);
        return ResponseEntity.ok().build();
    }

    // Kategoriye göre haber getir
    @GetMapping("/category/{category}")
    public ResponseEntity<List<News>> getNewsByCategory(@PathVariable String category) {
        return ResponseEntity.ok(newsService.getNewsByCategory(category));
    }

    // Kaynağa göre haber getir
    @GetMapping("/source/{sourceName}")
    public ResponseEntity<List<News>> getNewsBySource(@PathVariable String sourceName) {
        return ResponseEntity.ok(newsService.getNewsBySource(sourceName));
    }

    // Analiz durumuna göre haber getir
    @GetMapping("/status/{status}")
    public ResponseEntity<List<News>> getNewsByStatus(@PathVariable AnalysisStatus status) {
        return ResponseEntity.ok(newsService.getNewsByAnalysisStatus(status));
    }

    // Analizi bekleyen haberleri getir
    @GetMapping("/pending")
    public ResponseEntity<List<News>> getPendingNews() {
        return ResponseEntity.ok(newsService.getPendingAnalysis());
    }

    // Haber analizi başlat
    @PostMapping("/{id}/analyze")
    public ResponseEntity<News> startAnalysis(@PathVariable Long id) {
        return ResponseEntity.ok(newsService.startAnalysis(id));
    }

    // Analiz sonuçlarını kaydet
    @PostMapping("/{id}/analysis-result")
    public ResponseEntity<News> saveAnalysisResult(
            @PathVariable Long id,
            @RequestBody Map<String, Object> analysisResult) {
        return ResponseEntity.ok(newsService.completeAnalysis(
            id,
            (String) analysisResult.get("summary"),
            (Double) analysisResult.get("sentimentScore"),
            (String) analysisResult.get("keyPoints"),
            (String) analysisResult.get("mainTopics")
        ));
    }

    // Analiz istatistiklerini getir
    @GetMapping("/statistics")
    public ResponseEntity<Map<String, Object>> getStatistics() {
        return ResponseEntity.ok(Map.of(
            "analyzedCount", newsService.getAnalyzedNewsCount(),
            "averageSentiment", newsService.getAverageSentimentScore()
        ));
    }
}