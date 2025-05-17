package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import java.time.LocalDateTime;

@Entity
@Table(name = "news", indexes = {
        @Index(name = "idx_news_url", columnList = "url", unique = true),
        @Index(name = "idx_news_publication_date", columnList = "publicationDate"),
        @Index(name = "idx_news_section", columnList = "section"),
        @Index(name = "idx_news_source", columnList = "source")
})
@Getter
@Setter // Veya @Data
@NoArgsConstructor
public class News {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY) // Otomatik artan Long ID
    private Long id;

    @Column(nullable = false, length = 512) // Başlık alanı
    private String title;

    @Column(nullable = false, unique = true, length = 1024) // URL alanı
    private String url;

    @Column(nullable = false)
    private LocalDateTime publicationDate;

    @Column(nullable = false) // API'den gelen ham bölüm/kategori adı
    private String section;

    @Column(nullable = false)
    private String source;

    @Column(nullable = false) // Ne zaman çektiğimizin kaydı
    private LocalDateTime fetchedAt;
}

