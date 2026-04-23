"""Evaluator test battery smoke test."""

from sotda.evaluator import TEST_BATTERY, evaluate_weights
from sotda.generator import WeightConfig


def test_battery_has_six_cases():
    assert len(TEST_BATTERY) == 6


def test_all_cases_use_poststats():
    """Ensure Threads native types throughout."""
    for tc in TEST_BATTERY:
        assert hasattr(tc.stats, "post_id")
        assert hasattr(tc.stats, "author_avg_vph")
        assert not hasattr(tc.stats, "video_id")


def test_all_topics_are_hashtags():
    """Threads topics are hashtag-style tags."""
    for tc in TEST_BATTERY:
        assert tc.topic.topic.startswith("#")


def test_default_weights_hit_baseline_fitness():
    """Default weights should pass at least 5/6 scenarios (baseline fitness 83%+)."""
    config = WeightConfig()
    score, _ = evaluate_weights(config)
    assert score >= 80.0, f"Baseline fitness too low: {score}"


def test_summary_mentions_all_cases():
    config = WeightConfig()
    _, summary = evaluate_weights(config)
    for tc in TEST_BATTERY:
        assert tc.description in summary
