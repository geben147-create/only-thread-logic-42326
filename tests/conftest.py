"""Pytest fixtures shared across Threads scoring tests."""

import pytest

from sotda.pipeline import (
    ExplosionScoringPipeline,
    Phase1PostExplosion,
    Phase2RedOceanMultiplier,
    Phase3UsabilityOutput,
    PostStats,
    TopicContext,
)


@pytest.fixture
def pipeline():
    return ExplosionScoringPipeline()


@pytest.fixture
def blue_ocean_topic():
    return TopicContext(topic="#niche_craft", saturation_index=0.1)


@pytest.fixture
def red_ocean_topic():
    return TopicContext(topic="#viral_challenge", saturation_index=0.9)


@pytest.fixture
def normal_author_stats():
    """Healthy Threads account baseline (avg_vph=100)."""
    return lambda post_id, vph: PostStats(
        post_id=post_id,
        current_vph=vph,
        author_avg_vph=100,
        author_std_vph=50,
    )


@pytest.fixture
def small_author_stats():
    """Small Threads account baseline (avg_vph < threshold)."""
    return lambda post_id, vph: PostStats(
        post_id=post_id,
        current_vph=vph,
        author_avg_vph=15,
        author_std_vph=5,
    )
