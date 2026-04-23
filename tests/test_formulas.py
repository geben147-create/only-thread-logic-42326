"""
Per-formula unit tests — all 26 formulas exercised with known inputs.

Each test verifies the formula actually computes the expected number
for Threads-API-realistic inputs. Catches regression if someone tweaks
a threshold or a weight.
"""

import math
import pytest

from sotda import formulas as f


# ──────────────────────────────────────────────────────────
# 🟢 Trend detection (3)
# ──────────────────────────────────────────────────────────

class TestModifiedZ:
    def test_viral_outlier_flagged(self):
        """D-3b: 1M views in an otherwise 1K baseline should mz > 100."""
        baseline = [1000, 1200, 800, 1500, 900, 1100, 1300]
        z = f.modified_z(1_000_000, baseline + [1_000_000])
        assert z > 100

    def test_normal_value_near_zero(self):
        z = f.modified_z(1000, [900, 1000, 1100, 950, 1050])
        assert abs(z) < 1.5

    def test_empty_returns_zero(self):
        assert f.modified_z(100, []) == 0.0

    def test_zero_mad_no_divide_error(self):
        """All-identical list → MAD=0; formula must not divide by zero."""
        z = f.modified_z(100, [50, 50, 50, 50])
        assert math.isfinite(z)


class TestAlertLevel:
    def test_viral(self):
        assert f.alert_level(5.5) == "viral"

    def test_surge_by_z(self):
        assert f.alert_level(4.0) == "surge"

    def test_surge_by_growth(self):
        assert f.alert_level(1.0, growth_7d=2.5) == "surge"

    def test_trending(self):
        assert f.alert_level(3.2) == "trending"

    def test_watch(self):
        assert f.alert_level(2.5) == "watch"

    def test_none(self):
        assert f.alert_level(1.0) == "none"


class TestSurgeZ:
    def test_sudden_spike(self):
        """D-2a: 5x jump on flat baseline → large positive z."""
        z = f.surge_z(500, [100] * 7)
        assert z > 3.0  # std was 0 → floored to 1, z=(500-100)/1=400 but we only need > 3

    def test_no_change(self):
        z = f.surge_z(100, [100] * 7)
        assert abs(z) < 0.01

    def test_too_small_window(self):
        assert f.surge_z(100, [100]) == 0.0


# ──────────────────────────────────────────────────────────
# 🟢 Post analysis (5)
# ──────────────────────────────────────────────────────────

class TestZVPH:
    def test_normal_account(self):
        """A-1: healthy baseline, no correction."""
        z, corr = f.z_vph(current_vph=300, author_avg_vph=100, author_std_vph=50)
        assert z == pytest.approx(4.0)
        assert corr == []

    def test_small_account_dampened(self):
        z, corr = f.z_vph(current_vph=100, author_avg_vph=10, author_std_vph=3)
        assert z < 5.0  # log1p damped
        assert any("log_scaling" in c for c in corr)

    def test_std_floor_applied(self):
        z, corr = f.z_vph(current_vph=50, author_avg_vph=10, author_std_vph=0.5)
        assert any("std_floor" in c for c in corr)
        assert math.isfinite(z)


class TestRedOceanMultiplier:
    def test_blue_ocean_minimal_boost(self):
        assert f.red_ocean_multiplier(0.1) == pytest.approx(1.05)

    def test_red_ocean_capped(self):
        assert f.red_ocean_multiplier(1.0) == pytest.approx(1.5)

    def test_extreme_sat_still_capped(self):
        assert f.red_ocean_multiplier(5.0, weight=1.0, cap=1.5) == pytest.approx(1.5)

    def test_invalid_cap_raises(self):
        with pytest.raises(ValueError):
            f.red_ocean_multiplier(0.5, cap=0.5)


class TestFinalScoreV1:
    def test_known_composition(self):
        """A-3: z=4, mult=1.2, scale=50, base=50 → 4*1.2*50+50 = 290."""
        assert f.final_score_v1(4.0, 1.2) == pytest.approx(290.0)

    def test_custom_scale(self):
        assert f.final_score_v1(2.0, 1.5, scale=10, base=0) == pytest.approx(30.0)


class TestEngagementRate:
    def test_standard(self):
        """B-4a: (likes + replies) / views — Threads (replies, not comments)."""
        assert f.engagement_rate(likes=5000, replies=500, views=100_000) == pytest.approx(0.055)

    def test_zero_views(self):
        assert f.engagement_rate(100, 10, 0) == 0.0


class TestLikeRatio:
    def test_standard(self):
        assert f.like_ratio(4200, 100_000) == pytest.approx(0.042)

    def test_zero_views(self):
        assert f.like_ratio(0, 0) == 0.0


# ──────────────────────────────────────────────────────────
# 🟢 Account analysis (9)
# ──────────────────────────────────────────────────────────

