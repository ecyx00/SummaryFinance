package com.example.summaryfinance.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class NewsDTO {
    private String id;
    private String url;
    private LocalDateTime publicationDate;
    private String section;
    private String source;
}