package com.portfolio.quant.api;

import com.portfolio.quant.service.ResearchRunStore;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;

@RestController
public class ResearchResourceController {

    private final ResearchRunStore researchRunStore;

    public ResearchResourceController(ResearchRunStore researchRunStore) {
        this.researchRunStore = researchRunStore;
    }

    @GetMapping({"/api/v1/strategies/{researchId}", "/api/strategies/{researchId}"})
    public Object getStrategy(@PathVariable String researchId) {
        return nestedResult(researchId, "strategy");
    }

    @GetMapping({"/api/v1/backtests/{researchId}", "/api/backtests/{researchId}"})
    public Object getBacktest(@PathVariable String researchId) {
        return nestedResult(researchId, "backtest");
    }

    @GetMapping({"/api/v1/reports/{researchId}", "/api/reports/{researchId}"})
    public Object getReport(@PathVariable String researchId) {
        return nestedResult(researchId, "report");
    }

    private Object nestedResult(String researchId, String key) {
        ResearchRunStore.ResearchRun run = researchRunStore.find(researchId);
        if (run == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Research run not found: " + researchId);
        }
        Map<String, Object> result = run.result();
        Object value = result.get(key);
        if (value == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, key + " is not available for research run " + researchId);
        }
        return value;
    }
}