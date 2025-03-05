package com.summaryfinance.backend.dto;

import lombok.Data;
import java.util.List;

@Data
public class ClusterAnalysisDTO {
    private String clusterId;
    private List<Long> newsIds;
    private String summary;
    private String economicAnalysis;
    private Double averageImpactScore;
} 