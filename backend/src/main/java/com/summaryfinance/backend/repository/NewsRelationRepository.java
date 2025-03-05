package com.summaryfinance.backend.repository;

import com.summaryfinance.backend.model.NewsRelation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface NewsRelationRepository extends JpaRepository<NewsRelation, Long> {
    List<NewsRelation> findByClusterId(String clusterId);
} 