package com.portfolio.quant.api;

import com.portfolio.quant.domain.ResearchRequest;
import com.portfolio.quant.service.ResearchJobService;
import com.portfolio.quant.service.ResearchRunStore;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping({"/api/v1/research", "/api/research"})
public class ResearchController {

    private final ResearchJobService researchJobService;
    private final ResearchRunStore researchRunStore;

    public ResearchController(ResearchJobService researchJobService, ResearchRunStore researchRunStore) {
        this.researchJobService = researchJobService;
        this.researchRunStore = researchRunStore;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.ACCEPTED)
    public Map<String, Object> createResearch(@Valid @RequestBody ResearchRequest request) {
        String researchId = researchJobService.submit(request);
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("research_id", researchId);
        response.put("status", "QUEUED");
        response.put("gateway_status", "QUEUED");
        return response;
    }

    @GetMapping
    public List<Map<String, Object>> listResearch(@RequestParam(defaultValue = "20") int limit) {
        int boundedLimit = Math.max(1, Math.min(limit, 100));
        return researchRunStore.findRecent(boundedLimit).stream()
                .map(this::historyItem)
                .toList();
    }

    @GetMapping("/{researchId}")
    public Map<String, Object> getResearch(@PathVariable String researchId) {
        ResearchRunStore.ResearchRun run = storedRun(researchId);
        Map<String, Object> response = new LinkedHashMap<>(run.result());
        response.put("research_id", run.researchId());
        response.put("status", run.status());
        response.put("gateway_status", run.status());
        response.put("current_agent", run.currentAgent());
        response.put("errors", run.errors());
        response.put("submitted_at", run.submittedAt());
        response.put("updated_at", run.updatedAt());
        return response;
    }

    @GetMapping("/{researchId}/strategy")
    public Object getStrategy(@PathVariable String researchId) {
        return nestedResult(researchId, "strategy");
    }

    @GetMapping("/{researchId}/backtest")
    public Object getBacktest(@PathVariable String researchId) {
        return nestedResult(researchId, "backtest");
    }

    @GetMapping("/{researchId}/report")
    public Object getReport(@PathVariable String researchId) {
        return nestedResult(researchId, "report");
    }

    private Object nestedResult(String researchId, String key) {
        Object value = storedRun(researchId).result().get(key);
        if (value == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, key + " is not available for research run " + researchId);
        }
        return value;
    }

    private ResearchRunStore.ResearchRun storedRun(String researchId) {
        ResearchRunStore.ResearchRun run = researchRunStore.find(researchId);
        if (run == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Research run not found: " + researchId);
        }
        return run;
    }

    private Map<String, Object> historyItem(ResearchRunStore.ResearchRun run) {
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("research_id", run.researchId());
        item.put("status", run.status());
        item.put("gateway_status", run.status());
        item.put("current_agent", run.currentAgent());
        item.put("submitted_at", run.submittedAt());
        item.put("updated_at", run.updatedAt());
        item.put("query", run.request().query());
        item.put("symbols", run.request().symbols());
        Map<String, Object> strategy = asMap(run.result().get("strategy"));
        Map<String, Object> backtest = asMap(run.result().get("backtest"));
        item.put("strategy_name", strategy.get("name"));
        item.put("total_return", backtest.get("total_return"));
        item.put("benchmark_return", backtest.get("benchmark_return"));
        return item;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> asMap(Object value) {
        return value instanceof Map<?, ?> map ? (Map<String, Object>) map : Map.of();
    }

}
