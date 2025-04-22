package com.example.summaryfinance.repository;

import com.example.summaryfinance.entity.News;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface NewsRepository extends JpaRepository<News, String> {

    List<News> findBySection(String section);

    List<News> findByPublicationDateBetween(LocalDateTime start, LocalDateTime end);

    List<News> findBySource(String source);

    List<News> findBySectionAndPublicationDateBetween(String section, LocalDateTime start, LocalDateTime end);
}