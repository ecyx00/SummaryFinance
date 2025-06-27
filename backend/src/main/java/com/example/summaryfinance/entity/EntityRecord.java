package com.example.summaryfinance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "entities", uniqueConstraints = {
    @UniqueConstraint(name = "uk_entity_name_type", columnNames = {"name", "type"})
})
@Getter
@Setter
@NoArgsConstructor
public class EntityRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "name", nullable = false, length = 255)
    private String name;

    @Column(name = "type", nullable = false, length = 50)
    private String type;

    @Column(name = "canonical_id", length = 255)
    private String canonicalId;
    
    // İlişkiler
    @OneToMany(mappedBy = "entity", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<ArticleEntity> articleEntities = new ArrayList<>();
}
