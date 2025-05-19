package com.example.summaryfinance.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Python AI servisinden gelen tüm işlenmiş sonuçları içeren ana DTO sınıfı.
 * Hem başarıyla gruplanmış/özetlenmiş haberleri hem de gruplanamayan haberleri içerir.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AiProcessingResultDTO {
    
    @JsonProperty("analyzed_stories")
    private List<AnalyzedStoryPayloadDTO> analyzedStories; // Başarıyla analiz edilmiş haber özetleri
    
    @JsonProperty("ungrouped_news_ids")
    private List<String> ungroupedNewsIds; // Herhangi bir gruba atanamayan haber ID'leri (String formatında)
}
