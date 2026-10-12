package com.portfolio.quant.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;

@Service
public class ResearchRedisLock {

    private static final Logger logger = LoggerFactory.getLogger(ResearchRedisLock.class);

    private final StringRedisTemplate redisTemplate;
    private final Duration lockTtl;

    public ResearchRedisLock(
            StringRedisTemplate redisTemplate,
            @Value("${quant.jobs.lock-ttl-seconds:1800}") long lockTtlSeconds
    ) {
        this.redisTemplate = redisTemplate;
        this.lockTtl = Duration.ofSeconds(lockTtlSeconds);
    }

    public boolean tryAcquire(String researchId) {
        try {
            Boolean acquired = redisTemplate.opsForValue().setIfAbsent(lockKey(researchId), "worker", lockTtl);
            return Boolean.TRUE.equals(acquired);
        } catch (RuntimeException exception) {
            logger.warn("Redis unavailable; continuing research job {} without distributed lock", researchId);
            return true;
        }
    }

    public void release(String researchId) {
        try {
            redisTemplate.delete(lockKey(researchId));
        } catch (RuntimeException exception) {
            logger.warn("Unable to release Redis lock for research job {}", researchId);
        }
    }

    private String lockKey(String researchId) {
        return "quant:research:lock:" + researchId;
    }
}