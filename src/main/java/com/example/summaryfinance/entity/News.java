package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "news")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class News {

    @Id
    @Column(name = "id")
    private String id;

    @Column(name = "url", nullable = false)
    private String url;

    @Column(name = "publication_date", nullable = false)
    private LocalDateTime publicationDate;

    @Column(name = "section", nullable = false)
    private String section;

    @Column(name = "source", nullable = false)
    private String source;
}
