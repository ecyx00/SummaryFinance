package com.example.summaryfinance.service;

import com.example.summaryfinance.client.NewsSourceClient;
import com.example.summaryfinance.dto.NewsDTO;
import com.example.summaryfinance.entity.News;
import com.example.summaryfinance.mapper.NewsMapper;
import com.example.summaryfinance.repository.NewsRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
public class NewsService {

    private final List<NewsSourceClient> newsSourceClients;
    private final NewsRepository newsRepository;
    private final NewsMapper newsMapper;
    private static final Logger logger = LoggerFactory.getLogger(NewsService.class);

    public NewsService(List<NewsSourceClient> newsSourceClients,
                       NewsRepository newsRepository,
                       NewsMapper newsMapper) {
        this.newsSourceClients = newsSourceClients;
        this.newsRepository = newsRepository;
        this.newsMapper = newsMapper;
    }

    public void fetchAllBusinessNews() {
        List<NewsDTO> allNews = new ArrayList<>();

        // Fetch news from all sources
        for (NewsSourceClient client : newsSourceClients) {
            try {
                logger.info("Fetching news from {}", client.getSourceName());
                List<NewsDTO> newsFromSource = client.fetchBusinessNews();
                logger.info("Fetched {} news items from {}", newsFromSource.size(), client.getSourceName());
                allNews.addAll(newsFromSource);
            } catch (Exception e) {
                logger.error("Error fetching news from {}: {}", client.getSourceName(), e.getMessage(), e);
            }
        }

        logger.info("Total news items fetched: {}", allNews.size());

        // Save all news to database
        saveNews(allNews);
    }

    private void saveNews(List<NewsDTO> newsDTOs) {
        List<News> newsEntities = newsMapper.toEntityList(newsDTOs);
        newsRepository.saveAll(newsEntities);
        logger.info("Saved {} news items to database", newsEntities.size());
    }

    public List<NewsDTO> getAllNews() {
        List<News> newsEntities = newsRepository.findAll();
        return newsMapper.toDtoList(newsEntities);
    }

    public List<NewsDTO> getNewsBySection(String section) {
        List<News> newsEntities = newsRepository.findBySection(section);
        return newsMapper.toDtoList(newsEntities);
    }

    public List<NewsDTO> getNewsByDateRange(LocalDateTime start, LocalDateTime end) {
        List<News> newsEntities = newsRepository.findByPublicationDateBetween(start, end);
        return newsMapper.toDtoList(newsEntities);
    }

    public List<NewsDTO> getNewsBySource(String source) {
        List<News> newsEntities = newsRepository.findBySource(source);
        return newsMapper.toDtoList(newsEntities);
    }
}