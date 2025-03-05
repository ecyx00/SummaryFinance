package com.summaryfinance.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import java.time.LocalDateTime;

@Data
public class NewsCreateDTO {
    @NotBlank(message = "Guardian ID boş olamaz")
    private String guardianId;
    
    @NotBlank(message = "Başlık boş olamaz")
    private String title;
    
    @NotBlank(message = "İçerik boş olamaz")
    private String content;
    
    @NotBlank(message = "Kategori boş olamaz")
    private String category;
    
    private String sourceUrl;
    private String sourceName;
    
    @NotNull(message = "Yayın tarihi boş olamaz")
    private LocalDateTime publishedDate;
} 