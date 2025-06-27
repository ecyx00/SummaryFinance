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

import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZonedDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * NYTimes API'sinden haber metadata'sı çeken istemci.
 * Belirtilen API'ye özgü filtre string'i ve tarih aralığına göre
 * dinamik sayfalama yaparak ilgili haberleri getirir.
 */
@Component
public class NYTimesClient implements NewsSourceClient {

    private final WebClient webClient;
    private static final String SOURCE_NAME = "The New York Times";
    private static final Logger logger = LoggerFactory.getLogger(NYTimesClient.class);

    @Value("${nytimes.api.key}")
    private String apiKey;

    private static final String API_BASE_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json";
    private static final DateTimeFormatter NYT_DATE_FORMAT = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final int MAX_PAGES_NYT = 20; // NYT API limiti 100 sayfa olmasına rağmen, işlem süresini kısaltmak için sınırlama yapıyoruz

    @Value("${api.client.delay.nytimes.ms:10000}") // application.properties'den, default 10 saniye
    private long requestDelayMillis;

    public NYTimesClient(WebClient.Builder webClientBuilder) {
        this.webClient = webClientBuilder.build();
    }

    @Override
    public String getSourceName() {
        return SOURCE_NAME;
    }

    @Override
    public Flux<NewsDTO> fetchNewsByTopic(String resolvedApiFilter, LocalDate startDate, LocalDate endDate) {
        if (apiKey == null || apiKey.trim().isEmpty()) {
            logger.error("NYTimes API Key is missing or empty!");
            return Flux.error(new IllegalStateException("NYTimes API Key is missing."));
        }
        // NewsService zaten çözülmüş filtreyi gönderiyor (örn: "desk:\"Business\" OR section_name:\"Business\"")
        if (resolvedApiFilter == null || resolvedApiFilter.trim().isEmpty()) {
            logger.error("NYTimes client received an empty or null filter value from NewsService.");
            return Flux.empty();
        }

        final String startDateStr = startDate.format(NYT_DATE_FORMAT);
        final String endDateStr = endDate.format(NYT_DATE_FORMAT);

        logger.info("Starting fetching NYT news with filter: '{}', dates: {} to {}",
                resolvedApiFilter, startDateStr, endDateStr);

        AtomicBoolean continueFetching = new AtomicBoolean(true);

        return Flux.range(0, MAX_PAGES_NYT) // 0'dan 99'a kadar potansiyel sayfa numaraları
                // Her sayfa numarası üretildikten SONRA ve bir sonraki concatMap işleminden ÖNCE bekle
                .delayElements(Duration.ofMillis(requestDelayMillis))
                .concatMap(pageNumber -> {
                            if (!continueFetching.get()) {
                                return Flux.empty(); // Eğer önceki sayfa boşsa veya hata oluştuysa, daha fazla istek yapma
                            }
                            return fetchPageData(resolvedApiFilter, startDateStr, endDateStr, pageNumber)
                                    .collectList() // Sayfadaki tüm haberleri topla
                                    .flatMapMany(list -> {
                                        if (list.isEmpty()) {
                                            // Bu sayfa boş geldiyse, muhtemelen daha fazla sonuç yoktur (veya API hatası).
                                            logger.info("NYT Page {} for filter '{}' returned no results. Stopping pagination for this filter.", pageNumber, resolvedApiFilter);
                                            continueFetching.set(false); // Sonraki sayfaları çekmeyi durdur
                                            return Flux.empty(); // Bu sayfa boş, akışa bir şey emit etme
                                        }
                                        return Flux.fromIterable(list); // Doluysa haberleri emit et
                                    });
                        }
                        , 1) // Prefetch = 1, sayfaların sırayla ve bir önceki bitince işlenmesi için önemli
                .takeWhile(newsDTO -> continueFetching.get()); // continueFetching false olunca tüm akışı kes
    }

