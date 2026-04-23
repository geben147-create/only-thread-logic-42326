"""SOTDA Threads — explosion-focus scoring for Threads Graph API posts.

Two layers of API:
  1. 3-phase pipeline (opinionated composition):
       ExplosionScoringPipeline, PostStats, TopicContext, ScoringResult
       → one call, scored with correction/multiplier/flag.
  2. Individual formulas (pick-and-mix):
       from sotda.formulas import engagement_rate, repost_rate, ...
       → 26 pure functions, use standalone in your own composition.
"""

from sotda.pipeline import (
    ExplosionScoringPipeline,
    Phase1PostExplosion,
    Phase2RedOceanMultiplier,
    Phase3UsabilityOutput,
    PostStats,
    ScoringResult,
    TopicContext,
)
from sotda import formulas  # re-export the module for convenience

__all__ = [
    "ExplosionScoringPipeline",
    "Phase1PostExplosion",
    "Phase2RedOceanMultiplier",
    "Phase3UsabilityOutput",
    "PostStats",
    "ScoringResult",
    "TopicContext",
    "formulas",
]

__version__ = "0.2.0"
