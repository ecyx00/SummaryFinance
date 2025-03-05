package com.summaryfinance.backend.agent;

import com.summaryfinance.backend.model.News;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class NewsReaderAgent {
    
    @Value("${api.guardian.key}")
    private String guardianApiKey;
    
    @Value("${api.guardian.url}")
    private String guardianApiUrl;
    
    public List<News> fetchLatestNews() {
        // Python agent'ına bağlanıp haberleri çeken gerçek uygulama
        // Şimdilik boş bir liste dönüyoruz
        return new ArrayList<>();
    }
} 