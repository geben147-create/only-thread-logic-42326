"""
Weight Evaluator — scores a WeightConfig against Threads test scenarios.

Runs the scoring pipeline with given weights on a battery of
known-outcome Threads post scenarios and returns a fitness score (0-100).
"""

from __future__ import annotations

from dataclasses import dataclass

from sotda.generator import WeightConfig
from sotda.pipeline import (
    ExplosionScoringPipeline,
    Phase1PostExplosion,
    Phase2RedOceanMultiplier,
    Phase3UsabilityOutput,
    PostStats,
    TopicContext,
)


@dataclass(frozen=True)
class TestCase:
    """A Threads post scenario with expected outcome."""
    stats: PostStats
    topic: TopicContext
    expected_flag: str  # "HIGH", "MEDIUM", "LOW"
    description: str


# Known-outcome Threads test battery
TEST_BATTERY: list[TestCase] = [
    TestCase(
        stats=PostStats("threads_01", current_vph=500, author_avg_vph=100, author_std_vph=50),
        topic=TopicContext("#tech_review", 0.3),
        expected_flag="HIGH",
        description="Normal account genuine Threads explosion",
    ),
    TestCase(
        stats=PostStats("threads_02", current_vph=110, author_avg_vph=100, author_std_vph=50),
        topic=TopicContext("#cooking", 0.2),
        expected_flag="LOW",
        description="Normal account average Threads post",
    ),
    TestCase(
        stats=PostStats("threads_03", current_vph=80, author_avg_vph=5, author_std_vph=2),
        topic=TopicContext("#gaming", 0.1),
        expected_flag="MEDIUM",
        description="Small Threads account moderate spike (should not be HIGH)",
    ),
    TestCase(
        stats=PostStats("threads_04", current_vph=2000, author_avg_vph=15, author_std_vph=5),
        topic=TopicContext("#viral_challenge", 0.9),
        expected_flag="HIGH",
        description="Small Threads account real viral explosion in red ocean",
    ),
    TestCase(
        stats=PostStats("threads_05", current_vph=200, author_avg_vph=80, author_std_vph=40),
        topic=TopicContext("#kpop", 0.95),
        expected_flag="HIGH",
        description="Moderate Threads explosion boosted by red ocean hashtag",
    ),
    TestCase(
        stats=PostStats("threads_06", current_vph=200, author_avg_vph=80, author_std_vph=40),
        topic=TopicContext("#niche_craft", 0.05),
        expected_flag="MEDIUM",
        description="Moderate Threads explosion in blue ocean stays MEDIUM",
    ),
]


def evaluate_weights(config: WeightConfig) -> tuple[float, str]:
    """
    Run test battery with given weights, return (score, summary).

    Score = percentage of correct flag predictions (0-100).
    """
    pipeline = ExplosionScoringPipeline(
        phase1=Phase1PostExplosion(
            min_vph_threshold=config.min_vph_threshold,
            min_std_floor=config.min_std_floor,
        ),
        phase2=Phase2RedOceanMultiplier(
            weight=config.red_ocean_weight,
            cap=config.red_ocean_cap,
        ),
        phase3=Phase3UsabilityOutput(
            high_threshold=config.high_threshold,
            low_threshold=config.low_threshold,
        ),
    )

    correct = 0
    lines: list[str] = []

    for tc in TEST_BATTERY:
        result = pipeline.score(tc.stats, tc.topic)
        match = result.usability_flag == tc.expected_flag
        if match:
            correct += 1
        status = "PASS" if match else "FAIL"
        lines.append(
            f"  [{status}] {tc.description}: "
            f"expected={tc.expected_flag}, got={result.usability_flag} "
            f"(z={result.post_burst_score:.2f}, mult={result.red_ocean_multiplier:.2f}, "
            f"final={result.final_score:.1f})"
        )

    score = (correct / len(TEST_BATTERY)) * 100
    summary = (
        f"Fitness: {score:.0f}% ({correct}/{len(TEST_BATTERY)} correct)\n"
        + "\n".join(lines)
    )
    return score, summary
