package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import java.time.ZonedDateTime;

@Entity
@Table(name = "story_relationships")
@Getter
@Setter
@NoArgsConstructor
public class StoryRelationship {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "source_story_id", nullable = false)
    private AnalyzedStory sourceStory;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "target_story_id", nullable = false)
    private AnalyzedStory targetStory;
    
    @Column(name = "relationship_type", nullable = false, length = 100)
    private String relationshipType;
    
    @Column(name = "is_active", nullable = false)
    private Boolean isActive = true;
    
    @Column(name = "created_at", nullable = false)
    private ZonedDateTime createdAt;
    
    @Column(name = "created_by", nullable = false, length = 100)
    private String createdBy = "SYSTEM";
}
