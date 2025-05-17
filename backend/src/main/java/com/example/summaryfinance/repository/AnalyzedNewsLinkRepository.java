package com.example.summaryfinance.repository;

import com.example.summaryfinance.entity.AnalyzedNewsLink;
import com.example.summaryfinance.entity.AnalyzedSummaryOutput;
import com.example.summaryfinance.entity.News;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AnalyzedNewsLinkRepository extends JpaRepository<AnalyzedNewsLink, Long> {
    
    // Belirli bir özete ait haber bağlantılarını bul
    List<AnalyzedNewsLink> findByAnalyzedSummaryOutput(AnalyzedSummaryOutput analyzedSummaryOutput);
    
    // Belirli bir haberin yer aldığı özet bağlantılarını bul
    List<AnalyzedNewsLink> findByOriginalNews(News originalNews);
    
    // Belirli bir özetle ilişkili orijinal haberleri bul
    @Query("SELECT anl.originalNews FROM AnalyzedNewsLink anl WHERE anl.analyzedSummaryOutput.id = :summaryId")
    List<News> findOriginalNewsBySummaryId(@Param("summaryId") Long summaryId);
    
    // Belirli bir haberle ilişkili özetleri bul
    @Query("SELECT anl.analyzedSummaryOutput FROM AnalyzedNewsLink anl WHERE anl.originalNews.id = :newsId")
    List<AnalyzedSummaryOutput> findSummariesByNewsId(@Param("newsId") Long newsId);
} 