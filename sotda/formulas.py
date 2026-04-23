"""
All 26 Threads scoring formulas as pure callable functions.

Each function takes Threads Graph API primitives and returns a number
(or label). Import what you need; mix freely in your own program.

Categories
----------
🟢 공통 (17) — YouTube ⇄ Threads 동일 수식, 필드명만 rename
  • Trend detection (statistics, domain-agnostic): modified_z,
    alert_level, surge_z
  • Post analysis: z_vph, final_score_v1, red_ocean_multiplier,
    engagement_rate, like_ratio
  • Account analysis: account_momentum, views_per_follower,
    outlier_ratio, content_efficiency, posting_consistency,
    audience_credibility, follower_conversion, account_health_score,
    growth_trigger

🔵 Threads 전용 (9) — reposts / quotes / shares / media_type 활용
  • repost_rate, quote_rate, viral_velocity_24h, reply_ratio,
    threads_satisfaction, media_type_branch, share_rate,
    quote_to_reply_ratio, link_attachment_penalty

See docs/FORMULA_MASTER.md for full scoring tables and priorities.
"""

from __future__ import annotations

import math
import statistics
from typing import Literal, Optional


# ══════════════════════════════════════════════════════════════════
# 🟢 COMMON — Trend Detection (3)  |  statistics/domain-agnostic
# ══════════════════════════════════════════════════════════════════

def modified_z(x: float, values: list[float]) -> float:
    """**D-3b** modified Z-score via MAD (Median Absolute Deviation).

    More robust to outliers than the standard z-score.

    Parameters:
      x:       The value to score (may or may not be in `values`).
      values:  The reference distribution. Typically the last N
               observations of the same metric. **May include x or
               not** — results barely differ (see audit §2). Convention:
               pass the full history including the current observation.

    >>> round(modified_z(1_000_000, [1000, 1200, 800, 1500, 900, 1100, 1300, 1000000]), 1) > 100
    True
    """
    if not values:
        return 0.0
    median = statistics.median(values)
    deviations = [abs(v - median) for v in values]
    mad = statistics.median(deviations)
    if mad == 0:
        mad = 1.0
    return 0.6745 * (x - median) / mad


AlertLevel = Literal["viral", "surge", "trending", "watch", "none"]


def alert_level(z_score: float, growth_7d: float = 0.0) -> AlertLevel:
    """**D-4a** trend urgency classification.

    Thresholds (either z-score OR growth_7d can trigger):
      viral    — z > 5.0
      surge    — z > 3.5 or growth_7d > 2.0
      trending — z > 3.0 or growth_7d > 1.0
      watch    — z > 2.0 or growth_7d > 0.5
      none     — otherwise
    """
    if z_score > 5.0:
        return "viral"
    if z_score > 3.5 or growth_7d > 2.0:
        return "surge"
    if z_score > 3.0 or growth_7d > 1.0:
        return "trending"
    if z_score > 2.0 or growth_7d > 0.5:
        return "watch"
    return "none"


def surge_z(today: float, rolling_window: list[float]) -> float:
    """**D-2a** keyword/metric spike z-score.

    formula: (today - rolling_mean) / rolling_std

    >>> abs(surge_z(100, [100]*7)) < 0.01
    True
    """
    if len(rolling_window) < 2:
        return 0.0
    mean = statistics.mean(rolling_window)
    std = statistics.stdev(rolling_window)
    if std == 0:
        std = 1.0
    return (today - mean) / std


# ══════════════════════════════════════════════════════════════════
# 🟢 COMMON — Post Analysis (5)
# ══════════════════════════════════════════════════════════════════

def z_vph(
    current_vph: float,
    author_avg_vph: float,
    author_std_vph: float,
    min_vph_threshold: float = 50.0,
    min_std_floor: float = 5.0,
) -> tuple[float, list[str]]:
    """**A-1** z-VPH — account-relative explosion score.

    formula: (current_vph - author_avg_vph) / author_std_vph
    with small-account corrections:
      • std floor to prevent near-zero denominator
      • log1p dampening when author_avg is below threshold

    Returns (z_score, corrections_applied).
    """
    corrections: list[str] = []
    effective_std = max(author_std_vph, min_std_floor)
    if author_std_vph < min_std_floor:
        corrections.append(
            f"std_floor_applied: {author_std_vph:.2f} -> {effective_std:.2f}"
        )
    raw_z = (current_vph - author_avg_vph) / effective_std
    if author_avg_vph < min_vph_threshold:
        dampened = math.log1p(abs(raw_z)) * (1 if raw_z >= 0 else -1)
        corrections.append(
            f"log_scaling_applied: raw_z={raw_z:.2f} -> dampened_z={dampened:.2f}"
        )
        return dampened, corrections
    return raw_z, corrections


