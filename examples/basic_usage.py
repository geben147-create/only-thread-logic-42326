"""
Example: Basic sotda usage — plug into ANY program that needs
Threads post explosion scoring.

Works identically for:
  - SNS content generators
  - Legal/compliance monitors
  - Korean NLP pipelines
  - Marketing dashboards
  - Competitor analysis tools
  - Research datasets
  - Alerting systems

The integration point is the same in all of them: you give the library
a `PostStats` (built from Threads Graph API fields) and a `TopicContext`,
and it returns a `ScoringResult`. What your program does with the result
is up to you.

Run it (after `pip install -e .`):
    python examples/basic_usage.py

It uses mock data, so no tokens are needed and nothing is sent to
Threads. Copy the patterns into your program and replace the mock
function with a real Threads Graph API call (kept in YOUR program,
NOT in this repo).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from sotda import ExplosionScoringPipeline, PostStats, TopicContext


# ─────────────────────────────────────────────────────────────
# MOCK: in your program, this is a real Threads Graph API call.
# ─────────────────────────────────────────────────────────────

@dataclass
class _MockThreadsInsights:
    views: int
    likes: int
    replies: int
    reposts: int
    quotes: int
    shares: int


_MOCK_DB = {
    "post_A": _MockThreadsInsights(views=12500, likes=420, replies=55, reposts=110, quotes=30, shares=18),
    "post_B": _MockThreadsInsights(views=800, likes=12, replies=2, reposts=1, quotes=0, shares=0),
    "post_C": _MockThreadsInsights(views=45000, likes=3200, replies=410, reposts=920, quotes=180, shares=75),
}


def _fetch_insights_from_threads(post_id: str) -> _MockThreadsInsights:
    """In YOUR program: call graph.threads.net. Keep the token there."""
    return _MOCK_DB[post_id]


# ─────────────────────────────────────────────────────────────
# Your program's thin wrapper around sotda (this is the ONLY
# file in your codebase that needs to touch sotda).
# ─────────────────────────────────────────────────────────────

pipeline = ExplosionScoringPipeline()


def score_live_post(
    post_id: str,
    published_at: datetime,
    author_avg_vph: float,
    author_std_vph: float,
    hashtag: str,
    hashtag_saturation: float,
) -> dict:
    """Wrap a live Threads post into sotda and get explosion score.

    Caller supplies whatever author baseline is appropriate for their
    program (30d rolling, domain-specific, etc.).
    """
    insights = _fetch_insights_from_threads(post_id)
    hours = max((datetime.now(timezone.utc) - published_at).total_seconds() / 3600, 1.0)
    vph = insights.views / hours

    stats = PostStats(
        post_id=post_id,
        current_vph=vph,
        author_avg_vph=author_avg_vph,
        author_std_vph=author_std_vph,
    )
    topic = TopicContext(topic=hashtag, saturation_index=hashtag_saturation)
    result = pipeline.score(stats, topic)
    return result.to_dict()


# ─────────────────────────────────────────────────────────────
# Demo — ranks 3 posts by explosion potential.
# Replace with your own use case (alerting, dashboard, feedback loop, etc.)
# ─────────────────────────────────────────────────────────────

def main() -> None:
    AUTHOR_AVG_VPH = 400.0
    AUTHOR_STD_VPH = 150.0
    published = datetime.now(timezone.utc) - timedelta(hours=12)

    candidates = [
        # (post_id,  hashtag,       hashtag_saturation)
        ("post_A",   "#ai",          0.85),  # red ocean hashtag
        ("post_B",   "#niche_hobby", 0.10),  # blue ocean
        ("post_C",   "#viral_news",  0.95),  # saturated, but genuinely exploding
    ]

    print(f"{'post_id':<10} {'flag':<8} {'final':>8} {'z':>6} {'mult':>5}  reason")
    print("-" * 72)

    ranked = []
    for post_id, tag, sat in candidates:
        result = score_live_post(
            post_id=post_id,
            published_at=published,
            author_avg_vph=AUTHOR_AVG_VPH,
            author_std_vph=AUTHOR_STD_VPH,
            hashtag=tag,
            hashtag_saturation=sat,
        )
        ranked.append((post_id, result, tag))
        reason = " / ".join(result["corrections_applied"]) or "-"
        print(
            f"{post_id:<10} {result['usability_flag']:<8} "
            f"{result['final_score']:>8.1f} "
            f"{result['post_burst_score']:>6.2f} "
            f"{result['red_ocean_multiplier']:>5.2f}  {reason}"
        )

    winners = [p for p, r, _ in ranked if r["usability_flag"] == "HIGH"]
    print(f"\nHIGH-flag posts (your program decides what to do): {winners}")
    print("  e.g., feed as positive examples, trigger alert, add to dashboard, etc.")


if __name__ == "__main__":
    main()
