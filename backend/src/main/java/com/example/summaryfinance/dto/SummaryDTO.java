package com.example.summaryfinance.dto;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Analiz edilmiş özet bilgilerini taşıyan DTO sınıfı.
 * Frontend'e özetlerin listelenmesi ve detay görüntülenmesi için kullanılır.
 */
public class SummaryDTO {
    
    private Long id;
    private String storyTitle;
    private String summaryText;
    private LocalDate publicationDate;
    private LocalDateTime generatedAt;
    private List<String> assignedCategories = new ArrayList<>();
    // Kaynak URL'leri için basit bir liste
    private List<String> sourceUrls = new ArrayList<>();
    
    // Getters and Setters
    public Long getId() {
        return id;
    }
    
    public void setId(Long id) {
        this.id = id;
    }
    
    public String getStoryTitle() {
        return storyTitle;
    }
    
    public void setStoryTitle(String storyTitle) {
        this.storyTitle = storyTitle;
    }
    
    public String getSummaryText() {
        return summaryText;
    }
    
    public void setSummaryText(String summaryText) {
        this.summaryText = summaryText;
    }
    
    public LocalDate getPublicationDate() {
        return publicationDate;
    }
    
    public void setPublicationDate(LocalDate publicationDate) {
        this.publicationDate = publicationDate;
    }
    
    public LocalDateTime getGeneratedAt() {
        return generatedAt;
    }
    
    public void setGeneratedAt(LocalDateTime generatedAt) {
        this.generatedAt = generatedAt;
    }
    
    public List<String> getAssignedCategories() {
        return assignedCategories;
    }
    
    public void setAssignedCategories(List<String> assignedCategories) {
        this.assignedCategories = assignedCategories;
    }
    
    public List<String> getSourceUrls() {
        return sourceUrls;
    }
    
    public void setSourceUrls(List<String> sourceUrls) {
        this.sourceUrls = sourceUrls;
    }
}
