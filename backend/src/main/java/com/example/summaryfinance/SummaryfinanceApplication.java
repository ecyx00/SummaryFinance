package com.example.summaryfinance;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication
@EnableScheduling // Zamanlanmış görevleri etkinleştir
@EnableJpaRepositories(basePackages = "com.example.summaryfinance.repository") // Repository paketini belirtir
public class SummaryfinanceApplication {

    private static final Logger logger = LoggerFactory.getLogger(SummaryfinanceApplication.class);

    public static void main(String[] args) {
        logger.info("Attempting to start SummaryFinance application...");
        try {
            SpringApplication.run(SummaryfinanceApplication.class, args);
            logger.info("SummaryFinance application context initialized. Application should be running.");
        } catch (Exception e) {
            logger.error("Failed to start SummaryFinance application due to an exception.", e);
        }
    }
}