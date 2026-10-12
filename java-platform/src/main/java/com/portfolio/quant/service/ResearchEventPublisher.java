package com.portfolio.quant.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.portfolio.quant.domain.ResearchRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class ResearchEventPublisher {

    private static final Logger logger = LoggerFactory.getLogger(ResearchEventPublisher.class);

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;
    private final String requestedTopic;
    private final String completedTopic;
    private final String failedTopic;

    public ResearchEventPublisher(
            KafkaTemplate<String, String> kafkaTemplate,
            ObjectMapper objectMapper,
            @Value("${quant.events.requested-topic}") String requestedTopic,
            @Value("${quant.events.completed-topic}") String completedTopic,
            @Value("${quant.events.failed-topic}") String failedTopic
    ) {
        this.kafkaTemplate = kafkaTemplate;
        this.objectMapper = objectMapper;
        this.requestedTopic = requestedTopic;
        this.completedTopic = completedTopic;
        this.failedTopic = failedTopic;
    }

    public void publishRequested(String researchId, ResearchRequest request) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("event_type", "research.requested");
        payload.put("event_version", 1);
        payload.put("research_id", researchId);
        payload.put("occurred_at", Instant.now());
        payload.put("request", request);
        publish(requestedTopic, researchId, payload);
    }

    public void publishCompleted(String researchId, Map<String, Object> result) {
        Map<String, Object> payload = envelope("research.completed", researchId);
        payload.put("result", result);
        publish(completedTopic, researchId, payload);
    }

    public void publishFailed(String researchId, String error) {
        Map<String, Object> payload = envelope("research.failed", researchId);
        payload.put("error", error);
        publish(failedTopic, researchId, payload);
    }

    private Map<String, Object> envelope(String eventType, String researchId) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("event_type", eventType);
        payload.put("event_version", 1);
        payload.put("research_id", researchId);
        payload.put("occurred_at", Instant.now());
        return payload;
    }

    private void publish(String topic, String key, Map<String, Object> payload) {
        try {
            kafkaTemplate.send(topic, key, objectMapper.writeValueAsString(payload))
                    .whenComplete((result, error) -> {
                        if (error != null) {
                            logger.warn("Kafka event publication failed for topic {} and research {}", topic, key, error);
                        }
                    });
        } catch (JsonProcessingException | RuntimeException exception) {
            logger.warn("Kafka event could not be serialized or submitted for topic {} and research {}", topic, key, exception);
        }
    }
}