package com.example.summaryfinance.client;

import com.example.summaryfinance.dto.NewsDTO;
import com.fasterxml.jackson.databind.JsonNode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration; // Duration import'u
import java.time.LocalDate;
import java.time.ZonedDateTime;
// import java.time.ZoneId; // Kullanılmıyor
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

@Component
public class GuardianClient implements NewsSourceClient {

    private final WebClient webClient;
    private static final String SOURCE_NAME = "The Guardian";
    private static final Logger logger = LoggerFactory.getLogger(GuardianClient.class);

    @Value("${guardian.api.key}")
    private String apiKey;

    private static final String API_BASE_URL = "https://content.guardianapis.com/search";
    private static final DateTimeFormatter GUARDIAN_DATE_FORMAT = DateTimeFormatter.ISO_LOCAL_DATE;
    private static final int PAGE_SIZE_GUARDIAN = 100;
    private static final int MAX_ITERATION_LIMIT_GUARDIAN = 20;

    @Value("${api.client.delay.guardian.ms:2000}") // application.properties'den default 2sn
    private long requestDelayMillis;

    public GuardianClient(WebClient.Builder webClientBuilder) {
        this.webClient = webClientBuilder.build();
    }

    @Override
    public String getSourceName() {
        return SOURCE_NAME;
    }

    @Override
    public Flux<NewsDTO> fetchNewsByTopic(String resolvedApiFilter, LocalDate startDate, LocalDate endDate) {
        if (apiKey == null || apiKey.trim().isEmpty()) {
            logger.error("Guardian API Key is missing or empty!");
            return Flux.error(new IllegalStateException("Guardian API Key is missing."));
        }
        if (resolvedApiFilter == null || resolvedApiFilter.trim().isEmpty()) {
            logger.error("Guardian client received an empty or null filter value.");
            return Flux.empty();
        }

        final String startDateStr = startDate.format(GUARDIAN_DATE_FORMAT);
        final String endDateStr = endDate.format(GUARDIAN_DATE_FORMAT);
        final String pageSizeParam = "page-size=" + PAGE_SIZE_GUARDIAN;
        final String dateParams = "&from-date=" + startDateStr + "&to-date=" + endDateStr;

        logger.info("Starting fetching Guardian news with filter: '{}', dates: {} to {}",
                resolvedApiFilter, startDateStr, endDateStr);

        AtomicBoolean continueFetching = new AtomicBoolean(true);

        return Flux.range(1, MAX_ITERATION_LIMIT_GUARDIAN) // Guardian page 1'den başlar
                // ---> GECİKME EKLEME <---
                .delayElements(Duration.ofMillis(requestDelayMillis))
                .concatMap(pageNumber -> {
                            if (!continueFetching.get()) {
                                return Flux.empty();
                            }
                            // fetchPageData metodu continueFetching'i güncelleyecek
                            return fetchPageData(resolvedApiFilter, dateParams, pageSizeParam, pageNumber, continueFetching)
                                    .collectList() // Sayfadaki tüm haberleri topla
                                    .flatMapMany(list -> {
                                        if (list.isEmpty()) {
                                            logger.info("Guardian Page {} for filter '{}' returned no results. Stopping pagination for this filter.", pageNumber, resolvedApiFilter);
                                            continueFetching.set(false); // Sonraki sayfaları çekmeyi durdur
                                            return Flux.empty(); // Bu sayfa boş, ama önceki haberler korunur
                                        }
                                        return Flux.fromIterable(list); // Doluysa haberleri emit et
                                    });
                        }
                        , 1);
        // takeWhile operatörü kaldırıldı
    }