    private Flux<NewsDTO> fetchPageData(String resolvedFilter, String startDate, String endDate, int pageToFetch) {
        String pageParam = "page=" + pageToFetch;
        final String requestUrl = API_BASE_URL + "?api-key=" + apiKey + "&fq=" + resolvedFilter + "&sort=newest&" + pageParam + "&begin_date=" + startDate + "&end_date=" + endDate;
        logger.debug("Fetching NYT data for page {} (filter: '{}') from URL: {}", pageToFetch, resolvedFilter, requestUrl);

        return webClient.get()
                .uri(requestUrl)
                .retrieve()
                .onStatus(status -> status.isError(), clientResponse -> {
                    logger.error("NYTimes API Error on page {}: Status code {} for URL: {}", pageToFetch, clientResponse.statusCode(), requestUrl);
                    // Hata durumunda bu sayfa için akışı sonlandıracak bir hata fırlat
                    // onErrorResume bunu yakalayacak ve Flux.empty() dönecek, continueFetching false olacak.
                    return Mono.error(new RuntimeException("NYTimes API Error: " + clientResponse.statusCode() + " for page " + pageToFetch + " with filter '" + resolvedFilter + "'"));
                })
                .bodyToMono(JsonNode.class)
                .flatMapMany(response -> {
                    // Sayfa boşsa veya docs yoksa veya docs boş bir diziyse boş Flux dön
                    if (response == null || !response.has("response") || !response.path("response").has("docs") || !response.path("response").path("docs").isArray()) {
                        logger.warn("NYT Page {} (filter: '{}') returned invalid JSON structure or no 'docs' array. Assuming no more data.", pageToFetch, resolvedFilter);
                        return Flux.empty(); // Bu sayfa için sonuç yok, sayfalama duracak
                    }
                    JsonNode docsNode = response.path("response").path("docs");
                    // docsNode.isEmpty() kontrolü parseJsonResponseToNewsDTOFlux içinde yapılacak
                    return parseJsonResponseToNewsDTOFlux(docsNode, resolvedFilter);
                })
                .onErrorResume(e -> {
                    // API hatası (onStatus'tan gelen) veya parse hatası olursa logla ve bu sayfa için boş dön
                    logger.error("Error processing or parsing data for NYT page {} (filter: '{}') URL {}: {}", pageToFetch, resolvedFilter, requestUrl, e.getMessage());
                    return Flux.empty(); // Bu sayfanın hatası diğerlerini etkilemesin, ama sayfalama duracak (continueFetching false yapılacak)
                });
    }

    private Flux<NewsDTO> parseJsonResponseToNewsDTOFlux(JsonNode docsNode, String filterContext) {
        List<NewsDTO> newsList = new ArrayList<>();
        if (docsNode.isEmpty()){ // Eğer docs dizisi boşsa, bu sayfada haber yoktur.
            // fetchPageData'daki collectList().flatMapMany bloğu bu boş listeyi alıp continueFetching'i false yapacak.
            return Flux.empty();
        }

        for (JsonNode article : docsNode) {
            String webUrl = article.path("web_url").asText(null);
            if (webUrl == null || webUrl.isEmpty()) {
                logger.warn("Skipping NYTimes article (filter: {}) due to missing URL. ID: {}", filterContext, article.path("_id").asText("N/A"));
                continue;
            }
            try {
                NewsDTO news = new NewsDTO();
                news.setUrl(webUrl);

                JsonNode headlineNode = article.path("headline");
                String title = headlineNode.has("main") ? headlineNode.path("main").asText(null) : null;
                news.setTitle(title != null && !title.isEmpty() ? title : "Başlık Yok");

                String pubDateStr = article.path("pub_date").asText(null);
                news.setPublicationDate(parseDate(pubDateStr));

                String sectionName = article.path("section_name").asText(null);
                String newsDesk = article.path("news_desk").asText(null);
                String finalSection = "Diğer"; // Default

                if (sectionName != null && !sectionName.isEmpty()) {
                    finalSection = sectionName;
                } else if (newsDesk != null && !newsDesk.isEmpty()) {
                    finalSection = newsDesk;
                }
                news.setSection(finalSection); // API'den gelen ham section

                news.setSource(SOURCE_NAME);
                newsList.add(news);
            } catch (Exception e) {
                logger.error("Error parsing individual NYTimes article JSON (URL: {}, filter: {}): {}", webUrl, filterContext, e.getMessage(), e);
            }
        }
        if (!newsList.isEmpty()) {
            logger.debug("Successfully parsed {} news items from NYTimes docs node for filter: {}", newsList.size(), filterContext);
        }
        return Flux.fromIterable(newsList);
    }

    private ZonedDateTime parseDate(String dateStr) {
        if (dateStr == null || dateStr.isEmpty()) { return null; }
        List<DateTimeFormatter> formatters = List.of(
                DateTimeFormatter.ISO_OFFSET_DATE_TIME,
                DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ssXXX"),
                DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'")
        );
        for (DateTimeFormatter formatter : formatters) {
            try {
                // Öncelikle ZonedDateTime olarak parse etmeyi dene
                try {
                    return ZonedDateTime.parse(dateStr, formatter);
                } catch (Exception e) {
                    // ZonedDateTime olarak parse edilemiyorsa, LocalDateTime olarak parse et ve UTC zaman dilimine çevir
                    return LocalDateTime.parse(dateStr, formatter).atZone(ZoneId.of("UTC"));
                }
            } catch (Exception e) { /* Ignore */ }
        }
        logger.warn("Could not parse date string with any known NYT format: {}", dateStr);
        return null;
    }
}