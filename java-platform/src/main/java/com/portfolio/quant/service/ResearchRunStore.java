package com.portfolio.quant.service;

import com.portfolio.quant.domain.ResearchRequest;
import com.portfolio.quant.domain.ResearchRunEntity;
import com.portfolio.quant.repository.ResearchRunRepository;
import org.springframework.stereotype.Service;
import org.springframework.data.domain.PageRequest;

import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;
import java.util.Map;

@Service
public class ResearchRunStore {

    private final ResearchRunRepository repository;

    public ResearchRunStore(ResearchRunRepository repository) {
        this.repository = repository;
    }

    public void save(String researchId, ResearchRequest request, Map<String, Object> result) {
        ResearchRunEntity entity = repository.findById(researchId)
                .orElseThrow(() -> new IllegalArgumentException("Research run not found: " + researchId));
        entity.markCompleted(result);
        repository.save(entity);
    }

    public void createQueued(String researchId, ResearchRequest request) {
        repository.save(new ResearchRunEntity(researchId, request, null, Instant.now()));
    }

    public void markRunning(String researchId) {
        ResearchRunEntity entity = entity(researchId);
        entity.markRunning();
        repository.save(entity);
    }

    public void markCompleted(String researchId, Map<String, Object> result) {
        ResearchRunEntity entity = entity(researchId);
        entity.markCompleted(result);
        repository.save(entity);
    }

    public void markFailed(String researchId, String error) {
        ResearchRunEntity entity = entity(researchId);
        entity.markFailed(error);
        repository.save(entity);
    }

    public ResearchRun find(String researchId) {
        return repository.findById(researchId)
                .map(entity -> new ResearchRun(
                        entity.getResearchId(),
                        entity.toRequest(),
                        entity.getResult(),
                        entity.getStatus(),
                        entity.getCurrentAgent(),
                        entity.getErrors(),
                        entity.getSubmittedAt(),
                        entity.getUpdatedAt()
                ))
                .orElse(null);
    }

            public List<ResearchRun> findRecent(int limit) {
            return repository.findAllByOrderBySubmittedAtDesc(PageRequest.of(0, limit)).stream()
                .map(entity -> new ResearchRun(
                    entity.getResearchId(),
                    entity.toRequest(),
                    entity.getResult(),
                    entity.getStatus(),
                    entity.getCurrentAgent(),
                    entity.getErrors(),
                    entity.getSubmittedAt(),
                    entity.getUpdatedAt()
                ))
                .collect(Collectors.toList());
            }

                private ResearchRunEntity entity(String researchId) {
                return repository.findById(researchId)
                    .orElseThrow(() -> new IllegalArgumentException("Research run not found: " + researchId));
                }

    public record ResearchRun(
            String researchId,
            ResearchRequest request,
            Map<String, Object> result,
            String status,
            String currentAgent,
            List<String> errors,
            Instant submittedAt,
            Instant updatedAt
    ) {
    }
}