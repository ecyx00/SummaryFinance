package com.example.summaryfinance.mapper;

import com.example.summaryfinance.dto.NewsDTO;
import com.example.summaryfinance.entity.News;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

import java.util.List;

@Mapper(componentModel = "spring") // Bu, Spring'in NewsMapperImpl'i bir bean olarak yönetmesini sağlar
public interface NewsMapper {

    // News -> NewsDTO (entity -> dto dönüşümü)
    @Mapping(target = "section", constant = "Genel")
    NewsDTO toDto(News news);

    // NewsDTO -> News (dto -> entity dönüşümü)
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "fetchedAt", ignore = true)
    // Entity'deki ilişkileri null/empty olarak ayarlar
    @Mapping(target = "articleEntities", ignore = true)
    @Mapping(target = "processingLog", ignore = true)
    @Mapping(target = "sourceEdges", ignore = true)
    @Mapping(target = "storyNewsLinks", ignore = true)
    @Mapping(target = "targetEdges", ignore = true)
    News toEntity(NewsDTO newsDTO);

    List<NewsDTO> toDtoList(List<News> newsList);

    List<News> toEntityList(List<NewsDTO> newsDTOList);
    
    // ZonedDateTime dönüşüm metodu eklemiyoruz çünkü artık her iki tarafta da ZonedDateTime kullanıyoruz
}