def red_ocean_multiplier(
    topic_saturation: float, weight: float = 0.5, cap: float = 1.5
) -> float:
    """**A-2** red-ocean competition accelerator.

    formula: 1 + min(saturation * weight, cap - 1)
    Treats high competition as a positive signal (demand is proven).
    """
    if cap < 1.0:
        raise ValueError(f"cap must be >= 1.0, got {cap}")
    return 1.0 + min(topic_saturation * weight, cap - 1.0)


def final_score_v1(
    z: float, multiplier: float, base: float = 50.0, scale: float = 50.0
) -> float:
    """**A-3** final composite score.

    formula: z * multiplier * scale + base
    Default scale/base normalize a healthy post into ~0-400 range.
    """
    return z * multiplier * scale + base


def engagement_rate(likes: int, replies: int, views: int) -> float:
    """**B-4a** engagement rate for Threads posts.

    formula: (likes + replies) / views
    Threads uses replies; shares excluded to match industry convention.
    """
    if views <= 0:
        return 0.0
    return (likes + replies) / views


def like_ratio(likes: int, views: int) -> float:
    """**C-1a** like-to-view ratio."""
    if views <= 0:
        return 0.0
    return likes / views


# ══════════════════════════════════════════════════════════════════
# 🟢 COMMON — Account Analysis (9)
# ══════════════════════════════════════════════════════════════════

def account_momentum(
    views_30d: int,
    views_prev_30d: int,
    followers_30d_gained: int,
    followers_prev_30d_gained: int,
) -> float:
    """**CH-1** month-over-month growth acceleration.

    formula: (views_30d / views_prev) * (followers_30d / followers_prev)
    1.0 = stable, >1.0 accelerating, <1.0 decelerating.
    """
    if views_prev_30d <= 0 or followers_prev_30d_gained <= 0:
        return 0.0
    return (views_30d / views_prev_30d) * (
        followers_30d_gained / followers_prev_30d_gained
    )


def views_per_follower(avg_views_90d: float, total_followers: int) -> float:
    """**CH-2** views-per-follower (audience activity).

    Healthy: 0.10+ (10% of followers viewing).
    <0.03 suggests dead/bought followers.
    """
    if total_followers <= 0:
        return 0.0
    return avg_views_90d / total_followers


def outlier_ratio(post_views: int, account_avg_views: float) -> float:
    """**CH-3** breakout multiplier vs account average.

    5.0x = breakout; 0.3x = underperformer.
    """
    if account_avg_views <= 0:
        return 0.0
    return post_views / account_avg_views


def content_efficiency(views_30d: int, posts_30d: int) -> float:
    """**CH-4** average views per post.

    High value = efficient creator (low volume, high view).
    """
    if posts_30d <= 0:
        return 0.0
    return views_30d / posts_30d


def posting_consistency(post_timestamps_unix: list[float]) -> float:
    """**CH-5** posting-interval stability (scale-free).

    formula: 1 / (1 + stdev(intervals) / mean(intervals))
    i.e., `1 / (1 + coefficient_of_variation)`.

    1.0 = perfectly regular; approaches 0 = erratic. Scale-free so a
    daily schedule with ±1h jitter scores the same as a monthly
    schedule with ±1 day jitter.

    PREVIOUS FORMULA (v0.2.0): `1 / (1 + stdev(seconds))` was
    unit-dependent and collapsed to ~0 for any real data. Fixed in
    v0.3.0. See AUDIT.md §1.
    """
    if len(post_timestamps_unix) < 3:
        return 0.0
    sorted_ts = sorted(post_timestamps_unix)
    intervals = [sorted_ts[i + 1] - sorted_ts[i] for i in range(len(sorted_ts) - 1)]
    if len(intervals) < 2:
        return 0.0
    mean_int = statistics.mean(intervals)
    if mean_int <= 0:
        return 0.0
    std_int = statistics.stdev(intervals)
    cv = std_int / mean_int  # coefficient of variation
    return 1.0 / (1.0 + cv)


CredibilityLevel = Literal["REAL", "SUSPICIOUS"]


