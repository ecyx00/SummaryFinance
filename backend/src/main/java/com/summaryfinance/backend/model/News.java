package com.summaryfinance.backend.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@Entity
@Table(name = "news_articles")
public class News {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(unique = true)
    private String guardianId;
    
    @Column(nullable = false)
    private String title;
    
    @Column(columnDefinition = "TEXT")
    private String content;
    
    private String category;
    private String sourceUrl;
    private String sourceName;
    
    private LocalDateTime publishedDate;
    
    @Column(updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private AnalysisStatus analysisStatus = AnalysisStatus.PENDING;
    
    @Column(columnDefinition = "TEXT")
    private String summary;
    
    private Double sentimentScore;
    
    @Column(columnDefinition = "TEXT")
    private String keyPoints;
    
    @Column(columnDefinition = "TEXT")
    private String mainTopics;
    
    public enum AnalysisStatus {
        PENDING,
        PROCESSING,
        COMPLETED,
        FAILED
    }

    public void completeAnalysis(String summary, Double sentimentScore, 
                               String keyPoints, String mainTopics) {
        this.summary = summary;
        this.sentimentScore = sentimentScore;
        this.keyPoints = keyPoints;
        this.mainTopics = mainTopics;
        this.analysisStatus = AnalysisStatus.COMPLETED;
    }
}