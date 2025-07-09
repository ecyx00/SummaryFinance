package com.example.summaryfinance.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Kullanıcı geri bildirimi için veri transfer nesnesi
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class FeedbackDTO {

    /**
     * Değerlendirilen hikayenin ID'si
     */
    @NotNull(message = "Hikaye ID zorunludur")
    private Long storyId;
    
    /**
     * Kullanıcı puanı (1-5 arası)
     * Puan veya isHelpful'dan en az biri belirtilmelidir
     */
    @Min(value = 1, message = "Puan en az 1 olmalıdır")
    @Max(value = 5, message = "Puan en fazla 5 olmalıdır")
    private Integer rating;
    
    /**
     * Alternatif değerlendirme - yararlı mı? (true/false)
     * Puan veya isHelpful'dan en az biri belirtilmelidir
     */
    private Boolean isHelpful;
    
    /**
     * Opsiyonel kullanıcı yorumu
     */
    @Size(max = 1000, message = "Yorum en fazla 1000 karakter olmalıdır")
    private String comment;
}
