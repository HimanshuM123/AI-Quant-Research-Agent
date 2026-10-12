package com.portfolio.quant.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@Entity
@Table(name = "research_runs")
public class ResearchRunEntity {

    @Id
    @Column(name = "research_id", nullable = false, updatable = false, length = 64)
    private String researchId;

    @Column(nullable = false, length = 1000)
    private String query;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(nullable = false, columnDefinition = "jsonb")
    private List<String> symbols;

    @Column(name = "start_date", nullable = false)
    private LocalDate startDate;

    @Column(name = "end_date", nullable = false)
    private LocalDate endDate;

    @Column(name = "max_drawdown")
    private Double maxDrawdown;

    @Column(name = "volatility_window", nullable = false)
    private Integer volatilityWindow;

    @Column(name = "momentum_window", nullable = false)
    private Integer momentumWindow;

    @Column(name = "top_k", nullable = false)
    private Integer topK;

    @Column(name = "slippage_bps", nullable = false)
    private Double slippageBps;

    @Column(name = "initial_capital", nullable = false)
    private Double initialCapital;

    @Column(name = "annual_risk_free_rate", nullable = false)
    private Double annualRiskFreeRate;

    @Column(name = "var_confidence", nullable = false)
    private Double varConfidence;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> result;

    @Column(nullable = false, length = 32)
    private String status;

    @Column(name = "current_agent", length = 64)
    private String currentAgent;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(nullable = false, columnDefinition = "jsonb")
    private List<String> errors;

    @Column(name = "submitted_at", nullable = false, updatable = false)
    private Instant submittedAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected ResearchRunEntity() {
    }

    public ResearchRunEntity(String researchId, ResearchRequest request, Map<String, Object> result, Instant submittedAt) {
        this.researchId = researchId;
        this.query = request.query();
        this.symbols = request.symbols();
        this.startDate = request.startDate();
        this.endDate = request.endDate();
        this.maxDrawdown = request.maxDrawdown();
        this.volatilityWindow = request.volatilityWindow();
        this.momentumWindow = request.momentumWindow();
        this.topK = request.topK();
        this.slippageBps = request.slippageBps();
        this.initialCapital = request.initialCapital();
        this.annualRiskFreeRate = request.annualRiskFreeRate();
        this.varConfidence = request.varConfidence();
        this.result = result;
        this.status = "QUEUED";
        this.errors = new ArrayList<>();
        this.submittedAt = submittedAt;
        this.updatedAt = submittedAt;
    }

    public void markRunning() {
        status = "RUNNING";
        updatedAt = Instant.now();
    }

    public void markCompleted(Map<String, Object> result) {
        this.result = result;
        this.status = String.valueOf(result.getOrDefault("status", "COMPLETED"));
        this.currentAgent = result.get("current_agent") instanceof String agent ? agent : null;
        this.errors = new ArrayList<>();
        this.updatedAt = Instant.now();
    }

    public void markFailed(String error) {
        this.status = "FAILED";
        this.errors = new ArrayList<>(List.of(error));
        this.updatedAt = Instant.now();
    }

    public String getResearchId() {
        return researchId;
    }

    public ResearchRequest toRequest() {
        return new ResearchRequest(query, symbols, startDate, endDate, maxDrawdown, volatilityWindow,
                momentumWindow, topK, slippageBps, initialCapital, annualRiskFreeRate, varConfidence);
    }

    public Map<String, Object> getResult() {
        return result == null ? Collections.emptyMap() : result;
    }

    public Instant getSubmittedAt() {
        return submittedAt;
    }

    public String getStatus() {
        return status;
    }

    public String getCurrentAgent() {
        return currentAgent;
    }

    public List<String> getErrors() {
        return errors;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}