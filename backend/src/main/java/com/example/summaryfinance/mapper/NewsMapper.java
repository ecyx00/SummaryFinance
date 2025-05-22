package com.example.summaryfinance.mapper;

import com.example.summaryfinance.dto.NewsDTO;
import com.example.summaryfinance.entity.News;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
// Mappers import'una artık gerek yok
// import org.mapstruct.factory.Mappers; 

import java.util.List;

@Mapper(componentModel = "spring") // Bu, Spring'in NewsMapperImpl'i bir bean olarak yönetmesini sağlar
public interface NewsMapper {

    // NewsMapper INSTANCE = Mappers.getMapper(NewsMapper.class); // BU SATIRI SİL

    // News -> NewsDTO (id ve fetchedAt otomatik olarak ignore edilir)
    NewsDTO toDto(News news);

    // NewsDTO -> News (id ve fetchedAt null/default olur)
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "fetchedAt", ignore = true)
    News toEntity(NewsDTO newsDTO);

    List<NewsDTO> toDtoList(List<News> newsList);

    List<News> toEntityList(List<NewsDTO> newsDTOList);
}