    private Flux<NewsDTO> fetchPageData(String resolvedFilter, String dateParams, String pageSizeParam, int pageToFetch, AtomicBoolean continueFetchingSignal) {
        String pageParam = "page=" + pageToFetch;
        final String requestUrl = API_BASE_URL + "?api-key=" + apiKey + "&" + resolvedFilter + "&order-by=newest&" + pageSizeParam + dateParams + "&" + pageParam;
        logger.debug("Fetching Guardian data for page {} (filter: '{}') from URL: {}", pageToFetch, resolvedFilter, requestUrl);

        return webClient.get()
                .uri(requestUrl)
                .retrieve()
                .onStatus(status -> status.isError(), clientResponse -> {
                    logger.error("Guardian API Error on page {}: Status code {} for URL: {}", pageToFetch, clientResponse.statusCode(), requestUrl);
                    continueFetchingSignal.set(false);
                    return Mono.error(new RuntimeException("Guardian API Error: " + clientResponse.statusCode() + " for page " + pageToFetch + " with filter '" + resolvedFilter + "'"));
                })
                .bodyToMono(JsonNode.class)
                .flatMapMany(response -> {
                    if (response == null || !response.has("response")) {
                        logger.warn("Guardian Page {} (filter: '{}') returned invalid JSON structure (no 'response' field). Stopping.", pageToFetch, resolvedFilter);
                        continueFetchingSignal.set(false);
                        return Flux.empty();
                    }
                    JsonNode responseNode = response.path("response");

                    // ---> EK LOGLAMA <---
                    int totalResults = responseNode.path("total").asInt(-1);
                    int totalPagesFromApi = responseNode.path("pages").asInt(-1);
                    int currentPageFromApi = responseNode.path("currentPage").asInt(-1);
                    logger.info("Guardian API Response for page {}: TotalResults={}, TotalPages={}, CurrentPage={}", pageToFetch, totalResults, totalPagesFromApi, currentPageFromApi);
                    // ---> EK LOGLAMA BİTTİ <---

                    if (!responseNode.has("results") || !responseNode.path("results").isArray() || responseNode.path("results").isEmpty()) {
                        logger.info("Guardian Page {} (filter: '{}') returned no 'results' or 'results' is empty. Stopping pagination.", pageToFetch, resolvedFilter);
                        continueFetchingSignal.set(false);
                        return Flux.empty();
                    }

                    if (totalPagesFromApi > 0 && pageToFetch >= totalPagesFromApi) {
                        logger.info("Guardian Page {} (filter: '{}') is >= total pages ({}). Stopping pagination.", pageToFetch, resolvedFilter, totalPagesFromApi);
                        continueFetchingSignal.set(false);
                        // Bu sayfadaki sonuçları yine de parse et, ama bir sonrakini isteme
                    }
                    return parseJsonResponseToNewsDTOFlux(responseNode.path("results"), resolvedFilter);
                })
                .onErrorResume(e -> {
                    logger.error("Error processing or parsing data for Guardian page {} (filter: '{}') URL {}: {}", pageToFetch, resolvedFilter, requestUrl, e.getMessage());
                    continueFetchingSignal.set(false);
                    return Flux.empty();
                });
    }

    private Flux<NewsDTO> parseJsonResponseToNewsDTOFlux(JsonNode resultsNode, String filterContext) {
        List<NewsDTO> newsList = new ArrayList<>();
        if (resultsNode.isEmpty()){ // Zaten fetchPageData'da kontrol ediliyor ama burada da olabilir.
            // logger.info("Guardian results node is empty for filter: {}", filterContext);
            return Flux.empty();
        }

        for (JsonNode article : resultsNode) {
            String webUrl = article.path("webUrl").asText(null);
            if (webUrl == null || webUrl.isEmpty()) {
                logger.warn("Skipping Guardian article (filter: {}) due to missing URL. ID: {}", filterContext, article.path("id").asText("N/A"));
                continue;
            }
            try {
                NewsDTO news = new NewsDTO();
                news.setUrl(webUrl);
                String title = article.path("webTitle").asText(null);
                news.setTitle(title != null && !title.isEmpty() ? title : "Başlık Yok");
                String pubDateStr = article.path("webPublicationDate").asText(null);
                news.setPublicationDate(parseDate(pubDateStr));
                String sectionName = article.path("sectionName").asText(null);
                news.setSection(sectionName != null && !sectionName.isEmpty() ? sectionName : "Diğer");
                news.setSource(SOURCE_NAME);
                newsList.add(news);
            } catch (Exception e) {
                logger.error("Error parsing individual Guardian article JSON (URL: {}, filter: {}): {}", webUrl, filterContext, e.getMessage(), e);
            }
        }
        if (!newsList.isEmpty()) {
            logger.debug("Successfully parsed {} news items from Guardian results node for filter: {}", newsList.size(), filterContext);
        }
        return Flux.fromIterable(newsList);
    }

    private ZonedDateTime parseDate(String dateStr) {
        if (dateStr == null || dateStr.isEmpty()) { return null; }
        try {
            return ZonedDateTime.parse(dateStr, DateTimeFormatter.ISO_OFFSET_DATE_TIME);
        } catch (Exception e) {
            logger.warn("Could not parse date string with ISO_OFFSET_DATE_TIME format for Guardian: {}", dateStr);
            return null;
        }
    }
}