package com.example.summaryfinance.service;

import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.publisher.Sinks;

import java.time.LocalDateTime;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;

/**
 * SSE (Server-Sent Events) bildirim servisi.
 * Yeni analiz sonuçları geldiğinde frontend istemcilerine bildirim gönderir.
 */
@Service
public class NotificationService {
    
    // Tüm bağlı istemcilere bildirim göndermek için Reactor Sinks kullanılır
    private final Sinks.Many<ServerSentEvent<String>> eventSink;
    
    // Son özet güncellemesinin zaman damgasını tutar
    private final AtomicReference<LocalDateTime> lastSummaryUpdateTime;
    
    public NotificationService() {
        // Sınırsız arabellek ve çoklu abonelik desteği ile bir sink oluştur
        this.eventSink = Sinks.many().multicast().onBackpressureBuffer();
        this.lastSummaryUpdateTime = new AtomicReference<>(LocalDateTime.now());
    }
    
    /**
     * İstemci aboneliği için SSE stream'i döndürür
     * @return SSE olay akışı
     */
    public Flux<ServerSentEvent<String>> getEventStream() {
        return eventSink.asFlux();
    }
    
    /**
     * Yeni analiz özetleri kaydedildiğinde bildirim gönderir
     * @param timestamp Yeni özet kayıt zamanı
     */
    public void sendNewSummariesNotification(LocalDateTime timestamp) {
        // Son güncelleme zamanını ayarla
        this.lastSummaryUpdateTime.set(timestamp);
        
        ServerSentEvent<String> event = ServerSentEvent.<String>builder()
                .id(UUID.randomUUID().toString())
                .event("new_summaries_available")
                .data("{\"timestamp\":\"" + timestamp.toString() + "\"}")
                .build();
                
        // Sink'e yeni olay ekle
        Sinks.EmitResult result = eventSink.tryEmitNext(event);
        
        if (result.isFailure()) {
            // Hata durumunda loglama yapılabilir
            System.err.println("SSE olayı gönderilemedi: " + result);
        }
    }
    
    // Keep-alive sinyali artık gönderilmiyor - istemci tarafında yeniden bağlanma mantığı eklenmeli
    
    /**
     * Belirtilen tarihten sonra yeni özet eklenip eklenmediğini kontrol eder
     * @param since Kontrol başlangıç tarihi
     * @return Yeni özet varsa true, yoksa false döner
     */
    public Mono<Boolean> hasNewSummariesSince(LocalDateTime since) {
        LocalDateTime lastUpdate = this.lastSummaryUpdateTime.get();
        return Mono.just(lastUpdate != null && lastUpdate.isAfter(since));
    }
}
