"""Generate golden_vectors.json for SOTDA Threads — language-agnostic
verification data.

Usage:
    python scripts/gen_golden_vectors.py > golden_vectors.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sotda import formulas as f


def vectors():
    yield ("modified_z",
           {"x": 1_000_000, "values": [1000, 1200, 800, 1500, 900, 1100, 1300, 1_000_000]},
           f.modified_z(1_000_000, [1000, 1200, 800, 1500, 900, 1100, 1300, 1_000_000]))
    yield ("modified_z_empty", {"x": 100, "values": []}, f.modified_z(100, []))

    yield ("alert_level_viral", {"z_score": 5.5}, f.alert_level(5.5))
    yield ("alert_level_surge", {"z_score": 4.0}, f.alert_level(4.0))
    yield ("alert_level_trending", {"z_score": 3.2}, f.alert_level(3.2))
    yield ("alert_level_watch", {"z_score": 2.5}, f.alert_level(2.5))
    yield ("alert_level_none", {"z_score": 1.0}, f.alert_level(1.0))

    yield ("surge_z_spike", {"today": 500, "rolling_window": [100]*7}, f.surge_z(500, [100]*7))
    yield ("surge_z_flat", {"today": 100, "rolling_window": [100]*7}, f.surge_z(100, [100]*7))

    z, _ = f.z_vph(300, 100, 50)
    yield ("z_vph_normal", {"current_vph": 300, "author_avg_vph": 100, "author_std_vph": 50}, z)
    z2, _ = f.z_vph(100, 10, 3)
    yield ("z_vph_small_dampened", {"current_vph": 100, "author_avg_vph": 10, "author_std_vph": 3}, z2)

    yield ("red_ocean_blue", {"topic_saturation": 0.1}, f.red_ocean_multiplier(0.1))
    yield ("red_ocean_capped", {"topic_saturation": 1.0}, f.red_ocean_multiplier(1.0))
    yield ("final_score", {"z": 4.0, "multiplier": 1.2}, f.final_score_v1(4.0, 1.2))

    yield ("engagement_rate",
           {"likes": 5000, "replies": 500, "views": 100_000},
           f.engagement_rate(5000, 500, 100_000))
    yield ("like_ratio",
           {"likes": 4200, "views": 100_000},
           f.like_ratio(4200, 100_000))

    yield ("account_momentum",
           {"views_30d": 200_000, "views_prev_30d": 100_000,
            "followers_30d_gained": 1500, "followers_prev_30d_gained": 1000},
           f.account_momentum(200_000, 100_000, 1500, 1000))
    yield ("views_per_follower",
           {"avg_views_90d": 10_000, "total_followers": 100_000},
           f.views_per_follower(10_000, 100_000))
    yield ("outlier_ratio",
           {"post_views": 50_000, "account_avg_views": 10_000},
           f.outlier_ratio(50_000, 10_000))
    yield ("content_efficiency",
           {"views_30d": 100_000, "posts_30d": 4},
           f.content_efficiency(100_000, 4))

    regular = [86400.0 * i for i in range(10)]
    yield ("posting_consistency_regular",
           {"post_timestamps_unix": regular},
           f.posting_consistency(regular))

    yield ("audience_credibility_real", {"follower_engagement_rate": 0.06}, f.audience_credibility(0.06))
    yield ("audience_credibility_suspicious", {"follower_engagement_rate": 0.02}, f.audience_credibility(0.02))

    yield ("follower_conversion",
           {"followers_gained": 83, "views": 10_000},
           f.follower_conversion(83, 10_000))

    yield ("account_health_score_perfect",
           {"engagement_rate_norm": 100, "posting_consistency_norm": 100,
            "views_per_follower_norm": 100, "content_efficiency_norm": 100,
            "posting_frequency_norm": 100, "follower_conversion_norm": 100,
            "audience_credibility_norm": 100},
           f.account_health_score(100, 100, 100, 100, 100, 100, 100))

    yield ("growth_trigger_true", {"growth_7d_ratio": 3.0}, f.growth_trigger(3.0))
    yield ("growth_trigger_false", {"growth_7d_ratio": 1.5}, f.growth_trigger(1.5))

    # Threads-specific (T-1..T-9)
    yield ("repost_rate", {"reposts": 110, "views": 12_500}, f.repost_rate(110, 12_500))
    yield ("quote_rate", {"quotes": 30, "views": 12_500}, f.quote_rate(30, 12_500))
    yield ("viral_velocity_24h_early",
           {"reposts": 100, "hours_since_post": 2},
           f.viral_velocity_24h(100, 2))
    yield ("viral_velocity_24h_capped",
           {"reposts": 480, "hours_since_post": 120},
           f.viral_velocity_24h(480, 120))
    yield ("reply_ratio", {"replies": 55, "views": 12_500}, f.reply_ratio(55, 12_500))
    yield ("threads_satisfaction_perfect",
           {"reply_ratio_val": 0.05, "repost_rate_val": 0.03,
            "quote_rate_val": 0.02, "follower_gain_rate": 0.01},
           f.threads_satisfaction(0.05, 0.03, 0.02, 0.01))
    yield ("media_type_branch_text",
           {"media_type": "TEXT_POST"}, list(f.media_type_branch("TEXT_POST")))
    yield ("media_type_branch_video",
           {"media_type": "VIDEO"}, list(f.media_type_branch("VIDEO")))
    yield ("share_rate", {"shares": 18, "views": 12_500}, f.share_rate(18, 12_500))
    yield ("quote_to_reply_ratio", {"quotes": 30, "replies": 55}, f.quote_to_reply_ratio(30, 55))
    yield ("link_attachment_penalty_with",
           {"link_attachment_url": "https://example.com"},
           f.link_attachment_penalty("https://example.com"))
    yield ("link_attachment_penalty_without",
           {"link_attachment_url": None},
           f.link_attachment_penalty(None))


def main():
    data = {
        "spec_version": "0.3.0",
        "platform": "threads",
        "package": "sotda",
        "tolerance": 1e-9,
        "vectors": [
            {"formula": name, "input": inp, "expected": exp}
            for name, inp, exp in vectors()
        ],
    }
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
