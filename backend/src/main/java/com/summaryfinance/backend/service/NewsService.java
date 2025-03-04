package com.summaryfinance.backend.service;

import com.summaryfinance.backend.model.News;
import com.summaryfinance.backend.model.News.AnalysisStatus;
import com.summaryfinance.backend.repository.NewsRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class NewsService {
    
    private final NewsRepository newsRepository;
    
    @Autowired
    public NewsService(NewsRepository newsRepository) {
        this.newsRepository = newsRepository;
    }
    
    // Temel CRUD Operasyonları
    public List<News> getAllNews() {
        return newsRepository.findAll();
    }
    
    public News getNewsById(Long id) {
        return newsRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("News not found with id: " + id));
    }
    
    public News saveNews(News news) {
        // Yeni haber kaydedilirken analiz durumunu PENDING olarak ayarla
        news.setAnalysisStatus(AnalysisStatus.PENDING);
        return newsRepository.save(news);
    }
    
    public News updateNews(Long id, News newsDetails) {
        News news = getNewsById(id);
        
        // Temel alanları güncelle
        news.setTitle(newsDetails.getTitle());
        news.setContent(newsDetails.getContent());
        news.setSourceUrl(newsDetails.getSourceUrl());
        news.setSourceName(newsDetails.getSourceName());
        news.setCategory(newsDetails.getCategory());
        news.setPublishedDate(newsDetails.getPublishedDate());
        
        return newsRepository.save(news);
    }
    
    public void deleteNews(Long id) {
        newsRepository.deleteById(id);
    }
    
    // Analiz İşlemleri
    public News startAnalysis(Long id) {
        News news = getNewsById(id);
        news.setAnalysisStatus(AnalysisStatus.PROCESSING);
        return newsRepository.save(news);
    }
    
    public News completeAnalysis(Long id, String summary, Double sentimentScore, 
                               String keyPoints, String mainTopics) {
        News news = getNewsById(id);
        news.completeAnalysis(summary, sentimentScore, keyPoints, mainTopics);
        return newsRepository.save(news);
    }
    
    public News markAnalysisFailed(Long id) {
        News news = getNewsById(id);
        news.setAnalysisStatus(AnalysisStatus.FAILED);
        return newsRepository.save(news);
    }
    
    // Filtreleme Metodları
    public List<News> getNewsByCategory(String category) {
        return newsRepository.findByCategory(category);
    }
    
    public List<News> getNewsBySource(String sourceName) {
        return newsRepository.findBySourceName(sourceName);
    }
    
    // Analiz Durumuna Göre Filtreleme
    public List<News> getNewsByAnalysisStatus(AnalysisStatus status) {
        return newsRepository.findByAnalysisStatus(status);
    }
    
    public List<News> getPendingAnalysis() {
        return newsRepository.findByAnalysisStatus(AnalysisStatus.PENDING);
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
        return newsRepository.countByAnalysisStatus(AnalysisStatus.COMPLETED);
    }
}
