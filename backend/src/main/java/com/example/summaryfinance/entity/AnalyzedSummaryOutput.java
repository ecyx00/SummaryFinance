package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "analyzed_summary_outputs", indexes = {
        @Index(name = "idx_summary_publication_date", columnList = "publicationDate")
})
@Getter
@Setter
@NoArgsConstructor
public class AnalyzedSummaryOutput {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(length = 1024)
    private String storyTitle;

    @Lob
    @Column(columnDefinition = "TEXT", nullable = false)
    private String summaryText;

    @Column(nullable = false)
    private LocalDate publicationDate;

    @CreationTimestamp
    @Column(nullable = false, updatable = false)
    private LocalDateTime generatedAt;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(
            name = "summary_assigned_categories",
            joinColumns = @JoinColumn(name = "summary_output_id")
    )
    @Column(name = "category", nullable = false)
    private List<String> assignedCategories = new ArrayList<>();
} 