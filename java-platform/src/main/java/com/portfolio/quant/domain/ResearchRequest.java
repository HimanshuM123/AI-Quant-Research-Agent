package com.portfolio.quant.domain;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

import java.time.LocalDate;
import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record ResearchRequest(
        @NotBlank String query,
        @NotEmpty List<String> symbols,
    @NotNull LocalDate startDate,
    @NotNull LocalDate endDate,
        Double maxDrawdown,
        Integer volatilityWindow,
        Integer momentumWindow,
        Integer topK,
        Double slippageBps,
        Double initialCapital,
        Double annualRiskFreeRate,
        Double varConfidence
) {
    public ResearchRequest {
        if (volatilityWindow == null) volatilityWindow = 20;
        if (momentumWindow == null) momentumWindow = 20;
        if (topK == null) topK = 5;
        if (slippageBps == null) slippageBps = 2.0;
        if (initialCapital == null) initialCapital = 100000.0;
        if (annualRiskFreeRate == null) annualRiskFreeRate = 0.0;
        if (varConfidence == null) varConfidence = 0.95;
    }
}
