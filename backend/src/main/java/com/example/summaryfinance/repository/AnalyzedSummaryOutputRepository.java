package com.example.summaryfinance.repository;

import com.example.summaryfinance.entity.AnalyzedSummaryOutput;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface AnalyzedSummaryOutputRepository extends JpaRepository<AnalyzedSummaryOutput, Long> {
    
    // Belirli bir tarihe ait özetleri bul
    List<AnalyzedSummaryOutput> findByPublicationDate(LocalDate publicationDate);
    
    // Tarih aralığına göre özetleri bul
    List<AnalyzedSummaryOutput> findByPublicationDateBetween(LocalDate startDate, LocalDate endDate);
    
    // Kategori içeren özetleri bul
    List<AnalyzedSummaryOutput> findByAssignedCategoriesContaining(String category);
} 