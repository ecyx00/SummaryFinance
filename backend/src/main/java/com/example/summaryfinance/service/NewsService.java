package com.example.summaryfinance.service;

import com.example.summaryfinance.client.NewsSourceClient;
import com.example.summaryfinance.dto.NewsDTO;
import com.example.summaryfinance.entity.News;
import com.example.summaryfinance.mapper.NewsMapper;
import com.example.summaryfinance.repository.NewsRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class NewsService {

    private final List<NewsSourceClient> newsSourceClients;
    private final NewsRepository newsRepository;
    private final NewsMapper newsMapper;
    private final Environment environment;
    private static final Logger logger = LoggerFactory.getLogger(NewsService.class);

    @Value("${app.nytimes.enabled.keys:}")
    private String nytimesEnabledKeysCsv;

    @Value("${app.guardian.enabled.keys:}")
    private String guardianEnabledKeysCsv;

    @Value("${api.client.inter-topic.delay.nytimes.ms:12000}") // application.properties'den
    private long interTopicDelayNytMs;

    @Value("${api.client.inter-topic.delay.guardian.ms:2000}") // application.properties'den
    private long interTopicDelayGuardianMs;


    public NewsService(List<NewsSourceClient> newsSourceClients,
                       NewsRepository newsRepository,
                       NewsMapper newsMapper,
                       Environment environment) {
        this.newsSourceClients = newsSourceClients;
        this.newsRepository = newsRepository;
        this.newsMapper = newsMapper;
        this.environment = environment;
    }

    public Mono<Void> fetchAndSaveAllConfiguredNewsReactive() {
        logger.info("Starting reactive news fetching process for all configured topics...");
        final LocalDate endDate = LocalDate.now(); // Effectively final
        final LocalDate startDate = endDate.minusDays(1); // Effectively final

        List<String> nytimesTopicKeys = getEnabledTopicKeys(nytimesEnabledKeysCsv);
        List<String> guardianTopicKeys = getEnabledTopicKeys(guardianEnabledKeysCsv);

        logger.debug("NYTimes topics to fetch (keys from properties): {}", nytimesTopicKeys);
        logger.debug("Guardian topics to fetch (keys from properties): {}", guardianTopicKeys);

        Flux<NewsDTO> guardianNewsStream = Flux.empty();
        NewsSourceClient guardianClient = newsSourceClients.stream()
                .filter(c -> "The Guardian".equals(c.getSourceName())).findFirst().orElse(null);

        if (guardianClient != null && !guardianTopicKeys.isEmpty()) {
            final NewsSourceClient finalGuardianClient = guardianClient; // Effectively final
            guardianNewsStream = Flux.fromIterable(guardianTopicKeys)
                    .concatMap(topicKey -> {
                        String apiFilter = environment.getProperty("guardian.filter." + topicKey);
                        if (apiFilter == null || apiFilter.isEmpty()) {
                            logger.warn("Filter not found for Guardian topic key '{}'. Skipping.", topicKey);
                            return Flux.empty();
                        }
                        logger.info("Guardian: Initiating fetch for topic key '{}', filter '{}'", topicKey, apiFilter);
                        return finalGuardianClient.fetchNewsByTopic(apiFilter, startDate, endDate)
                                .doOnError(e -> logger.error("Guardian: Error on topic key '{}': {}", topicKey, e.getMessage()))
                                .onErrorResume(e -> Flux.empty())
                                // Her topic bittikten sonra (tüm sayfaları çekildikten sonra) bir sonraki topic'e geçmeden önce gecikme
                                .delaySequence(Duration.ofMillis(interTopicDelayGuardianMs));
                    }, 3); // Prefetch değeri 3 olarak ayarlandı, daha fazla paralel işlem için
        }

        Flux<NewsDTO> nytimesNewsStream = Flux.empty();
        NewsSourceClient nytClient = newsSourceClients.stream()
                .filter(c -> "The New York Times".equals(c.getSourceName())).findFirst().orElse(null);

        if (nytClient != null && !nytimesTopicKeys.isEmpty()) {
            final NewsSourceClient finalNytClient = nytClient; // Effectively final
            nytimesNewsStream = Flux.fromIterable(nytimesTopicKeys)
                    .concatMap(topicKey -> {
                        String apiFilter = environment.getProperty("nytimes.filter." + topicKey);
                        if (apiFilter == null || apiFilter.isEmpty()) {
                            logger.warn("Filter not found for NYT topic key '{}'. Skipping.", topicKey);
                            return Flux.empty();
                        }
                        logger.info("NYTimes: Initiating fetch for topic key '{}', filter '{}'", topicKey, apiFilter);
                        return finalNytClient.fetchNewsByTopic(apiFilter, startDate, endDate)
                                .doOnError(e -> logger.error("NYTimes: Error on topic key '{}': {}", topicKey, e.getMessage()))
                                .onErrorResume(e -> Flux.empty())
                                // Her topic bittikten sonra (tüm sayfaları çekildikten sonra) bir sonraki topic'e geçmeden önce gecikme
                                .delaySequence(Duration.ofMillis(interTopicDelayNytMs));
                    }, 2); // Prefetch değeri 2 olarak ayarlandı, NYT için daha düşük tutuyoruz (rate limit nedeniyle)
        }

        // Guardian ve NYTimes akışlarını paralel işlemek için Flux.merge kullanıyoruz
        // Bu şekilde toplam işlem süresi önemli ölçüde kısalacak
        return Flux.merge(guardianNewsStream, nytimesNewsStream)
                .doOnNext(dto -> {
                    logger.info("[DEBUG] DTO EMITTED TO FINAL MERGE (Source: {}): URL - {}", dto.getSource(), dto.getUrl());
                })
                .collectList()
                .flatMap(newsDTOs -> {
                    long guardianCountInCollectedList = newsDTOs.stream().filter(d -> "The Guardian".equals(d.getSource())).count();
                    long nytimesCountInCollectedList = newsDTOs.stream().filter(d -> "The New York Times".equals(d.getSource())).count();
                    logger.info("[DEBUG] Total DTOs in collectedList for deduplication: {}, Guardian DTOs: {}, NYTimes DTOs: {}",
                            newsDTOs.size(), guardianCountInCollectedList, nytimesCountInCollectedList);

                    if (newsDTOs.isEmpty()) {
                        logger.info("No news items were fetched or all were filtered out.");
                        return Mono.just(0L);
                    }
                    return this.deduplicateAndSaveNews(newsDTOs);
                })
                .doOnSuccess(count -> {
                    if (count != null && count > 0) {
                        logger.info("Successfully processed and saved {} new news items in total.", count);
                    } else {
                        logger.info("Processing complete. No new news items were saved.");
                    }
                })
                .doOnError(e -> logger.error("Error during the final news deduplication process: {}", e.getMessage(), e))
                .then()
                .doFinally(signalType -> {
                    logger.info("Overall news fetching and saving process has finished. Final signal type: {}", signalType);
                });
    }

    private List<String> getEnabledTopicKeys(String csvString) {
        if (csvString == null || csvString.trim().isEmpty()) {
            return List.of();
        }
        return Arrays.stream(csvString.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .collect(Collectors.toList());
    }

    private Mono<Long> deduplicateAndSaveNews(List<NewsDTO> newsDTOs) {
        if (newsDTOs.isEmpty()) {
            logger.info("deduplicateAndSaveNews called with an empty list. No action taken.");
            return Mono.just(0L);
        }
        return Mono.fromCallable(() -> {
            logger.info("Processing {} fetched news items for deduplication and saving.", newsDTOs.size());
            Set<String> incomingUrls = newsDTOs.stream()
                    .map(NewsDTO::getUrl)
                    .filter(Objects::nonNull)
                    .filter(url -> !url.isEmpty())
                    .collect(Collectors.toSet());
            if (incomingUrls.isEmpty()) {
                logger.warn("No valid URLs found in the fetched news items list for deduplication.");
                return 0L;
            }
            Set<String> existingUrls = newsRepository.findExistingUrls(incomingUrls);
            logger.debug("Found {} existing URLs in the database out of {} incoming unique URLs.", existingUrls.size(), incomingUrls.size());
            List<News> newsToSave = newsDTOs.stream()
                    .filter(dto -> dto.getUrl() != null && !dto.getUrl().isEmpty() && !existingUrls.contains(dto.getUrl()))
                    .map(newsMapper::toEntity)
                    .collect(Collectors.toList());
            if (!newsToSave.isEmpty()) {
                LocalDateTime now = LocalDateTime.now();
                for (News newsEntity : newsToSave) {
                    if (newsEntity.getTitle() == null || newsEntity.getTitle().isEmpty()) newsEntity.setTitle("Başlık Yok");
                    if (newsEntity.getSection() == null || newsEntity.getSection().isEmpty()) newsEntity.setSection("Diğer");
                    if (newsEntity.getPublicationDate() == null) {
                        logger.warn("News entity with URL {} has null publicationDate. Setting to (now - 1 hour).", newsEntity.getUrl());
                        newsEntity.setPublicationDate(now.minusHours(1));
                    }
                    newsEntity.setFetchedAt(now);
                }
                newsRepository.saveAll(newsToSave);
                logger.info("Saved {} new news items to database.", newsToSave.size());
                return (long) newsToSave.size();
            } else {
                logger.info("No new news items to save after deduplication.");
                return 0L;
            }
        }).subscribeOn(Schedulers.boundedElastic());
    }

    public List<NewsDTO> getAllNews() { return newsMapper.toDtoList(newsRepository.findAll()); }
    public List<NewsDTO> getNewsBySection(String section) { return newsMapper.toDtoList(newsRepository.findBySection(section)); }
    public List<NewsDTO> getNewsByDateRange(LocalDateTime start, LocalDateTime end) { return newsMapper.toDtoList(newsRepository.findByPublicationDateBetween(start, end)); }
    public List<NewsDTO> getNewsBySource(String source) { return newsMapper.toDtoList(newsRepository.findBySource(source)); }
}