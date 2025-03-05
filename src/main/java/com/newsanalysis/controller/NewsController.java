package com.newsanalysis.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/news")
public class NewsController {
    
    @Autowired
    private NewsService newsService;
    
    @GetMapping("/analyze")
    public ResponseEntity<List<NewsAnalysis>> analyzeNews() {
        return ResponseEntity.ok(newsService.triggerNewsAnalysis());
    }
    
    @GetMapping("/summaries")
    public ResponseEntity<List<NewsSummary>> getLatestSummaries(
            @RequestParam(defaultValue = "10") int limit) {
        return ResponseEntity.ok(newsService.getLatestSummaries(limit));
    }
} 