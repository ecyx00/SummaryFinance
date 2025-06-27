package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.time.ZonedDateTime;

@Entity
@Table(name = "llm_interactions", indexes = {
        @Index(name = "idx_llm_interactions_task_type", columnList = "task_type")
})
@Getter
@Setter
@NoArgsConstructor
public class LlmInteraction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "request_timestamp", nullable = false)
    private ZonedDateTime requestTimestamp;
    
    @Column(name = "task_type", nullable = false, length = 255)
    private String taskType;
    
    @Column(name = "prompt_version", length = 50)
    private String promptVersion;
    
    @Column(name = "model_version", length = 255)
    private String modelVersion;
    
    @Column(name = "input_prompt", columnDefinition = "TEXT")
    private String inputPrompt;
    
    @Column(name = "raw_output", columnDefinition = "TEXT")
    private String rawOutput;
    
    @Column(name = "parsed_output", columnDefinition = "jsonb")
    @JdbcTypeCode(SqlTypes.JSON)
    private String parsedOutput;
    
    @Column(name = "token_usage", columnDefinition = "jsonb")
    @JdbcTypeCode(SqlTypes.JSON)
    private String tokenUsage;
    
    @Column(name = "latency_ms")
    private Integer latencyMs;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "story_id")
    private AnalyzedStory story;
}
