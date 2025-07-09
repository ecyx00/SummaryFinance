package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import java.time.ZonedDateTime;

@Entity
@Table(name = "user_feedback", uniqueConstraints = {
        @UniqueConstraint(name = "uk_user_feedback_story_ip", columnNames = {"story_id", "ip_address"})
})
@Getter
@Setter
@NoArgsConstructor
public class UserFeedback {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "story_id", nullable = false)
    private AnalyzedStory story;
    
    @Column(name = "ip_address", nullable = false, length = 45)
    private String ipAddress;
    
    @Column(name = "user_agent", columnDefinition = "TEXT")
    private String userAgent;
    
    @Column(name = "rating")
    private Short rating;
    
    @Column(name = "is_helpful")
    private Boolean isHelpful;
    
    @Column(name = "comment", columnDefinition = "TEXT")
    private String comment;
    
    @Column(name = "feedback_timestamp", nullable = false)
    private ZonedDateTime feedbackTimestamp;
    
    @PrePersist
    public void validate() {
        if (rating == null && isHelpful == null) {
            throw new IllegalStateException("Either rating or isHelpful must be provided");
        }
        
        if (rating != null && (rating < 1 || rating > 5)) {
            throw new IllegalStateException("Rating must be between 1 and 5");
        }
    }
}
