package com.summaryfinance.backend.repository;

import com.summaryfinance.backend.model.News;
import com.summaryfinance.backend.model.News.AnalysisStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface NewsRepository extends JpaRepository<News, Long> {
    List<News> findByCategory(String category);
    List<News> findBySourceName(String sourceName);
    List<News> findByAnalysisStatus(AnalysisStatus status);
    Long countByAnalysisStatus(AnalysisStatus status);
}
