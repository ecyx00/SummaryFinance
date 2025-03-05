package com.summaryfinance.backend.controller;

import com.summaryfinance.backend.dto.NewsDTO;
import com.summaryfinance.backend.service.NewsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/news")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class NewsController {
    private final NewsService newsService;
    
    @GetMapping("/latest")
    public ResponseEntity<List<NewsDTO>> getLatestNews() {
        return ResponseEntity.ok(newsService.getLatestNews());
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<NewsDTO> getNewsById(@PathVariable Long id) {
        return ResponseEntity.ok(newsService.getNewsById(id));
    }
    
    @GetMapping("/category/{category}")
    public ResponseEntity<List<NewsDTO>> getNewsByCategory(@PathVariable String category) {
        return ResponseEntity.ok(newsService.getNewsByCategory(category));
    }
}