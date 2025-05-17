package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "analyzed_news_links", 
       indexes = {
           @Index(name = "idx_news_link_summary_id", columnList = "summary_output_id"),
           @Index(name = "idx_news_link_news_id", columnList = "original_news_id")
       },
       uniqueConstraints = {
           @UniqueConstraint(name = "unique_summary_news", columnNames = {"summary_output_id", "original_news_id"})
       }
)
@Getter
@Setter
@NoArgsConstructor
public class AnalyzedNewsLink {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "summary_output_id", nullable = false)
    private AnalyzedSummaryOutput analyzedSummaryOutput;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "original_news_id", nullable = false)
    private News originalNews;
    
    // Constructor
    public AnalyzedNewsLink(AnalyzedSummaryOutput analyzedSummaryOutput, News originalNews) {
        this.analyzedSummaryOutput = analyzedSummaryOutput;
        this.originalNews = originalNews;
    }
} 