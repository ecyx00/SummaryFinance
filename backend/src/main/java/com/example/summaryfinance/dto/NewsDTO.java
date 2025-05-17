package com.example.summaryfinance.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class NewsDTO {
    // Kaynağa özgü ID kaldırıldı
    private String url;
    private String title; // Başlık eklendi
    private LocalDateTime publicationDate;
    private String section; // API'den gelen ham bölüm/kategori adı
    private String source;
}
