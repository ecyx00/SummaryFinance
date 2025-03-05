package com.summaryfinance.backend.dto;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class NewsFromAgentDTO {
    private String externalId;
    private String title;
    private String content;
    private String category;
    private String categoryType;
    private String sourceUrl;
    private String thumbnail;
    private LocalDateTime publishedDate;
} 