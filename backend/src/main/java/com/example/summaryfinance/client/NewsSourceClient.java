package com.example.summaryfinance.client;

import com.example.summaryfinance.dto.NewsDTO;
import reactor.core.publisher.Flux;
import java.time.LocalDate;

public interface NewsSourceClient {

    Flux<NewsDTO> fetchNewsByTopic(String resolvedApiFilter, LocalDate startDate, LocalDate endDate);
    String getSourceName();
}