package com.portfolio.quant.domain;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

import java.time.LocalDate;
import java.util.List;

public record ResearchRequest(
        @NotBlank String query,
        @NotEmpty List<String> symbols,
        LocalDate startDate,
        LocalDate endDate,
        Double maxDrawdown
) {}
