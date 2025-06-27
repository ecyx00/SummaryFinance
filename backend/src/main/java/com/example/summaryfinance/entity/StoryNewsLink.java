package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "story_news_link")
@Getter
@Setter
@NoArgsConstructor
public class StoryNewsLink {

    @EmbeddedId
    private StoryNewsLinkId id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("storyId")
    @JoinColumn(name = "story_id")
    private AnalyzedStory story;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("newsId")
    @JoinColumn(name = "news_id")
    private News news;
    
    // Bileşik anahtar için iç sınıf
    @Embeddable
    @Getter
    @Setter
    @NoArgsConstructor
    public static class StoryNewsLinkId implements java.io.Serializable {
        
        private static final long serialVersionUID = 1L;
        
        @Column(name = "story_id")
        private Long storyId;
        
        @Column(name = "news_id")
        private Long newsId;
        
        public StoryNewsLinkId(Long storyId, Long newsId) {
            this.storyId = storyId;
            this.newsId = newsId;
        }
        
        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            
            StoryNewsLinkId that = (StoryNewsLinkId) o;
            
            if (!storyId.equals(that.storyId)) return false;
            return newsId.equals(that.newsId);
        }
        
        @Override
        public int hashCode() {
            int result = storyId.hashCode();
            result = 31 * result + newsId.hashCode();
            return result;
        }
    }
}
