package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "news", indexes = {
        @Index(name = "idx_news_publication_date", columnList = "publication_date"),
        @Index(name = "idx_news_source", columnList = "source")
})
@Getter
@Setter
@NoArgsConstructor
public class News {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "url", nullable = false, length = 2048)
    private String url;
    
    @Column(name = "title", length = 1024)
    private String title;
    
    @Column(name = "source", length = 255)
    private String source;
    
    @Column(name = "publication_date")
    private ZonedDateTime publicationDate;
    
    @Column(name = "fetched_at", nullable = false)
    private ZonedDateTime fetchedAt;
    
    // İlişkiler
    @OneToMany(mappedBy = "news", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<ArticleEntity> articleEntities = new ArrayList<>();
    
    @OneToMany(mappedBy = "news", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<StoryNewsLink> storyNewsLinks = new ArrayList<>();
    
    @OneToOne(mappedBy = "news", cascade = CascadeType.ALL, orphanRemoval = true)
    private AiProcessingLog processingLog;
    
    @OneToMany(mappedBy = "sourceNews", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<GraphEdge> sourceEdges = new ArrayList<>();
    
    @OneToMany(mappedBy = "targetNews", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<GraphEdge> targetEdges = new ArrayList<>();
}

