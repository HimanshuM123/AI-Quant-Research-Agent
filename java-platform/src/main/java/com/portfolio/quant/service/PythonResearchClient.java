package com.portfolio.quant.service;

import com.portfolio.quant.domain.ResearchRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class PythonResearchClient {

    private final RestTemplate restTemplate;
    private final String baseUrl;

    @Autowired
    public PythonResearchClient(
            RestTemplate restTemplate,
            @Value("${python.ai.base-url:http://localhost:8000}") String baseUrl
    ) {
        this.restTemplate = restTemplate;
        this.baseUrl = baseUrl;
    }

    public PythonResearchClient(RestTemplate restTemplate) {
        this(restTemplate, "http://localhost:8000");
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> runResearch(ResearchRequest request) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("query", request.query());
        body.put("symbols", request.symbols());
        body.put("start_date", request.startDate().toString());
        body.put("end_date", request.endDate().toString());
        body.put("volatility_window", request.volatilityWindow() != null ? request.volatilityWindow() : 20);
        body.put("momentum_window", request.momentumWindow() != null ? request.momentumWindow() : 20);
        body.put("top_k", request.topK() != null ? request.topK() : 5);
        body.put("slippage_bps", request.slippageBps() != null ? request.slippageBps() : 2.0);
        body.put("initial_capital", request.initialCapital() != null ? request.initialCapital() : 100000.0);
        body.put("annual_risk_free_rate", request.annualRiskFreeRate() != null ? request.annualRiskFreeRate() : 0.0);
        body.put("var_confidence", request.varConfidence() != null ? request.varConfidence() : 0.95);

        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
        return restTemplate.postForObject(baseUrl + "/api/v1/research/run", entity, Map.class);
    }
}
