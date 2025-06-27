package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "article_entities")
@Getter
@Setter
@NoArgsConstructor
public class ArticleEntity {

    @EmbeddedId
    private ArticleEntityId id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("newsId")
    @JoinColumn(name = "news_id")
    private News news;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("entityId")
    @JoinColumn(name = "entity_id")
    private EntityRecord entity;
    
    // Bileşik anahtar için iç sınıf
    @Embeddable
    @Getter
    @Setter
    @NoArgsConstructor
    public static class ArticleEntityId implements java.io.Serializable {
        
        private static final long serialVersionUID = 1L;
        
        @Column(name = "news_id")
        private Long newsId;
        
        @Column(name = "entity_id")
        private Long entityId;
        
        public ArticleEntityId(Long newsId, Long entityId) {
            this.newsId = newsId;
            this.entityId = entityId;
        }
        
        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            
            ArticleEntityId that = (ArticleEntityId) o;
            
            if (!newsId.equals(that.newsId)) return false;
            return entityId.equals(that.entityId);
        }
        
        @Override
        public int hashCode() {
            int result = newsId.hashCode();
            result = 31 * result + entityId.hashCode();
            return result;
        }
    }
}
