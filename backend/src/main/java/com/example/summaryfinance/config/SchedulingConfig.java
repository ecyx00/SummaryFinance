package com.example.summaryfinance.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Zamanlı görevleri aktifleştiren konfigürasyon sınıfı.
 * NotificationService sınıfındaki keep-alive sinyali için gereklidir.
 */
@Configuration
@EnableScheduling
public class SchedulingConfig {
    // Ek konfigürasyon gerekmez, sadece @EnableScheduling anotasyonu yeterlidir
}
