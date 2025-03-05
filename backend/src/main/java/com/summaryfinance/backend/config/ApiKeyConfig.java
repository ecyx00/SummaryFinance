package com.summaryfinance.backend.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.PropertySource;

/**
 * API anahtarlarını ve gizli bilgileri güvenli bir şekilde yönetmek için yapılandırma sınıfı.
 * application.properties dosyasındaki değerleri okur.
 */
@Configuration
@PropertySource(value = "classpath:application.properties", ignoreResourceNotFound = true)
@PropertySource(value = "file:${user.home}/.summaryfinance/application-secrets.properties", ignoreResourceNotFound = true)
public class ApiKeyConfig {

    @Value("${guardian.api.key:}")
    private String guardianApiKey;

    @Value("${guardian.api.url:https://content.guardianapis.com/search}")
    private String guardianApiUrl;

    @Value("${gemini.api.key:}")
    private String geminiApiKey;

    @Value("${gemini.api.url:https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent}")
    private String geminiApiUrl;

    @Value("${reuters.api.key:}")
    private String reutersApiKey;

    @Value("${reuters.api.url:}")
    private String reutersApiUrl;

    @Value("${bloomberg.api.key:}")
    private String bloombergApiKey;

    @Value("${bloomberg.api.url:}")
    private String bloombergApiUrl;

    @Value("${ft.api.key:}")
    private String ftApiKey;

    @Value("${ft.api.url:}")
    private String ftApiUrl;

    public String getGuardianApiKey() {
        return guardianApiKey;
    }

    public String getGuardianApiUrl() {
        return guardianApiUrl;
    }

    public String getGeminiApiKey() {
        return geminiApiKey;
    }

    public String getGeminiApiUrl() {
        return geminiApiUrl;
    }

    public String getReutersApiKey() {
        return reutersApiKey;
    }

    public String getReutersApiUrl() {
        return reutersApiUrl;
    }

    public String getBloombergApiKey() {
        return bloombergApiKey;
    }

    public String getBloombergApiUrl() {
        return bloombergApiUrl;
    }

    public String getFtApiKey() {
        return ftApiKey;
    }

    public String getFtApiUrl() {
        return ftApiUrl;
    }
} 