class TestAccountMomentum:
    def test_accelerating(self):
        """CH-1: views 2x + followers 1.5x = 3.0x momentum."""
        m = f.account_momentum(200_000, 100_000, 1500, 1000)
        assert m == pytest.approx(3.0)

    def test_stable(self):
        m = f.account_momentum(100_000, 100_000, 1000, 1000)
        assert m == pytest.approx(1.0)

    def test_zero_prev(self):
        assert f.account_momentum(100_000, 0, 1000, 500) == 0.0


class TestViewsPerFollower:
    def test_healthy(self):
        """CH-2: 10K views / 100K followers = 10%."""
        assert f.views_per_follower(10_000, 100_000) == pytest.approx(0.10)

    def test_dead_followers(self):
        assert f.views_per_follower(1_000, 100_000) == pytest.approx(0.01)

    def test_zero_followers(self):
        assert f.views_per_follower(5_000, 0) == 0.0


class TestOutlierRatio:
    def test_5x_breakout(self):
        assert f.outlier_ratio(50_000, 10_000) == pytest.approx(5.0)

    def test_underperformer(self):
        assert f.outlier_ratio(3_000, 10_000) == pytest.approx(0.3)

    def test_zero_baseline(self):
        assert f.outlier_ratio(50_000, 0) == 0.0


class TestContentEfficiency:
    def test_efficient_creator(self):
        """CH-4: 100K views / 4 posts = 25K per post."""
        assert f.content_efficiency(100_000, 4) == pytest.approx(25_000)

    def test_zero_posts(self):
        assert f.content_efficiency(0, 0) == 0.0


class TestPostingConsistency:
    def test_perfectly_regular(self):
        """Daily posting: intervals all 86400s → std=0 → consistency=1.0."""
        timestamps = [86400.0 * i for i in range(10)]
        assert f.posting_consistency(timestamps) == pytest.approx(1.0)

    def test_irregular_approaches_zero(self):
        timestamps = [0, 3600, 86400 * 10, 86400 * 10 + 60, 86400 * 30]
        c = f.posting_consistency(timestamps)
        assert 0.0 < c < 0.01  # huge std → near 0

    def test_too_few_posts(self):
        assert f.posting_consistency([0, 86400]) == 0.0


class TestAudienceCredibility:
    def test_real(self):
        assert f.audience_credibility(0.06) == "REAL"

    def test_suspicious(self):
        assert f.audience_credibility(0.02) == "SUSPICIOUS"

    def test_threshold_boundary(self):
        assert f.audience_credibility(0.05) == "REAL"


class TestFollowerConversion:
    def test_standard(self):
        """C-2b: 83 new followers per 10K views = 0.83%."""
        assert f.follower_conversion(83, 10_000) == pytest.approx(0.0083)

    def test_zero_views(self):
        assert f.follower_conversion(10, 0) == 0.0


class TestAccountHealthScore:
    def test_excellent_account(self):
        score = f.account_health_score(90, 80, 70, 85, 75, 60, 90)
        assert score > 70

    def test_weak_account(self):
        score = f.account_health_score(20, 10, 15, 10, 5, 5, 30)
        assert score < 20

    def test_weights_sum_to_1(self):
        score = f.account_health_score(100, 100, 100, 100, 100, 100, 100)
        assert score == pytest.approx(100.0)


class TestGrowthTrigger:
    def test_surge_detected(self):
        """D-4b: 300% growth in 7d → surge."""
        assert f.growth_trigger(3.0) is True

    def test_below_threshold(self):
        assert f.growth_trigger(1.5) is False


# ──────────────────────────────────────────────────────────
# 🔵 Threads-only (9)
# ──────────────────────────────────────────────────────────

class TestRepostRate:
    def test_standard(self):
        """T-1: 110 reposts / 12500 views = ~0.88%."""
        assert f.repost_rate(110, 12_500) == pytest.approx(0.0088, abs=1e-4)

    def test_zero_views(self):
        assert f.repost_rate(5, 0) == 0.0


class TestQuoteRate:
    def test_standard(self):
        assert f.quote_rate(30, 12_500) == pytest.approx(0.0024, abs=1e-4)


class TestViralVelocity24h:
    def test_early_burst(self):
        """T-3: 100 reposts in first 2h → 50 rp/h."""
        assert f.viral_velocity_24h(100, 2) == pytest.approx(50.0)

    def test_capped_at_24h(self):
        """120h later, denominator still capped at 24h."""
        assert f.viral_velocity_24h(480, 120) == pytest.approx(20.0)

    def test_floor_at_1h(self):
        """Just posted (<1h) still reads as 1h to avoid blowup."""
        assert f.viral_velocity_24h(10, 0.1) == pytest.approx(10.0)


class TestReplyRatio:
    def test_standard(self):
        """T-4: 55 replies / 12.5K views = ~0.44%."""
        assert f.reply_ratio(55, 12_500) == pytest.approx(0.0044, abs=1e-4)


