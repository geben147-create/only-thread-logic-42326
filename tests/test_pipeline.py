"""
3-Phase pipeline tests — Threads native.

Covers:
  - Normal account baseline behavior (no correction needed)
  - Small account correction (log scaling + std floor)
  - Red ocean multiplier (blue/red/cap)
  - Output separation (all fields present, red ocean boosts final)
"""

import math

import pytest

from sotda.pipeline import (
    ExplosionScoringPipeline,
    Phase1PostExplosion,
    Phase2RedOceanMultiplier,
    Phase3UsabilityOutput,
    PostStats,
    TopicContext,
)


# ──────────────────────────────────────────────
# Phase 1: Normal account (avg_vph >= 50)
# ──────────────────────────────────────────────

class TestNormalAccount:
    """Threads accounts with healthy baselines — no correction should apply."""

    def test_moderate_explosion(self, pipeline, blue_ocean_topic):
        stats = PostStats(
            post_id="normal_01",
            current_vph=300,
            author_avg_vph=100,
            author_std_vph=50,
        )
        result = pipeline.score(stats, blue_ocean_topic)
        # z = (300 - 100) / 50 = 4.0 — genuine explosion
        assert result.post_burst_score == pytest.approx(4.0)
        assert result.usability_flag == "HIGH"
        assert len(result.corrections_applied) == 0

    def test_no_explosion(self, pipeline, blue_ocean_topic):
        stats = PostStats(
            post_id="normal_02",
            current_vph=110,
            author_avg_vph=100,
            author_std_vph=50,
        )
        result = pipeline.score(stats, blue_ocean_topic)
        assert result.post_burst_score == pytest.approx(0.2)
        assert result.usability_flag == "LOW"

    def test_negative_z_score(self, pipeline, blue_ocean_topic):
        stats = PostStats(
            post_id="normal_03",
            current_vph=30,
            author_avg_vph=100,
            author_std_vph=50,
        )
        result = pipeline.score(stats, blue_ocean_topic)
        assert result.post_burst_score < 0


# ──────────────────────────────────────────────
# Phase 1: Small account (avg_vph < 50)
# ──────────────────────────────────────────────

class TestSmallAccountCorrection:
    """
    Small Threads accounts with tiny baselines (10-20 views avg).
    Without correction, z-scores explode to absurd values.
    Log scaling + std floor must dampen these.
    """

    def test_small_account_z_is_dampened(self, pipeline, blue_ocean_topic):
        stats = PostStats(
            post_id="small_01",
            current_vph=100,
            author_avg_vph=10,
            author_std_vph=3,
        )
        result = pipeline.score(stats, blue_ocean_topic)
        # Without correction: z = (100-10)/5 = 18.0 (absurd for Threads too)
        # With log1p: log1p(18.0) ≈ 2.94 (reasonable)
        assert result.post_burst_score < 5.0
        assert any("log_scaling" in c for c in result.corrections_applied)

    def test_very_small_account_extreme_case(self, pipeline, blue_ocean_topic):
        stats = PostStats(
            post_id="small_02",
            current_vph=500,
            author_avg_vph=5,
            author_std_vph=1,
        )
        result = pipeline.score(stats, blue_ocean_topic)
        # Without correction: z = (500-5)/5 = 99.0 (broken)
        # With log1p: log1p(99.0) ≈ 4.60 (sane)
        assert result.post_burst_score < 6.0

    def test_std_floor_applied(self):
        phase1 = Phase1PostExplosion(min_std_floor=5.0)
        stats = PostStats(
            post_id="small_03",
            current_vph=50,
            author_avg_vph=10,
            author_std_vph=0.5,  # near-zero std
        )
        _, corrections = phase1.compute(stats)
        assert any("std_floor" in c for c in corrections)

    def test_small_account_still_detects_real_explosion(self, pipeline, blue_ocean_topic):
        """Even with dampening, a genuine Threads explosion should score HIGH."""
        stats = PostStats(
            post_id="small_04",
            current_vph=1000,
            author_avg_vph=15,
            author_std_vph=5,
        )
        result = pipeline.score(stats, blue_ocean_topic)
        assert result.usability_flag == "HIGH"


# ──────────────────────────────────────────────
# Phase 2: Red Ocean Multiplier
# ──────────────────────────────────────────────

class TestRedOceanMultiplier:

    def test_blue_ocean_minimal_boost(self):
        phase2 = Phase2RedOceanMultiplier(weight=0.5, cap=1.5)
        topic = TopicContext(topic="#niche", saturation_index=0.1)
        mult = phase2.compute(topic)
        assert mult == pytest.approx(1.05)  # 1 + 0.1*0.5

    def test_red_ocean_capped(self):
        phase2 = Phase2RedOceanMultiplier(weight=0.5, cap=1.5)
        topic = TopicContext(topic="#viral", saturation_index=1.0)
        mult = phase2.compute(topic)
        assert mult == pytest.approx(1.5)

    def test_extreme_saturation_still_capped(self):
        phase2 = Phase2RedOceanMultiplier(weight=1.0, cap=1.5)
        topic = TopicContext(topic="#oversaturated", saturation_index=5.0)
        mult = phase2.compute(topic)
        assert mult == pytest.approx(1.5)

    def test_invalid_cap_raises(self):
        with pytest.raises(ValueError):
            Phase2RedOceanMultiplier(cap=0.5)


# ──────────────────────────────────────────────
# Phase 3: Output separation
# ──────────────────────────────────────────────

class TestOutputSeparation:

    def test_output_has_all_fields(self, pipeline, red_ocean_topic):
        stats = PostStats(
            post_id="out_01",
            current_vph=200,
            author_avg_vph=80,
            author_std_vph=40,
        )
        result = pipeline.score(stats, red_ocean_topic)
        output = result.to_dict()
        assert "post_burst_score" in output
        assert "red_ocean_multiplier" in output
        assert "final_score" in output
        assert "usability_flag" in output
        # Threads-native: no legacy video_burst_score
        assert "video_burst_score" not in output

    def test_red_ocean_boosts_final_score(self, pipeline):
        stats = PostStats(
            post_id="cmp_01",
            current_vph=200,
            author_avg_vph=80,
            author_std_vph=40,
        )
        blue = TopicContext(topic="#blue", saturation_index=0.0)
        red = TopicContext(topic="#red", saturation_index=1.0)

        score_blue = pipeline.score(stats, blue).final_score
        score_red = pipeline.score(stats, red).final_score
        assert score_red > score_blue

    def test_final_score_is_finite_with_zero_std(self, pipeline, blue_ocean_topic):
        """Guard against 0-division when author_std_vph == 0 (new accounts)."""
        stats = PostStats(
            post_id="zero_std",
            current_vph=100,
            author_avg_vph=60,
            author_std_vph=0.0,
        )
        result = pipeline.score(stats, blue_ocean_topic)
        assert math.isfinite(result.final_score)
