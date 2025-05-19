package com.example.summaryfinance.scheduler;

import com.example.summaryfinance.service.NewsService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration; // Duration import'u
import java.time.Instant; // Instant import'u

/**
 * Haber çekme işlemini periyodik olarak tetikleyen zamanlanmış görev.
 * İşlemin başlangıcını, sonucunu ve süresini loglar.
 */
@Component
public class NewsScheduler {

    private static final Logger logger = LoggerFactory.getLogger(NewsScheduler.class);
    private final NewsService newsService;
    private final WebClient webClient;
    
    @Value("${ai.service.url:http://localhost:8000}")
    private String aiServiceBaseUrl;

    public NewsScheduler(NewsService newsService, WebClient.Builder webClientBuilder) {
        this.newsService = newsService;
        this.webClient = webClientBuilder.baseUrl(aiServiceBaseUrl).build();
    }

    /**
     * application.properties dosyasındaki 'news.fetch.cron' ifadesine göre
     * periyodik olarak çalışır ve haber çekme servisini tetikler.
     * Varsayılan olarak her gün sabah 5'te çalışır.
     */
    @Scheduled(cron = "${news.fetch.cron:0 0 5 * * ?}")
    public void triggerDailyNewsFetch() {
        Instant startTime = Instant.now(); // İşlem başlangıç zamanı
        logger.info("Scheduled news fetch task started at {}", startTime);

        try {
            // NewsService'deki güncellenmiş reaktif metodu çağır
            newsService.fetchAndSaveAllConfiguredNewsReactive() // <--- METOD ADI GÜNCELLENDİ
                    .doFinally(signalType -> { // Akış her durumda bittiğinde (başarılı, hatalı, iptal) çalışır
                        Instant endTime = Instant.now();
                        long durationMillis = Duration.between(startTime, endTime).toMillis();
                        // signalType, akışın nasıl sonlandığını belirtir (e.g., ON_COMPLETE, ON_ERROR, CANCEL)
                        logger.info("Scheduled news fetch task finished at {}. Duration: {} ms. Signal type: {}",
                                endTime, durationMillis, signalType);
                    })
                    .subscribe(
                            null, // onNext: Mono<Void> için genellikle kullanılmaz.
                            error -> { // onError: Akış bir hatayla sonlandığında çalışır.
                                // Hatanın kendisi (stack trace dahil) newsService içinde zaten loglanmış olabilir.
                                // Burada genel bir hata mesajı loglayabiliriz.
                                logger.error("Scheduled news fetch task encountered an unrecoverable error.", error);
                                // İsteğe bağlı: Burada bir bildirim mekanizması (e-posta, Slack vs.) tetiklenebilir.
                            },
                            () -> { // onComplete: Akış başarıyla ve hatasız tamamlandığında çalışır.
                                // Başarı logu zaten doFinally içinde genel olarak atılıyor.
                                logger.info("Scheduled news fetch task completed successfully. Triggering AI analysis...");
                                
                                // Python AI servisini tetikle
                                triggerAiAnalysis();
                            }
                    );
        } catch (Exception e) {
            // Bu blok, newsService.fetchAndSaveAllConfiguredNewsReactive() çağrısı
            // subscribe edilmeden ÖNCE bir senkron hata fırlatırsa yakalar (çok nadir bir durum).
            // Reaktif akıştaki hatalar .subscribe() içindeki onError bloğunda yakalanır.
            logger.error("Unexpected synchronous error during the initiation of scheduled news fetch task.", e);
            Instant endTime = Instant.now();
            long durationMillis = Duration.between(startTime, endTime).toMillis();
            logger.info("Scheduled news fetch task aborted due to an unexpected synchronous error at {}. Duration: {} ms.", endTime, durationMillis);
        }
    }
    
    /**
     * Python AI servisinin /trigger-analysis endpoint'ine HTTP POST isteği gönderir.
     * Bu metod, haber çekme işlemi başarıyla tamamlandığında çağrılır.
     */
    private void triggerAiAnalysis() {
        String endpoint = "/trigger-analysis";
        logger.info("Triggering AI analysis at: {}{}", aiServiceBaseUrl, endpoint);
        
        webClient.post()
                .uri(endpoint) // sadece path kullanıyoruz, baseUrl webClient'da zaten tanımlı
                .retrieve()
                .toBodilessEntity()
                .subscribe(
                        response -> {
                            if (response.getStatusCode() == HttpStatus.OK || response.getStatusCode() == HttpStatus.ACCEPTED) {
                                logger.info("AI analysis triggered successfully");
                            } else {
                                logger.warn("AI analysis trigger returned unexpected status: {}", response.getStatusCode());
                            }
                        },
                        error -> logger.error("Failed to trigger AI analysis", error)
                );
    }
}