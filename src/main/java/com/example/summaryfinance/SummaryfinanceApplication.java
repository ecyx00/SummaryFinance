package com.example.summaryfinance;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class SummaryfinanceApplication {

    public static void main(String[] args) {
        System.out.println("Starting SummaryFinance application...");
        SpringApplication.run(SummaryfinanceApplication.class, args);
        System.out.println("SummaryFinance application started successfully!");
    }
}