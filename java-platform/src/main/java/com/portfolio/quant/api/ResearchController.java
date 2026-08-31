package com.portfolio.quant.api;

import com.portfolio.quant.domain.ResearchRequest;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/research")
public class ResearchController {

    @PostMapping
    @ResponseStatus(HttpStatus.ACCEPTED)
    public Map<String, Object> createResearch(@Valid @RequestBody ResearchRequest request) {
        // Phase 1 shell. In the Kafka milestone this will persist a job and publish
        // quant.research.requested.
        return Map.of(
                "researchId", UUID.randomUUID().toString(),
                "status", "ACCEPTED",
                "query", request.query(),
                "createdAt", Instant.now().toString()
        );
    }
}
