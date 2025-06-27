package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import java.time.LocalDate;

@Entity
@Table(name = "graph_edges", indexes = {
        @Index(name = "idx_graph_edges_run_date", columnList = "run_date")
})
@Getter
@Setter
@NoArgsConstructor
public class GraphEdge {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "run_date", nullable = false)
    private LocalDate runDate;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "source_news_id", nullable = false)
    private News sourceNews;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "target_news_id", nullable = false)
    private News targetNews;
    
    @Column(name = "semantic_score")
    private Float semanticScore;
    
    @Column(name = "entity_score")
    private Float entityScore;
    
    @Column(name = "temporal_score")
    private Float temporalScore;
    
    @Column(name = "total_interaction_score")
    private Float totalInteractionScore;
}
