package com.portfolio.quant.service;

import com.portfolio.quant.domain.ResearchRequest;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.Executor;

@Service
public class ResearchJobService {

    private final PythonResearchClient pythonResearchClient;
    private final ResearchRunStore researchRunStore;
    private final ResearchEventPublisher researchEventPublisher;
    private final ResearchRedisLock researchRedisLock;
    private final MeterRegistry meterRegistry;
    private final Executor executor;

    public ResearchJobService(
            PythonResearchClient pythonResearchClient,
            ResearchRunStore researchRunStore,
            ResearchEventPublisher researchEventPublisher,
            ResearchRedisLock researchRedisLock,
            MeterRegistry meterRegistry,
            @Qualifier("researchJobExecutor") Executor executor
    ) {
        this.pythonResearchClient = pythonResearchClient;
        this.researchRunStore = researchRunStore;
        this.researchEventPublisher = researchEventPublisher;
        this.researchRedisLock = researchRedisLock;
        this.meterRegistry = meterRegistry;
        this.executor = executor;
    }

    public String submit(ResearchRequest request) {
        String researchId = UUID.randomUUID().toString();
        researchRunStore.createQueued(researchId, request);
        researchEventPublisher.publishRequested(researchId, request);
        meterRegistry.counter("quant.research.jobs", "state", "queued").increment();
        executor.execute(() -> execute(researchId, request));
        return researchId;
    }

    private void execute(String researchId, ResearchRequest request) {
        if (!researchRedisLock.tryAcquire(researchId)) {
            return;
        }
        Timer.Sample timer = Timer.start(meterRegistry);
        try {
            researchRunStore.markRunning(researchId);
            Map<String, Object> result = new LinkedHashMap<>(pythonResearchClient.runResearch(request));
            result.put("research_id", researchId);
            researchRunStore.markCompleted(researchId, result);
            researchEventPublisher.publishCompleted(researchId, result);
            meterRegistry.counter("quant.research.jobs", "state", "completed").increment();
        } catch (Exception exception) {
            String error = exception.getMessage() == null ? exception.toString() : exception.getMessage();
            researchRunStore.markFailed(researchId, error);
            researchEventPublisher.publishFailed(researchId, error);
            meterRegistry.counter("quant.research.jobs", "state", "failed").increment();
        } finally {
            timer.stop(meterRegistry.timer("quant.research.engine.duration"));
            researchRedisLock.release(researchId);
        }
    }
}