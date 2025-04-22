package com.example.summaryfinance.client;

import com.example.summaryfinance.dto.NewsDTO;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

@Component
public class GuardianClient implements NewsSourceClient {
    private final WebClient webClient;
    private static final String SOURCE_NAME = "The Guardian";

    @Value("${guardian.api.key}")
    private String apiKey;

    public GuardianClient(WebClient webClient) {
        this.webClient = webClient;
    }

    @Override
    public List<NewsDTO> fetchBusinessNews() {
        try {
            JsonNode response = webClient.get()
                    .uri("https://content.guardianapis.com/search?api-key=" + apiKey + "&section=business&order-by=newest")
                    .retrieve()
                    .bodyToMono(JsonNode.class)
                    .block();

            return parseResponse(response);
        } catch (Exception e) {
            return new ArrayList<>();
        }
    }

    @Override
    public String getSourceName() {
        return SOURCE_NAME;
    }

    private List<NewsDTO> parseResponse(JsonNode response) {
        List<NewsDTO> newsList = new ArrayList<>();

        if (response != null && response.has("response") && response.get("response").has("results")) {
            JsonNode results = response.get("response").get("results");

            for (JsonNode article : results) {
                NewsDTO news = new NewsDTO();
                news.setId(article.path("id").asText());
                news.setUrl(article.path("webUrl").asText());
                news.setPublicationDate(parseDate(article.path("webPublicationDate").asText()));
                news.setSection(article.path("sectionName").asText());
                news.setSource(SOURCE_NAME);

                newsList.add(news);
            }
        }

        return newsList;
    }

    private LocalDateTime parseDate(String dateStr) {
        try {
            return LocalDateTime.parse(dateStr, DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'"));
        } catch (Exception e) {
            return LocalDateTime.now();
        }
    }
}