package com.summaryfinance.backend.repository;

import com.summaryfinance.backend.model.News;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface NewsRepository extends JpaRepository<News, Long> {
    List<News> findTop20ByOrderByPublishedDateDesc();
    List<News> findByCategoryOrderByPublishedDateDesc(String category);
    Optional<News> findByGuardianId(String guardianId);
    List<News> findByAnalysisStatus(News.AnalysisStatus status);
    List<News> findBySourceName(String sourceName);
}
