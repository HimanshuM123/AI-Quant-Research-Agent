package com.portfolio.quant.service;

import com.portfolio.quant.domain.ResearchRequest;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executor;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class ResearchJobServiceTest {

    @Test
    void queuesAndCompletesResearchWithoutBlockingSubmission() {
        PythonResearchClient client = mock(PythonResearchClient.class);
        ResearchRunStore store = mock(ResearchRunStore.class);
        ResearchEventPublisher publisher = mock(ResearchEventPublisher.class);
        ResearchRedisLock lock = mock(ResearchRedisLock.class);
        when(lock.tryAcquire(any())).thenReturn(true);
        Executor immediateExecutor = Runnable::run;
        when(client.runResearch(any())).thenReturn(Map.of("status", "RISK_READY"));
        ResearchJobService service = new ResearchJobService(client, store, publisher, lock, new SimpleMeterRegistry(), immediateExecutor);

        String researchId = service.submit(request());

        assertThat(researchId).isNotBlank();
        verify(store).createQueued(eq(researchId), any(ResearchRequest.class));
        verify(store).markRunning(researchId);
        verify(store).markCompleted(eq(researchId), any(Map.class));
        verify(publisher).publishRequested(eq(researchId), any(ResearchRequest.class));
        verify(publisher).publishCompleted(eq(researchId), any(Map.class));
        verify(lock).release(researchId);
    }

    @Test
    void persistsFailureWhenPythonEngineThrows() {
        PythonResearchClient client = mock(PythonResearchClient.class);
        ResearchRunStore store = mock(ResearchRunStore.class);
        ResearchEventPublisher publisher = mock(ResearchEventPublisher.class);
        ResearchRedisLock lock = mock(ResearchRedisLock.class);
        when(lock.tryAcquire(any())).thenReturn(true);
        when(client.runResearch(any())).thenThrow(new IllegalStateException("engine unavailable"));
        ResearchJobService service = new ResearchJobService(client, store, publisher, lock, new SimpleMeterRegistry(), Runnable::run);

        String researchId = service.submit(request());

        verify(store).markFailed(researchId, "engine unavailable");
        verify(publisher).publishRequested(eq(researchId), any(ResearchRequest.class));
        verify(publisher).publishFailed(researchId, "engine unavailable");
        verify(lock).release(researchId);
    }

    private ResearchRequest request() {
        return new ResearchRequest(
                "Momentum breakout", List.of("AAPL"), LocalDate.of(2024, 1, 1),
                LocalDate.of(2024, 12, 31), null, null, null, null, null, null, null, null
        );
    }
}