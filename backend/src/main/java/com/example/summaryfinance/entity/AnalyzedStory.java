package com.example.summaryfinance.entity;

import com.pgvector.PGvector;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import java.time.LocalDate;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "analyzed_stories", indexes = {
        @Index(name = "idx_analyzed_stories_story_date", columnList = "story_date")
})
@Getter
@Setter
@NoArgsConstructor
public class AnalyzedStory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "story_title", nullable = false, length = 1024)
    private String storyTitle;
    
    @Column(name = "analysis_summary", nullable = false, columnDefinition = "TEXT")
    private String analysisSummary;
    
    @Column(name = "story_date")
    private LocalDate storyDate;
    
    @Column(name = "generated_at", nullable = false)
    private ZonedDateTime generatedAt;
    
    @Column(name = "group_label", length = 1024)
    private String groupLabel;
    
    @Column(name = "connection_rationale", columnDefinition = "TEXT")
    private String connectionRationale;
    
    @Column(name = "story_essence_text", columnDefinition = "TEXT")
    private String storyEssenceText;
    
    @Column(name = "story_context_snippets", columnDefinition = "TEXT[]")
    private String[] storyContextSnippets;
    
    @Column(name = "story_embedding_vector", columnDefinition = "vector(384)")
    private PGvector storyEmbeddingVector;
    
    @Column(name = "is_active", nullable = false)
    private Boolean isActive = true;
    
    @Column(name = "last_update_date")
    private ZonedDateTime lastUpdateDate;
    
    // İlişkiler
    @OneToMany(mappedBy = "story", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<StoryNewsLink> storyNewsLinks = new ArrayList<>();
    
    @OneToMany(mappedBy = "sourceStory", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<StoryRelationship> outgoingRelationships = new ArrayList<>();
    
    @OneToMany(mappedBy = "targetStory", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<StoryRelationship> incomingRelationships = new ArrayList<>();
    
    @OneToMany(mappedBy = "story", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<UserFeedback> userFeedbacks = new ArrayList<>();
    
    @OneToMany(mappedBy = "story", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<LlmInteraction> llmInteractions = new ArrayList<>();
}
