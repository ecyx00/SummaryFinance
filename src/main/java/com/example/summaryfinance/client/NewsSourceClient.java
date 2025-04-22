package com.example.summaryfinance.client;

import com.example.summaryfinance.dto.NewsDTO;

import java.util.List;

public interface NewsSourceClient {

    List<NewsDTO> fetchBusinessNews();
    String getSourceName();
}