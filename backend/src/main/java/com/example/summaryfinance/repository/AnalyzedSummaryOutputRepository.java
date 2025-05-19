package com.example.summaryfinance.repository;

import com.example.summaryfinance.entity.AnalyzedSummaryOutput;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface AnalyzedSummaryOutputRepository extends JpaRepository<AnalyzedSummaryOutput, Long> {
    
    // Belirli bir tarihe ait özetleri bul - Liste
    List<AnalyzedSummaryOutput> findByPublicationDate(LocalDate publicationDate);
    
    // Belirli bir tarihe ait özetleri bul - Sayfalama destekli
    Page<AnalyzedSummaryOutput> findByPublicationDate(LocalDate publicationDate, Pageable pageable);
    
    // Tarih aralığına göre özetleri bul
    List<AnalyzedSummaryOutput> findByPublicationDateBetween(LocalDate startDate, LocalDate endDate);
    
    // Tarih aralığına göre özetleri bul - Sayfalama destekli
    Page<AnalyzedSummaryOutput> findByPublicationDateBetween(LocalDate startDate, LocalDate endDate, Pageable pageable);
    
    // Kategori içeren özetleri bul
    List<AnalyzedSummaryOutput> findByAssignedCategoriesContaining(String category);
    
    // Kategori içeren özetleri bul - Sayfalama destekli
    Page<AnalyzedSummaryOutput> findByAssignedCategoriesContaining(String category, Pageable pageable);
    
    // Belirli bir başlığa sahip özetleri bul
    List<AnalyzedSummaryOutput> findByStoryTitle(String storyTitle);
    
    // Belirli tarih ve kategoriye göre özetleri bul - Sayfalama destekli
    Page<AnalyzedSummaryOutput> findByPublicationDateAndAssignedCategoriesContaining(
            LocalDate publicationDate, String category, Pageable pageable);
} 