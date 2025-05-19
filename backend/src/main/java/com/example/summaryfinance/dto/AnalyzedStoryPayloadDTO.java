package com.example.summaryfinance.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.List;

/**
 * AI tarafından işlenmiş ve analiz edilmiş haber gruplarını temsil eden DTO sınıfı.
 * Python AI servisinden gelen hikaye/özet sonuçlarını taşır.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AnalyzedStoryPayloadDTO {
    
    @JsonProperty("story_title")
    private String storyTitle;
    
    @JsonProperty("analysis_summary")
    private String summaryText;
    
    // Not: Python tarafından gönderilmiyor, varsayılan olarak güncel tarih kullanılıyor
    private LocalDate publicationDate = LocalDate.now();
    
    @JsonProperty("main_categories")
    private List<String> assignedCategories;
    
    @JsonProperty("related_news_ids")
    private List<String> newsIds; // İlişkili haberlerin ID'leri (String formatında)
}
