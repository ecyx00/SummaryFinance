package com.summaryfinance.backend.dto;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class NewsDTO {
    private Long id;
    private String title;
    private String content;
    private String category;
    private String sourceUrl;
    private String sourceName;
    private LocalDateTime publishedDate;
    private String summary;
    private Double sentimentScore;
    private String keyPoints;
    private String mainTopics;
}