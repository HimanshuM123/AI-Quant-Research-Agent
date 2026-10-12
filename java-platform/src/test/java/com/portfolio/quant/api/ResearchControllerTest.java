package com.portfolio.quant.api;

import com.portfolio.quant.domain.ResearchRequest;
import com.portfolio.quant.domain.ResearchRunEntity;
import com.portfolio.quant.repository.ResearchRunRepository;
import com.portfolio.quant.service.ResearchJobService;
import com.portfolio.quant.service.ResearchRunStore;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import org.springframework.web.server.ResponseStatusException;

class ResearchControllerTest {

    @Test
    void deserializesSnakeCaseResearchDates() throws Exception {
        ObjectMapper objectMapper = new ObjectMapper().registerModule(new JavaTimeModule());
        ResearchRequest request = objectMapper.readValue("""
                {"query":"Momentum breakout","symbols":["AAPL"],"start_date":"2024-01-01","end_date":"2024-12-31"}
                """, ResearchRequest.class);

        assertThat(request.startDate()).isEqualTo(LocalDate.of(2024, 1, 1));
        assertThat(request.endDate()).isEqualTo(LocalDate.of(2024, 12, 31));
    }

    @Test
    void storesCompletedRunAndExposesResourceViews() {
        Map<String, Object> engineResult = Map.of(
                "research_id", "run-123",
                "status", "RISK_READY",
                "strategy", Map.of("name", "Momentum"),
                "backtest", Map.of("total_return", 0.2),
                "report", Map.of("decision", "ACCEPT")
        );
        ResearchRequest request = new ResearchRequest(
                "Momentum breakout", List.of("AAPL"), LocalDate.of(2024, 1, 1),
                LocalDate.of(2024, 12, 31), null, null, null, null, null, null, null, null
        );
            ResearchRunRepository repository = mock(ResearchRunRepository.class);
            ResearchRunEntity storedRun = new ResearchRunEntity("run-123", request, engineResult, java.time.Instant.now());
        when(repository.save(any(ResearchRunEntity.class))).thenReturn(storedRun);
        storedRun.markCompleted(engineResult);
        when(repository.findById("run-123")).thenReturn(Optional.of(storedRun));
        ResearchRunStore store = new ResearchRunStore(repository);
        ResearchJobService jobService = mock(ResearchJobService.class);
        when(jobService.submit(request)).thenReturn("run-123");
        ResearchController controller = new ResearchController(jobService, store);

        Map<String, Object> created = controller.createResearch(request);

        assertThat(created).containsEntry("gateway_status", "QUEUED");
        assertThat(controller.getResearch("run-123")).containsEntry("status", "RISK_READY");
        assertThat(controller.getStrategy("run-123")).isEqualTo(Map.of("name", "Momentum"));
        assertThat(controller.getBacktest("run-123")).isEqualTo(Map.of("total_return", 0.2));
        assertThat(controller.getReport("run-123")).isEqualTo(Map.of("decision", "ACCEPT"));

        ResearchResourceController resources = new ResearchResourceController(store);
        assertThat(resources.getStrategy("run-123")).isEqualTo(Map.of("name", "Momentum"));
    }

    @Test
    void returnsNotFoundForUnknownRun() {
        ResearchRunRepository repository = mock(ResearchRunRepository.class);
        when(repository.findById("missing")).thenReturn(Optional.empty());
        ResearchController controller = new ResearchController(null, new ResearchRunStore(repository));

        assertThatThrownBy(() -> controller.getResearch("missing"))
                .isInstanceOf(ResponseStatusException.class)
                .extracting("statusCode.value")
                .isEqualTo(404);
    }
}