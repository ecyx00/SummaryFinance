package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import java.time.ZonedDateTime;

@Entity
@Table(name = "ai_processing_log", indexes = {
        @Index(name = "idx_ai_processing_log_status", columnList = "status")
})
@Getter
@Setter
@NoArgsConstructor
public class AiProcessingLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "news_id", nullable = false, unique = true)
    private News news;
    
    @Column(name = "status", nullable = false, length = 255)
    private String status = "PENDING";
    
    @Column(name = "last_attempt_at")
    private ZonedDateTime lastAttemptAt;
    
    @Column(name = "attempt_count", nullable = false)
    private Integer attemptCount = 0;
    
    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;
    
    @Column(name = "embedding_vector_id", length = 255)
    private String embeddingVectorId;
    
    @Column(name = "embedding_model_version", length = 255)
    private String embeddingModelVersion;
}
