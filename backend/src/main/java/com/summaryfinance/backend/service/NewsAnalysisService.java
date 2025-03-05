package com.summaryfinance.backend.service;

import com.summaryfinance.backend.model.*;
import com.summaryfinance.backend.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;
import java.util.ArrayList;

@Service
@RequiredArgsConstructor
public class NewsAnalysisService {
    private final NewsService newsService;
    private final NewsRelationRepository relationRepository;
    private final NewsSummaryRepository summaryRepository;
    
    @Transactional
    public void analyzeNewsCluster(String clusterId, List<Long> newsIds) {
        List<News> newsItems = newsService.findAllById(newsIds);
        List<NewsRelation> relations = new ArrayList<>();
        
        // Her haber için ilişki oluştur
        for (News news : newsItems) {
            NewsRelation relation = new NewsRelation();
            relation.setClusterId(clusterId);
            relation.setNews(news);
            relation.setRelationStrength(calculateRelationStrength(news));
            relation.setEconomicImpactScore(calculateEconomicImpact(news));
            relations.add(relation);
        }
        
        relationRepository.saveAll(relations);
    }
    
    @Transactional
    public void createNewsSummary(String clusterId, String summary, String economicAnalysis) {
        NewsSummary newsSummary = new NewsSummary();
        newsSummary.setClusterId(clusterId);
        newsSummary.setSummary(summary);
        newsSummary.setEconomicAnalysis(economicAnalysis);
        summaryRepository.save(newsSummary);
    }
    
    private Float calculateRelationStrength(News news) {
        // İlişki gücü hesaplama algoritması
        return 0.0f; // Şimdilik varsayılan değer
    }
    
    private Float calculateEconomicImpact(News news) {
        // Ekonomik etki hesaplama algoritması
        return 0.0f; // Şimdilik varsayılan değer
    }
} 