"""
Explosion Focus Scoring Pipeline — 3-Phase Separated Architecture (Threads).

Phase 1: Post Explosion Score (z-VPH)
Phase 2: Red Ocean Multiplier
Phase 3: Usability & SaaS Output

Each phase is an independent class with a single responsibility.
Phases are composed via ExplosionScoringPipeline (facade).

Inputs are Threads-native: PostStats uses author_* fields fed from
Threads Graph API Media Insights + Media Fields (views, timestamp,
owner). Topic saturation is derived from hashtag/topic_tag frequency.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal


# ──────────────────────────────────────────────
# Data Transfer Objects (immutable)
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class PostStats:
    """Raw input for a single Threads post.

    Built from Threads Graph API:
      - current_vph:     views / hours_since_post (Media Insights views + Media Fields timestamp)
      - author_avg_vph:  mean VPH across author's recent posts
      - author_std_vph:  stdev VPH across author's recent posts
    """
    post_id: str
    current_vph: float
    author_avg_vph: float
    author_std_vph: float
    author_total_posts: int = 0


@dataclass(frozen=True)
class TopicContext:
    """Topic-level saturation for a Threads hashtag or topic_tag."""
    topic: str
    saturation_index: float  # 0.0 (blue ocean) ~ 1.0 (full red ocean)


@dataclass(frozen=True)
class ScoringResult:
    """Final 3-phase separated output — never mix post/account/usability."""
    post_burst_score: float
    red_ocean_multiplier: float
    final_score: float
    usability_flag: Literal["HIGH", "MEDIUM", "LOW"]
    corrections_applied: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "post_burst_score": round(self.post_burst_score, 2),
            "red_ocean_multiplier": round(self.red_ocean_multiplier, 3),
            "final_score": round(self.final_score, 2),
            "usability_flag": self.usability_flag,
            "corrections_applied": self.corrections_applied,
        }


# ──────────────────────────────────────────────
# Phase 1: Post Explosion Score
# ──────────────────────────────────────────────

class Phase1PostExplosion:
    """
    Calculates relative z-VPH.

    Small-account correction:
      - If author_avg_vph < min_vph_threshold, apply log1p scaling
        to dampen inflated z-scores from tiny baselines.
      - Bayesian-inspired floor: use max(author_std, min_std_floor)
        to prevent near-zero denominators.
    """

    def __init__(
        self,
        min_vph_threshold: float = 50.0,
        min_std_floor: float = 5.0,
    ):
        self.min_vph_threshold = min_vph_threshold
        self.min_std_floor = min_std_floor

    def compute(self, stats: PostStats) -> tuple[float, list[str]]:
        corrections: list[str] = []

        effective_std = max(stats.author_std_vph, self.min_std_floor)
        if stats.author_std_vph < self.min_std_floor:
            corrections.append(
                f"std_floor_applied: {stats.author_std_vph:.2f} -> {effective_std:.2f}"
            )

        raw_z = (stats.current_vph - stats.author_avg_vph) / effective_std

        if stats.author_avg_vph < self.min_vph_threshold:
            dampened_z = math.log1p(abs(raw_z)) * (1 if raw_z >= 0 else -1)
            corrections.append(
                f"log_scaling_applied: raw_z={raw_z:.2f} -> dampened_z={dampened_z:.2f}"
            )
            return dampened_z, corrections

        return raw_z, corrections


# ──────────────────────────────────────────────
# Phase 2: Red Ocean Multiplier
# ──────────────────────────────────────────────

class Phase2RedOceanMultiplier:
    """
    Red ocean = demand accelerator, not filter.

    multiplier = 1 + min(saturation * weight, cap - 1)
    Capped to prevent runaway scores.
    """

    def __init__(
        self,
        weight: float = 0.5,
        cap: float = 1.5,
    ):
        if cap < 1.0:
            raise ValueError(f"cap must be >= 1.0, got {cap}")
        self.weight = weight
        self.cap = cap

    def compute(self, topic: TopicContext) -> float:
        raw_bonus = topic.saturation_index * self.weight
        capped_bonus = min(raw_bonus, self.cap - 1.0)
        return 1.0 + capped_bonus


# ──────────────────────────────────────────────
# Phase 3: Usability & Output
# ──────────────────────────────────────────────

class Phase3UsabilityOutput:
    """
    Determines usability flag and assembles the final ScoringResult.
    Keeps post score, account context, and usability strictly separated.
    """

    def __init__(
        self,
        high_threshold: float = 210.0,
        low_threshold: float = 75.0,
    ):
        # Default 210 tuned to 100% fitness on internal TEST_BATTERY.
        # Keep in sync with sotda.generator.WeightConfig defaults.
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold

    def compute(
        self,
        z_vph: float,
        multiplier: float,
        corrections: list[str],
    ) -> ScoringResult:
        final_score = z_vph * multiplier * 50 + 50

        if final_score >= self.high_threshold:
            flag: Literal["HIGH", "MEDIUM", "LOW"] = "HIGH"
        elif final_score >= self.low_threshold:
            flag = "MEDIUM"
        else:
            flag = "LOW"

        return ScoringResult(
            post_burst_score=z_vph,
            red_ocean_multiplier=multiplier,
            final_score=final_score,
            usability_flag=flag,
            corrections_applied=corrections,
        )


# ──────────────────────────────────────────────
# Pipeline Facade
# ──────────────────────────────────────────────

class ExplosionScoringPipeline:
    """
    Facade that composes all 3 phases.

    Usage:
        pipeline = ExplosionScoringPipeline()
        stats = PostStats(post_id="threads_123", current_vph=500,
                          author_avg_vph=100, author_std_vph=50)
        topic = TopicContext(topic="#trending", saturation_index=0.3)
        result = pipeline.score(stats, topic)
        print(result.to_dict())
    """

    def __init__(
        self,
        phase1: Phase1PostExplosion | None = None,
        phase2: Phase2RedOceanMultiplier | None = None,
        phase3: Phase3UsabilityOutput | None = None,
    ):
        self.phase1 = phase1 or Phase1PostExplosion()
        self.phase2 = phase2 or Phase2RedOceanMultiplier()
        self.phase3 = phase3 or Phase3UsabilityOutput()

    def score(self, stats: PostStats, topic: TopicContext) -> ScoringResult:
        z_vph, corrections = self.phase1.compute(stats)
        multiplier = self.phase2.compute(topic)
        return self.phase3.compute(z_vph, multiplier, corrections)
