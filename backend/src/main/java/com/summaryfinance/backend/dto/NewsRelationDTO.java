package com.summaryfinance.backend.dto;

import lombok.Data;

@Data
public class NewsRelationDTO {
    private String clusterId;
    private String newsExternalId;
    private Float relationStrength;
    private Float economicImpactScore;
    private String relationDescription;
} 