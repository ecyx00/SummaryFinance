package com.example.summaryfinance.controller;

import com.example.summaryfinance.service.NotificationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.ZonedDateTime;

/**
 * Bildirim kontroller sınıfı.
 * Frontend istemcilere yeni analiz sonuçları hakkında bildirim göndermek için
 * hem SSE hem de polling tabanlı çözümler sunar.
 */
@RestController
@RequestMapping("/api")
public class SseNotificationController {

    private final NotificationService notificationService;
    
    @Autowired
    public SseNotificationController(NotificationService notificationService) {
        this.notificationService = notificationService;
    }
    
    /**
     * SSE akışını başlatan endpoint.
     * İstemcilere yeni analiz özetleri hakkında bildirim gönderir.
     * Not: Bu endpoint'i sadece yeni özet bildirimlerini almak için kullanın,
     * sürekli açık tutmayın.
     * 
     * @return SSE olay akışı
     */
    @GetMapping(path = "/summary-updates", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> streamSummaryUpdates() {
        // Client bağlandığında hemen başlangıç olayı gönder
        ServerSentEvent<String> connectEvent = ServerSentEvent.<String>builder()
                .event("connect")
                .data("SSE stream'e bağlantı başarılı - sadece yeni analizler olduğunda event gönderilecek")
                .build();
                
        // Bağlantı olayını ve gerçek bildirim akışını birleştir
        return Flux.concat(
            Flux.just(connectEvent),
            notificationService.getEventStream()
        );
    }
    
    /**
     * Frontend'in düzenli aralıklarla sorgulayabileceği endpoint.
     * Yeni analiz sonuçları olup olmadığını kontrol eder.
     * SSE'ye alternatif olarak sunulmuştur.
     * 
     * @param lastCheckTime Frontendde bilinen en son kontrol zamanı (ISO-8601 formatında)
     * @return Yeni özet olup olmadığı bilgisi
     */
    @GetMapping("/check-new-summaries")
    public Mono<ResponseEntity<Boolean>> checkNewSummaries(String lastCheckTime) {
        ZonedDateTime checkTime = lastCheckTime != null ? 
                ZonedDateTime.parse(lastCheckTime) : 
                ZonedDateTime.now().minusDays(1);
                
        return notificationService.hasNewSummariesSince(checkTime)
                .map(hasNew -> ResponseEntity.ok(hasNew));
    }
}
