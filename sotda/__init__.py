"""SOTDA Threads — explosion-focus scoring for Threads Graph API posts."""

from sotda.pipeline import (
    ExplosionScoringPipeline,
    Phase1PostExplosion,
    Phase2RedOceanMultiplier,
    Phase3UsabilityOutput,
    PostStats,
    ScoringResult,
    TopicContext,
)

__all__ = [
    "ExplosionScoringPipeline",
    "Phase1PostExplosion",
    "Phase2RedOceanMultiplier",
    "Phase3UsabilityOutput",
    "PostStats",
    "ScoringResult",
    "TopicContext",
]

__version__ = "0.1.0"