def audience_credibility(
    follower_engagement_rate: float, threshold: float = 0.05
) -> CredibilityLevel:
    """**CH-6** follower authenticity.

    NoxInfluencer standard: >= 5% engagement = REAL, else SUSPICIOUS.
    """
    return "REAL" if follower_engagement_rate >= threshold else "SUSPICIOUS"


def follower_conversion(followers_gained: int, views: int) -> float:
    """**C-2b** followers gained per view."""
    if views <= 0:
        return 0.0
    return followers_gained / views


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(val, hi))


def normalize_engagement_rate(er: float, target: float = 0.05) -> float:
    """Map raw engagement_rate to 0-100 score. Target = 5% → 100."""
    if er <= 0:
        return 0.0
    return _clamp(er / target * 100)


def normalize_posting_consistency(c: float) -> float:
    """posting_consistency already returns 0-1; scale to 0-100."""
    return _clamp(c * 100)


def normalize_views_per_follower(vpf: float, target: float = 0.10) -> float:
    """10% VPF = healthy = 100."""
    if vpf <= 0:
        return 0.0
    return _clamp(vpf / target * 100)


def normalize_content_efficiency(eff_views_per_post: float, target: float = 10_000) -> float:
    """10K views/post = 100. Domain-specific; adjust target for your niche."""
    if eff_views_per_post <= 0:
        return 0.0
    return _clamp(eff_views_per_post / target * 100)


def normalize_posting_frequency(posts_30d: int, target: int = 30) -> float:
    """30 posts/month = 100 (daily cadence)."""
    if posts_30d <= 0:
        return 0.0
    return _clamp(posts_30d / target * 100)


def normalize_follower_conversion(conv: float, target: float = 0.02) -> float:
    """2% follower-gain-per-view = 100."""
    if conv <= 0:
        return 0.0
    return _clamp(conv / target * 100)


def normalize_audience_credibility(verdict: "CredibilityLevel") -> float:
    """'REAL' → 100, 'SUSPICIOUS' → 30."""
    return 100.0 if verdict == "REAL" else 30.0


def account_health_score(
    engagement_rate_norm: float,
    posting_consistency_norm: float,
    views_per_follower_norm: float,
    content_efficiency_norm: float,
    posting_frequency_norm: float,
    follower_conversion_norm: float,
    audience_credibility_norm: float,
) -> float:
    """**CH-7** composite account health (7-indicator weighted).

    All inputs must be normalized to 0-100. Use the `normalize_*`
    helpers above to convert raw values:

        >>> score = account_health_score(
        ...     engagement_rate_norm=normalize_engagement_rate(0.05),
        ...     posting_consistency_norm=normalize_posting_consistency(0.9),
        ...     views_per_follower_norm=normalize_views_per_follower(0.1),
        ...     content_efficiency_norm=normalize_content_efficiency(15000),
        ...     posting_frequency_norm=normalize_posting_frequency(30),
        ...     follower_conversion_norm=normalize_follower_conversion(0.02),
        ...     audience_credibility_norm=normalize_audience_credibility('REAL'),
        ... )

    Output: 0-100. Weights: engagement 25%, consistency 15%, vpf 15%,
    efficiency 15%, frequency 10%, conversion 10%, credibility 10%.
    """
    return (
        0.25 * engagement_rate_norm
        + 0.15 * posting_consistency_norm
        + 0.15 * views_per_follower_norm
        + 0.15 * content_efficiency_norm
        + 0.10 * posting_frequency_norm
        + 0.10 * follower_conversion_norm
        + 0.10 * audience_credibility_norm
    )


def growth_trigger(growth_7d_ratio: float, threshold: float = 2.0) -> bool:
    """**D-4b** surge detection for account-level growth.

    True if growth_7d_ratio > 2.0 (i.e., 200%+ in past 7 days).
    """
    return growth_7d_ratio > threshold


# ══════════════════════════════════════════════════════════════════
# 🔵 THREADS-ONLY — 9 formulas using reposts/quotes/shares/media_type
# ══════════════════════════════════════════════════════════════════

def repost_rate(reposts: int, views: int) -> float:
    """**T-1** repost-to-view ratio (viral amplification).

    Threads-only: YouTube has no equivalent field.
    """
    if views <= 0:
        return 0.0
    return reposts / views


def quote_rate(quotes: int, views: int) -> float:
    """**T-2** quote-to-view ratio.

    Threads-only: high quote_rate signals the post is being used as
    material for secondary creation (meme, debate, commentary).
    """
    if views <= 0:
        return 0.0
    return quotes / views


