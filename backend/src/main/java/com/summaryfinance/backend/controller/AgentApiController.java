package com.summaryfinance.backend.controller;

import com.summaryfinance.backend.dto.*;
import com.summaryfinance.backend.service.NewsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/agent")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class AgentApiController {
    private final NewsService newsService;
    
    @PostMapping("/news")
    public ResponseEntity<?> saveNews(@RequestBody List<NewsFromAgentDTO> newsItems) {
        newsService.saveNewsFromAgent(newsItems);
        return ResponseEntity.ok().build();
    }
    
    @PostMapping("/relations")
    public ResponseEntity<?> saveRelations(@RequestBody List<NewsRelationDTO> relations) {
        newsService.saveRelationsFromAgent(relations);
        return ResponseEntity.ok().build();
    }
    
    @PostMapping("/summaries") 
    public ResponseEntity<?> saveSummaries(@RequestBody List<NewsSummaryDTO> summaries) {
        newsService.saveSummariesFromAgent(summaries);
        return ResponseEntity.ok().build();
    }
    
    @GetMapping("/pending-news")
    public ResponseEntity<List<NewsDTO>> getPendingNews() {
        return ResponseEntity.ok(newsService.getPendingNews());
    }
} 