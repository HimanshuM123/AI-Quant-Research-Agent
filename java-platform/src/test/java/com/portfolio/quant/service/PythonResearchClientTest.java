package com.portfolio.quant.service;

import com.portfolio.quant.domain.ResearchRequest;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.jsonPath;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class PythonResearchClientTest {

    @Test
    void runResearchSendsExpectedPythonPayload() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();

        server.expect(requestTo("http://localhost:8000/api/v1/research/run"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.query").value("Momentum breakout"))
                .andExpect(jsonPath("$.symbols[0]").value("AAPL"))
                .andExpect(jsonPath("$.start_date").value("2024-01-01"))
                .andExpect(jsonPath("$.volatility_window").value(20))
                .andRespond(withSuccess("{\"status\":\"RISK_READY\",\"current_agent\":\"risk\",\"research_id\":\"abc\"}", MediaType.APPLICATION_JSON));

        PythonResearchClient client = new PythonResearchClient(restTemplate);
        ResearchRequest request = new ResearchRequest(
                "Momentum breakout",
                List.of("AAPL", "MSFT"),
                LocalDate.of(2024, 1, 1),
                LocalDate.of(2024, 12, 31),
                0.2,
                20,
                20,
                5,
                2.0,
                100000.0,
                0.04,
                0.95
        );

        Map<String, Object> response = client.runResearch(request);

        assertThat(response).containsEntry("status", "RISK_READY");
        assertThat(response).containsEntry("current_agent", "risk");
        server.verify();
    }
}
