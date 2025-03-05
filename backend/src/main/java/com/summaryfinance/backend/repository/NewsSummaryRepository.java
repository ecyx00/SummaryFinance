package com.summaryfinance.backend.repository;

import com.summaryfinance.backend.model.NewsSummary;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface NewsSummaryRepository extends JpaRepository<NewsSummary, Long> {
} 