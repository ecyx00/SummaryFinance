package com.summaryfinance.backend.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "news")
public class News {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String title;
    
    @Column(columnDefinition = "TEXT")
    private String content;
    
    private String sourceUrl;
    
    @Column(name = "published_date")
    private LocalDateTime publishedDate;
    
    @Column(name = "source_name")
    private String sourceName;
    
    private String category;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(columnDefinition = "TEXT")
    private String summary;
    
    @Column(name = "sentiment_score")
    private Double sentimentScore;
    
    @Column(name = "key_points", columnDefinition = "TEXT")
    private String keyPoints;
    
    @Column(name = "main_topics")
    private String mainTopics;
    
    @Column(name = "analyzed_at")
    private LocalDateTime analyzedAt;
    
    @Column(name = "analysis_status")
    @Enumerated(EnumType.STRING)
    private AnalysisStatus analysisStatus = AnalysisStatus.PENDING;
    
    public enum AnalysisStatus {
        PENDING,
        PROCESSING,
        COMPLETED,
        FAILED
    }

    // Getter metodları
    public Long getId() { return id; }
    public String getTitle() { return title; }
    public String getContent() { return content; }
    public String getSourceUrl() { return sourceUrl; }
    public LocalDateTime getPublishedDate() { return publishedDate; }
    public String getSourceName() { return sourceName; }
    public String getCategory() { return category; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public String getSummary() { return summary; }
    public Double getSentimentScore() { return sentimentScore; }
    public String getKeyPoints() { return keyPoints; }
    public String getMainTopics() { return mainTopics; }
    public LocalDateTime getAnalyzedAt() { return analyzedAt; }
    public AnalysisStatus getAnalysisStatus() { return analysisStatus; }

    // Setter metodları
    public void setId(Long id) { this.id = id; }
    public void setTitle(String title) { this.title = title; }
    public void setContent(String content) { this.content = content; }
    public void setSourceUrl(String sourceUrl) { this.sourceUrl = sourceUrl; }
    public void setPublishedDate(LocalDateTime publishedDate) { this.publishedDate = publishedDate; }
    public void setSourceName(String sourceName) { this.sourceName = sourceName; }
    public void setCategory(String category) { this.category = category; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public void setSummary(String summary) { this.summary = summary; }
    public void setSentimentScore(Double sentimentScore) { this.sentimentScore = sentimentScore; }
    public void setKeyPoints(String keyPoints) { this.keyPoints = keyPoints; }
    public void setMainTopics(String mainTopics) { this.mainTopics = mainTopics; }
    public void setAnalyzedAt(LocalDateTime analyzedAt) { this.analyzedAt = analyzedAt; }
    public void setAnalysisStatus(AnalysisStatus analysisStatus) { this.analysisStatus = analysisStatus; }

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        analysisStatus = AnalysisStatus.PENDING;
    }
    
    public void completeAnalysis(String summary, Double sentimentScore, 
                               String keyPoints, String mainTopics) {
        this.summary = summary;
        this.sentimentScore = sentimentScore;
        this.keyPoints = keyPoints;
        this.mainTopics = mainTopics;
        this.analyzedAt = LocalDateTime.now();
        this.analysisStatus = AnalysisStatus.COMPLETED;
    }
}