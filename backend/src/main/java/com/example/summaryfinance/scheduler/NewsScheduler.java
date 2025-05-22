package com.example.summaryfinance.scheduler;

import com.example.summaryfinance.service.NewsService;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired; // Eğer webClientBuilder'ı field olarak tutacaksan
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;

@Component
public class NewsScheduler {

    private static final Logger logger = LoggerFactory.getLogger(NewsScheduler.class);
    private final NewsService newsService;
    private WebClient webClient; // Constructor'dan çıkarıp field yap
    private final WebClient.Builder webClientBuilder; // Bunu constructor'da alıp field yap

    @Value("${ai.service.url:http://localhost:8000}")
    private String aiServiceBaseUrl;

    // Constructor'ı güncelle
    @Autowired // Spring 4.3+ için constructor injection'da @Autowired zorunlu değil ama açıkça belirtmek iyi
    public NewsScheduler(NewsService newsService, WebClient.Builder webClientBuilder) {
        this.newsService = newsService;
        this.webClientBuilder = webClientBuilder; // Builder'ı field'a ata
        logger.info("NewsScheduler CONSTRUCTOR: NewsScheduler bean created. aiServiceBaseUrl (at construction): {}", aiServiceBaseUrl);
        // this.webClient = webClientBuilder.baseUrl(aiServiceBaseUrl).build(); // BU SATIRI BURADAN KALDIR
    }

    @PostConstruct
    public void init() {
        // aiServiceBaseUrl burada @Value ile enjekte edilmiş olmalı
        this.webClient = this.webClientBuilder.baseUrl(this.aiServiceBaseUrl).build(); // WebClient'ı burada oluştur
        logger.info("NewsScheduler POSTCONSTRUCT: NewsScheduler bean initialized. aiServiceBaseUrl (after @Value injection): {}. WebClient configured.", aiServiceBaseUrl);
    }

    @Scheduled(cron = "${news.fetch.cron}", zone = "Europe/Istanbul")
    public void triggerDailyNewsFetch() {
        // METOD BAŞLANGIÇ LOGU
        logger.info("SCHEDULER_TASK_STARTED: triggerDailyNewsFetch called at {}", LocalDateTime.now());
        Instant startTime = Instant.now();
        try {
            newsService.fetchAndSaveAllConfiguredNewsReactive()
                    .doFinally(signalType -> {
                        Instant endTime = Instant.now();
                        long durationMillis = Duration.between(startTime, endTime).toMillis();
                        logger.info("SCHEDULER_TASK_FINISHED: triggerDailyNewsFetch finished at {}. Duration: {} ms. Signal type: {}",
                                endTime, durationMillis, signalType);
                    })
                    .subscribe(
                            null,
                            error -> {
                                logger.error("SCHEDULER_TASK_ERROR: Scheduled news fetch task encountered an unrecoverable error.", error);
                            },
                            () -> {
                                logger.info("SCHEDULER_TASK_SUCCESS: Scheduled news fetch task completed successfully. Triggering AI analysis...");
                                triggerAiAnalysis();
                            }
                    );
        } catch (Throwable e) { // Catch Throwable for more safety
            logger.error("SCHEDULER_TASK_UNEXPECTED_ERROR: Unexpected synchronous error during the initiation of scheduled news fetch task.", e);
            Instant endTime = Instant.now();
            long durationMillis = Duration.between(startTime, endTime).toMillis();
            logger.info("SCHEDULER_TASK_ABORTED: News fetch aborted at {}. Duration: {} ms.", endTime, durationMillis);
        }
    }

    private void triggerAiAnalysis() {
        if (this.webClient == null) { // Ekstra güvenlik kontrolü
            logger.error("SCHEDULER_TRIGGER_AI_ERROR: WebClient is not initialized!");
            return;
        }
        String endpoint = "/trigger-analysis";
        logger.info("SCHEDULER_TRIGGER_AI: Triggering AI analysis at: {}{}", aiServiceBaseUrl, endpoint);
        webClient.post()
                .uri(endpoint)
                .retrieve()
                .toBodilessEntity()
                .subscribe(
                        response -> {
                            if (response.getStatusCode() == HttpStatus.OK || response.getStatusCode() == HttpStatus.ACCEPTED) {
                                logger.info("SCHEDULER_TRIGGER_AI_SUCCESS: AI analysis triggered successfully");
                            } else {
                                logger.warn("SCHEDULER_TRIGGER_AI_WARN: AI analysis trigger returned unexpected status: {}", response.getStatusCode());
                            }
                        },
                        error -> logger.error("SCHEDULER_TRIGGER_AI_ERROR: Failed to trigger AI analysis", error)
                );
    }
}