def viral_velocity_24h(reposts: int, hours_since_post: float) -> float:
    """**T-3** early-24h repost velocity (reposts per hour).

    Threads posts typically decay within 24-48h, so we cap the
    denominator at 24h to reflect the initial explosion window.
    """
    effective_hours = min(max(hours_since_post, 1.0), 24.0)
    return reposts / effective_hours


def reply_ratio(replies: int, views: int) -> float:
    """**T-4** reply-to-view ratio (conversation index)."""
    if views <= 0:
        return 0.0
    return replies / views


def threads_satisfaction(
    reply_ratio_val: float,
    repost_rate_val: float,
    quote_rate_val: float,
    follower_gain_rate: float,
) -> float:
    """**T-5** Threads-native satisfaction composite.

    Replaces YouTube's retention-based satisfaction (retention is
    unavailable via Threads API). Internally normalizes each input
    against a target rate, then weights:

      replies   35% (target 5%)
      reposts   30% (target 3%)
      quotes    20% (target 2%)
      follower  15% (target 1%)

    Output: 0-100.
    """
    r = min(reply_ratio_val / 0.05 * 100, 100.0) if reply_ratio_val > 0 else 0.0
    p = min(repost_rate_val / 0.03 * 100, 100.0) if repost_rate_val > 0 else 0.0
    q = min(quote_rate_val / 0.02 * 100, 100.0) if quote_rate_val > 0 else 0.0
    f = min(follower_gain_rate / 0.01 * 100, 100.0) if follower_gain_rate > 0 else 0.0
    return 0.35 * r + 0.30 * p + 0.20 * q + 0.15 * f


MediaType = Literal["TEXT_POST", "IMAGE", "VIDEO", "CAROUSEL_ALBUM"]


def media_type_branch(media_type: str) -> tuple[float, float]:
    """**T-6** threshold adjustment by Threads media type.

    Returns (high_threshold, low_threshold) for Phase 3 usability flag.
    Replaces YouTube's Shorts/Long branching.

    TEXT_POST       — 180/70 (fast decay, 1-6h decisive)
    IMAGE           — 200/75 (middle, Instagram cross-surface)
    VIDEO           — 220/80 (slow growth, long tail)
    CAROUSEL_ALBUM  — 210/78 (saves drive sustained reach)
    """
    lookup = {
        "TEXT_POST": (180.0, 70.0),
        "IMAGE": (200.0, 75.0),
        "VIDEO": (220.0, 80.0),
        "CAROUSEL_ALBUM": (210.0, 78.0),
    }
    return lookup.get(media_type, (210.0, 75.0))


def share_rate(shares: int, views: int) -> float:
    """**T-7** share-to-view ratio (external distribution)."""
    if views <= 0:
        return 0.0
    return shares / views


def quote_to_reply_ratio(quotes: int, replies: int) -> float:
    """**T-8** controversy/debate index.

    High ratio suggests the post triggers quotes (public commentary)
    more than replies (direct conversation) — a debate signal.
    """
    if replies <= 0:
        return 0.0
    return quotes / replies


def link_attachment_penalty(link_attachment_url: Optional[str]) -> float:
    """**T-9** Meta algorithm penalty for external links.

    Meta suppresses reach on posts with external links by ~30%.
    Returns 0.7 if a link is attached, else 1.0.
    """
    return 0.7 if link_attachment_url else 1.0


__all__ = [
    # trend
    "modified_z", "alert_level", "surge_z", "AlertLevel",
    # post
    "z_vph", "red_ocean_multiplier", "final_score_v1",
    "engagement_rate", "like_ratio",
    # account
    "account_momentum", "views_per_follower", "outlier_ratio",
    "content_efficiency", "posting_consistency", "audience_credibility",
    "follower_conversion", "account_health_score", "growth_trigger",
    "CredibilityLevel",
    # normalization helpers for CH-7
    "normalize_engagement_rate", "normalize_posting_consistency",
    "normalize_views_per_follower", "normalize_content_efficiency",
    "normalize_posting_frequency", "normalize_follower_conversion",
    "normalize_audience_credibility",
    # threads-only
    "repost_rate", "quote_rate", "viral_velocity_24h", "reply_ratio",
    "threads_satisfaction", "media_type_branch", "share_rate",
    "quote_to_reply_ratio", "link_attachment_penalty", "MediaType",
]
