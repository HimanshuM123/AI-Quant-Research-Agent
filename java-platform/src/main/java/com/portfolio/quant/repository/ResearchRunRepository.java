package com.portfolio.quant.repository;

import com.portfolio.quant.domain.ResearchRunEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.domain.Pageable;

import java.util.List;

public interface ResearchRunRepository extends JpaRepository<ResearchRunEntity, String> {

	List<ResearchRunEntity> findAllByOrderBySubmittedAtDesc(Pageable pageable);
}