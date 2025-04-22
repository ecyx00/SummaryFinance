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
public class NYTimesClient implements NewsSourceClient {
    private final WebClient webClient;
    private static final String SOURCE_NAME = "The New York Times";

    @Value("${nytimes.api.key}")
    private String apiKey;

    public NYTimesClient(WebClient webClient) {
        this.webClient = webClient;
    }

    @Override
    public List<NewsDTO> fetchBusinessNews() {
        try {
            JsonNode response = webClient.get()
                    .uri("https://api.nytimes.com/svc/search/v2/articlesearch.json?api-key=" + apiKey + "&fq=new_desk:\"Business\"&sort=newest")
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

        if (response != null && response.has("response") && response.get("response").has("docs")) {
            JsonNode docs = response.get("response").get("docs");

            for (JsonNode article : docs) {
                NewsDTO news = new NewsDTO();
                news.setId(article.path("_id").asText());
                news.setUrl(article.path("web_url").asText());
                String dateStr = article.path("pub_date").asText();
                news.setPublicationDate(parseDate(dateStr));
                news.setSection(article.path("section_name").asText("Business"));
                news.setSource(SOURCE_NAME);

                newsList.add(news);
            }
        }

        return newsList;
    }

    private LocalDateTime parseDate(String dateStr) {
        try {
            return LocalDateTime.parse(dateStr, DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ssXXX"));
        } catch (Exception e) {
            try {
                return LocalDateTime.parse(dateStr, DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'"));
            } catch (Exception e2) {
                return LocalDateTime.now();
            }
        }
    }
}