class TestThreadsSatisfaction:
    def test_perfect_post(self):
        """All metrics at target → score ≈ 100."""
        score = f.threads_satisfaction(
            reply_ratio_val=0.05,   # target
            repost_rate_val=0.03,
            quote_rate_val=0.02,
            follower_gain_rate=0.01,
        )
        assert score == pytest.approx(100.0)

    def test_mediocre_post(self):
        """Half of each target → score ≈ 50."""
        score = f.threads_satisfaction(
            reply_ratio_val=0.025, repost_rate_val=0.015,
            quote_rate_val=0.01, follower_gain_rate=0.005,
        )
        assert score == pytest.approx(50.0, abs=1.0)

    def test_zero_post(self):
        assert f.threads_satisfaction(0, 0, 0, 0) == 0.0


class TestMediaTypeBranch:
    def test_text_post_threshold(self):
        high, low = f.media_type_branch("TEXT_POST")
        assert high == 180.0 and low == 70.0

    def test_video_threshold(self):
        high, low = f.media_type_branch("VIDEO")
        assert high == 220.0 and low == 80.0

    def test_carousel_threshold(self):
        high, low = f.media_type_branch("CAROUSEL_ALBUM")
        assert high == 210.0 and low == 78.0

    def test_unknown_falls_back(self):
        high, low = f.media_type_branch("REPOST_FACILITATOR")
        assert high == 210.0 and low == 75.0


class TestShareRate:
    def test_standard(self):
        assert f.share_rate(18, 12_500) == pytest.approx(0.00144, abs=1e-5)


class TestQuoteToReplyRatio:
    def test_debated_post(self):
        """T-8: 30 quotes / 55 replies = 0.545 (debate)."""
        assert f.quote_to_reply_ratio(30, 55) == pytest.approx(0.545, abs=0.01)

    def test_no_replies(self):
        assert f.quote_to_reply_ratio(10, 0) == 0.0


class TestLinkAttachmentPenalty:
    def test_with_link(self):
        """T-9: external link → 30% reach reduction."""
        assert f.link_attachment_penalty("https://example.com") == 0.7

    def test_no_link(self):
        assert f.link_attachment_penalty(None) == 1.0

    def test_empty_string_no_penalty(self):
        """Empty string is not a real link."""
        assert f.link_attachment_penalty("") == 1.0


# ──────────────────────────────────────────────────────────
# Integration — formulas compose into the pipeline result
# ──────────────────────────────────────────────────────────

class TestFormulaPipelineIntegration:
    def test_z_vph_matches_pipeline_phase1(self):
        """z_vph() function must produce the same z as Phase1PostExplosion."""
        from sotda.pipeline import Phase1PostExplosion, PostStats
        phase1 = Phase1PostExplosion()
        stats = PostStats("x", current_vph=500, author_avg_vph=100, author_std_vph=50)
        pipeline_z, pipeline_corr = phase1.compute(stats)
        formula_z, formula_corr = f.z_vph(500, 100, 50)
        assert pipeline_z == pytest.approx(formula_z)
        assert pipeline_corr == formula_corr

    def test_red_ocean_formula_matches_phase2(self):
        from sotda.pipeline import Phase2RedOceanMultiplier, TopicContext
        phase2 = Phase2RedOceanMultiplier(weight=0.5, cap=1.5)
        pipeline_m = phase2.compute(TopicContext("x", 0.3))
        formula_m = f.red_ocean_multiplier(0.3, weight=0.5, cap=1.5)
        assert pipeline_m == pytest.approx(formula_m)

    def test_final_score_formula_matches_phase3(self):
        from sotda.pipeline import Phase3UsabilityOutput
        phase3 = Phase3UsabilityOutput()
        result = phase3.compute(z_vph=4.0, multiplier=1.2, corrections=[])
        formula_fs = f.final_score_v1(4.0, 1.2)
        assert result.final_score == pytest.approx(formula_fs)


def test_all_26_formulas_exported():
    """Guard: __all__ must list every public formula function."""
    expected = {
        # trend
        "modified_z", "alert_level", "surge_z",
        # post
        "z_vph", "red_ocean_multiplier", "final_score_v1",
        "engagement_rate", "like_ratio",
        # account
        "account_momentum", "views_per_follower", "outlier_ratio",
        "content_efficiency", "posting_consistency", "audience_credibility",
        "follower_conversion", "account_health_score", "growth_trigger",
        # threads-only
        "repost_rate", "quote_rate", "viral_velocity_24h", "reply_ratio",
        "threads_satisfaction", "media_type_branch", "share_rate",
        "quote_to_reply_ratio", "link_attachment_penalty",
    }
    # 17 공통 + 9 Threads 전용 = 26 (z_vph + red_ocean + final_score are both
    # in pipeline.py as classes AND in formulas.py as functions)
    assert len(expected) == 26
    for name in expected:
        assert hasattr(f, name), f"formulas.{name} missing"
        assert name in f.__all__, f"{name} not in __all__"
