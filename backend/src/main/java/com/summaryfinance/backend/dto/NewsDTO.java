package com.summaryfinance.backend.dto;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class NewsDTO {
    private String title;           // Başlık
    private String content;         // İçerik
    private String sourceUrl;       // Kaynak URL
    private String sourceName;      // Kaynak adı
    private String category;        // Kategori
    private LocalDateTime publishedDate;  // Yayın tarihi
}