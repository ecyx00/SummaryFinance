package com.summaryfinance.backend.service;

import com.summaryfinance.backend.dto.*;
import com.summaryfinance.backend.model.News;
import com.summaryfinance.backend.model.News.AnalysisStatus;
import com.summaryfinance.backend.model.NewsRelation;
import com.summaryfinance.backend.model.NewsSummary;
import com.summaryfinance.backend.repository.NewsRelationRepository;
import com.summaryfinance.backend.repository.NewsRepository;
import com.summaryfinance.backend.repository.NewsSummaryRepository;
import com.summaryfinance.backend.exception.ResourceNotFoundException;
import com.summaryfinance.backend.agent.NewsReaderAgent;
import com.summaryfinance.backend.agent.NewsRelationAgent;
import com.summaryfinance.backend.agent.NewsSummaryAgent;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class NewsService {
    
    private final NewsRepository newsRepository;
    private final NewsRelationRepository newsRelationRepository;
    private final NewsSummaryRepository newsSummaryRepository;
    private final NewsReaderAgent newsReaderAgent;
    private final NewsRelationAgent newsRelationAgent;
    private final NewsSummaryAgent newsSummaryAgent;
    
    // Temel CRUD Operasyonları
    public List<News> findAllById(List<Long> ids) {
        return newsRepository.findAllById(ids);
    }
    
    public News findById(Long id) {
        return newsRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Haber bulunamadı: " + id));
    }
    
    @Transactional
    public News save(News news) {
        return newsRepository.save(news);
    }
    
    @Transactional
    public void deleteById(Long id) {
        newsRepository.deleteById(id);
    }
    
    public List<News> getAllNews() {
        return newsRepository.findAll();
    }
    
    // Haber DTO metodları
    public List<NewsDTO> getLatestNews() {
        return newsRepository.findTop20ByOrderByPublishedDateDesc()
            .stream()
            .map(this::convertToDTO)
            .collect(Collectors.toList());
    }
    
    public NewsDTO getNewsById(Long id) {
        News news = newsRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Haber bulunamadı"));
        return convertToDTO(news);
    }
    
    public List<NewsDTO> getNewsByCategory(String category) {
        return newsRepository.findByCategoryOrderByPublishedDateDesc(category)
            .stream()
            .map(this::convertToDTO)
            .collect(Collectors.toList());
    }
    
    // Analiz İşlemleri
    public News startAnalysis(Long id) {
        News news = findById(id);
        news.setAnalysisStatus(AnalysisStatus.PROCESSING);
        return newsRepository.save(news);
    }
    
    public News completeAnalysis(Long id, String summary, Double sentimentScore, 
                               String keyPoints, String mainTopics) {
        News news = findById(id);
        news.completeAnalysis(summary, sentimentScore, keyPoints, mainTopics);
        return newsRepository.save(news);
    }
    
    public News markAnalysisFailed(Long id) {
        News news = findById(id);
        news.setAnalysisStatus(AnalysisStatus.FAILED);
        return newsRepository.save(news);
    }
    
    // Filtreleme Metodları
    public List<News> getNewsBySourceName(String sourceName) {
        return newsRepository.findBySourceName(sourceName);
    }
    
    // Analiz Durumuna Göre Filtreleme
    public List<News> getNewsByAnalysisStatus(AnalysisStatus status) {
        return newsRepository.findByAnalysisStatus(status);
    }
    
    public List<News> getPendingAnalysis() {
        return newsRepository.findByAnalysisStatus(AnalysisStatus.PENDING);
    }
    
    public List<NewsDTO> getPendingNews() {
        return newsRepository.findByAnalysisStatus(AnalysisStatus.PENDING)
            .stream()
            .map(this::convertToDTO)
            .collect(Collectors.toList());
    }
    
    // İstatistik Metodları
    public Double getAverageSentimentScore() {
        List<News> analyzedNews = newsRepository.findByAnalysisStatus(AnalysisStatus.COMPLETED);
        if (analyzedNews.isEmpty()) return 0.0;
        
        return analyzedNews.stream()
            .mapToDouble(News::getSentimentScore)
            .average()
            .orElse(0.0);
    }
    
    public Long getAnalyzedNewsCount() {
        return (long) newsRepository.findByAnalysisStatus(AnalysisStatus.COMPLETED).size();
    }
    
    @Transactional
    public void deleteNews(Long id) {
        News news = findById(id);
        newsRepository.delete(news);
    }
    
    @Transactional
    public void fetchAndAnalyzeNews() {
        // 1. Haberleri çek
        List<News> newNews = newsReaderAgent.fetchLatestNews();
        newsRepository.saveAll(newNews);
        
        // 2. İlişkileri analiz et
        newsRelationAgent.analyzeNewsRelations(newNews);
        
        // 3. Özetleri oluştur
        newsSummaryAgent.generateSummaries(newNews);
    }
    
    // Python Agent'larından gelen verileri işle
    @Transactional
    public void saveNewsFromAgent(List<NewsFromAgentDTO> newsItems) {
        for (NewsFromAgentDTO dto : newsItems) {
            // External ID'ye göre kontrol et, yoksa ekle
            Optional<News> existingNews = newsRepository.findByGuardianId(dto.getExternalId());
            
            if (existingNews.isEmpty()) {
                News news = new News();
                news.setGuardianId(dto.getExternalId());
                news.setTitle(dto.getTitle());
                news.setContent(dto.getContent());
                news.setCategory(dto.getCategory());
                news.setSourceUrl(dto.getSourceUrl());
                news.setSourceName("Guardian");
                news.setPublishedDate(dto.getPublishedDate());
                news.setAnalysisStatus(News.AnalysisStatus.PENDING);
                
                newsRepository.save(news);
            }
        }
    }
    
    @Transactional
    public void saveRelationsFromAgent(List<NewsRelationDTO> relations) {
        for (NewsRelationDTO dto : relations) {
            Optional<News> newsOpt = newsRepository.findByGuardianId(dto.getNewsExternalId());
            
            if (newsOpt.isPresent()) {
                News news = newsOpt.get();
                
                NewsRelation relation = new NewsRelation();
                relation.setClusterId(dto.getClusterId());
                relation.setNews(news);
                relation.setRelationStrength(dto.getRelationStrength());
                relation.setEconomicImpactScore(dto.getEconomicImpactScore());
                
                newsRelationRepository.save(relation);
                
                // Haberin durumunu güncelle
                news.setAnalysisStatus(News.AnalysisStatus.PROCESSING);
                newsRepository.save(news);
            }
        }
    }
    
    @Transactional
    public void saveSummariesFromAgent(List<NewsSummaryDTO> summaries) {
        for (NewsSummaryDTO dto : summaries) {
            NewsSummary summary = new NewsSummary();
            summary.setClusterId(dto.getClusterId());
            summary.setSummary(dto.getSummary());
            summary.setEconomicAnalysis(dto.getEconomicAnalysis());
            
            newsSummaryRepository.save(summary);
            
            // Bu kümeye ait haberleri güncelle
            List<NewsRelation> relations = newsRelationRepository.findByClusterId(dto.getClusterId());
            for (NewsRelation relation : relations) {
                News news = relation.getNews();
                news.setSummary(dto.getSummary());
                news.setAnalysisStatus(News.AnalysisStatus.COMPLETED);
                newsRepository.save(news);
            }
        }
    }
    
    private NewsDTO convertToDTO(News news) {
        NewsDTO dto = new NewsDTO();
        dto.setId(news.getId());
        dto.setTitle(news.getTitle());
        dto.setContent(news.getContent());
        dto.setCategory(news.getCategory());
        dto.setPublishedDate(news.getPublishedDate());
        dto.setSummary(news.getSummary());
        dto.setKeyPoints(news.getKeyPoints());
        dto.setMainTopics(news.getMainTopics());
        dto.setSourceUrl(news.getSourceUrl());
        return dto;
    }
}
