package com.example.summaryfinance.mapper;

import com.example.summaryfinance.dto.NewsDTO;
import com.example.summaryfinance.entity.News;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

@Mapper(componentModel = "spring")
public interface NewsMapper {

    NewsMapper INSTANCE = Mappers.getMapper(NewsMapper.class);

    NewsDTO toDto(News news);

    News toEntity(NewsDTO newsDTO);

    List<NewsDTO> toDtoList(List<News> newsList);

    List<News> toEntityList(List<NewsDTO> newsDTOList);
}