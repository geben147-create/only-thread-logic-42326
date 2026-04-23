"""
Formula Triage — Threads 26 formulas (17 공통 rename + 9 Threads 전용).

Derived from SOTDA YouTube v4.2 (34 formulas) by mapping against
Threads Graph API v1.0 field inventory:
  - Media Insights: views, likes, replies, reposts, quotes, shares
  - Media Fields:   media_type (TEXT_POST/IMAGE/VIDEO/CAROUSEL_ALBUM),
                    is_quote_post, link_attachment_url, timestamp

Removed (17): watch_time-dependent (3), Shorts/duration (3),
              revenue API (3), keyword volume (7), external NLP (1).

Scoring: revenue(0-3) + growth(0-3) + speed(0-3) + data(0-3) + unique(0-3)
MUST (12+), KEEP (8-11).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FormulaScore:
    id: str
    name: str
    memo: str           # noun-ending Korean (tooltip)
    formula: str
    industry_ref: str
    category: str       # trend / post / account / threads_only
    origin: str         # common (YouTube ⇄ Threads) / threads_only
    revenue: int
    growth: int
    speed: int
    data: int
    unique: int

    @property
    def total(self) -> int:
        return self.revenue + self.growth + self.speed + self.data + self.unique

    @property
    def verdict(self) -> str:
        if self.total >= 12:
            return "MUST"
        elif self.total >= 8:
            return "KEEP"
        return "CUT"


ALL_FORMULAS: list[FormulaScore] = [
    # -- 🟢 공통 (17개): YouTube ⇄ Threads 동일 수식, 필드명만 rename --

    # 1. 트렌드 감지 (3개) — 통계학/도메인 무관
    FormulaScore("D-3b", "modified_z",
        "바이럴 즉시 감지 지수",
        "0.6745 * (x - median) / MAD",
        "통계학 MAD (도메인 무관)",
        "trend", "common",
        revenue=2, growth=3, speed=3, data=3, unique=3),  # 14
    FormulaScore("D-4a", "alert_level",
        "트렌드 긴급도 등급",
        "z>5=viral, >3.5=surge, >3=trending, >2=watch",
        "통계학 z-threshold (도메인 무관)",
        "trend", "common",
        revenue=2, growth=3, speed=3, data=3, unique=3),  # 14
    FormulaScore("D-2a", "surge_z",
        "스파이크 감지 지수",
        "(today - rolling_mean) / rolling_std",
        "Van Brakel smoothed z-score",
        "trend", "common",
        revenue=2, growth=3, speed=3, data=2, unique=3),  # 13

    # 2. 게시물 분석 (5개) — views/likes/replies 기반
    FormulaScore("A-1", "z-VPH",
        "계정 대비 조회 폭발 강도",
        "(current_vph - author_avg_vph) / author_std_vph",
        "Threads views + timestamp (VPH rolling window)",
        "post", "common",
        revenue=2, growth=3, speed=3, data=3, unique=3),  # 14
    FormulaScore("A-3", "final_score",
        "게시물 종합 폭발 점수",
        "z_vph * multiplier * 50 + 50",
        "자체 설계 (z*mult 정규화)",
        "post", "common",
        revenue=2, growth=3, speed=3, data=3, unique=3),  # 14
    FormulaScore("B-4a", "engagement_rate",
        "게시물 참여율",
        "(likes + replies) / views",
        "Threads Media Insights (likes + replies)",
        "post", "common",
        revenue=1, growth=3, speed=2, data=3, unique=3),  # 12
    FormulaScore("C-1a", "like_ratio",
        "조회 대비 좋아요 비율",
        "likes / views",
        "Threads Media Insights (likes, views)",
        "post", "common",
        revenue=1, growth=2, speed=3, data=3, unique=3),  # 12
    FormulaScore("A-2", "red_ocean_multiplier",
        "레드오션 경쟁 가속 계수",
        "1 + min(topic_saturation * weight, cap - 1)",
        "자체 설계 (해시태그/토픽 포화도 기반)",
        "post", "common",
        revenue=1, growth=2, speed=2, data=2, unique=3),  # 10

    # 3. 계정 분석 (9개) — follower/post 기반 (channel→account rename)
    FormulaScore("CH-1", "account_momentum",
        "계정 월간 가속도",
        "(views_30d / views_prev_30d) * (followers_30d / followers_prev_30d)",
        "Threads User Insights (views, followers_count)",
        "account", "common",
        revenue=2, growth=3, speed=3, data=3, unique=3),  # 14
    FormulaScore("CH-2", "views_per_follower",
        "팔로워 대비 조회 비율",
        "avg_views_90d / total_followers",
        "Threads User Insights (views, followers_count)",
        "account", "common",
        revenue=2, growth=3, speed=3, data=3, unique=3),  # 14
    FormulaScore("CH-3", "outlier_ratio",
        "계정 평균 대비 돌파 배수",
        "post_views / account_avg_views",
        "Threads Media Insights (views per post)",
        "account", "common",
        revenue=2, growth=3, speed=3, data=3, unique=3),  # 14
    FormulaScore("CH-4", "content_efficiency",
        "게시물당 평균 조회수",
        "views_30d / posts_published_30d",
        "Threads User Insights + media count",
        "account", "common",
        revenue=2, growth=3, speed=3, data=3, unique=3),  # 14
    FormulaScore("CH-5", "posting_consistency",
        "게시 간격 안정성 지수",
        "1 / (1 + stdev(post_intervals_90d))",
        "Threads Media timestamp stdev",
        "account", "common",
        revenue=1, growth=3, speed=2, data=3, unique=3),  # 12
    FormulaScore("CH-6", "audience_credibility",
        "팔로워 진성도 판별 등급",
        "follower_rate >= 5% ? REAL : SUSPICIOUS",
        "Threads follower_demographics + engagement cross-check",
        "account", "common",
        revenue=2, growth=1, speed=2, data=3, unique=3),  # 11
    FormulaScore("C-2b", "follower_conversion",
        "게시물당 팔로워 전환율",
        "followers_gained / views",
        "Threads User Insights (followers_count delta)",
        "account", "common",
        revenue=1, growth=3, speed=2, data=2, unique=3),  # 11
    FormulaScore("CH-7", "account_health_score",
        "계정 종합 건강 점수",
        "7-indicator weighted composite (engagement 25% top)",
        "자체 설계 (7개 지표 가중 합성)",
        "account", "common",
        revenue=2, growth=2, speed=2, data=2, unique=3),  # 11
    FormulaScore("D-4b", "growth_trigger",
        "계정 급성장 트리거 신호",
        "growth_7d > 200% -> surge alert",
        "Threads User Insights (followers 급등)",
        "account", "common",
        revenue=1, growth=2, speed=2, data=2, unique=1),  # 8

    # -- 🔵 Threads 전용 (9개): reposts / quotes / shares / media_type 활용 --

    FormulaScore("T-1", "repost_rate",
        "리포스트 바이럴 증폭 비율",
        "reposts / views",
        "Threads Media Insights (reposts) — YouTube 없음",
        "threads_only", "threads_only",
        revenue=2, growth=3, speed=3, data=3, unique=3),  # 14
    FormulaScore("T-2", "quote_rate",
        "인용 유발 비율",
        "quotes / views",
        "Threads Media Insights (quotes) — YouTube 없음",
        "threads_only", "threads_only",
        revenue=2, growth=3, speed=3, data=3, unique=3),  # 14
    FormulaScore("T-3", "viral_velocity_24h",
        "초기 24시간 확산 속도",
        "reposts / min(hours_since_post, 24)",
        "Threads Media Insights + timestamp — 24h decay",
        "threads_only", "threads_only",
        revenue=2, growth=3, speed=3, data=2, unique=3),  # 13
    FormulaScore("T-4", "reply_ratio",
        "답글 유발 비율",
        "replies / views",
        "Threads Media Insights (replies)",
        "threads_only", "threads_only",
        revenue=1, growth=3, speed=2, data=3, unique=3),  # 12
    FormulaScore("T-5", "threads_satisfaction",
        "Threads 종합 만족 지수",
        "0.35*reply_ratio_n + 0.30*repost_rate_n + 0.20*quote_rate_n + 0.15*follower_gain_n",
        "자체 설계 (retention 미제공 대응 재구성)",
        "threads_only", "threads_only",
        revenue=2, growth=3, speed=2, data=2, unique=3),  # 12
    FormulaScore("T-6", "media_type_branch",
        "포맷 분기 판별기",
        "media_type in {TEXT_POST, IMAGE, VIDEO, CAROUSEL_ALBUM} -> threshold 조정",
        "Threads Media Fields (media_type) — YouTube Shorts/Long 대체",
        "threads_only", "threads_only",
        revenue=1, growth=2, speed=3, data=2, unique=3),  # 11
    FormulaScore("T-7", "share_rate",
        "외부 공유 비율",
        "shares / views",
        "Threads Media Insights (shares)",
        "threads_only", "threads_only",
        revenue=1, growth=2, speed=2, data=2, unique=3),  # 10
    FormulaScore("T-8", "quote_to_reply_ratio",
        "논쟁성 지수",
        "quotes / replies",
        "Threads 고유 (quotes vs replies 비율)",
        "threads_only", "threads_only",
        revenue=1, growth=2, speed=2, data=2, unique=3),  # 10
    FormulaScore("T-9", "link_attachment_penalty",
        "외부 링크 도달 페널티 계수",
        "link_attachment_url != null ? 0.7 : 1.0",
        "Meta 알고리즘 (외부 링크 도달 억제)",
        "threads_only", "threads_only",
        revenue=1, growth=2, speed=1, data=2, unique=3),  # 9
]


# ======================================================
# Tests
# ======================================================

class TestFormulaCount:
    def test_exactly_26(self):
        assert len(ALL_FORMULAS) == 26

    def test_common_17(self):
        common = [f for f in ALL_FORMULAS if f.origin == "common"]
        assert len(common) == 17

    def test_threads_only_9(self):
        threads_only = [f for f in ALL_FORMULAS if f.origin == "threads_only"]
        assert len(threads_only) == 9

    def test_no_cut(self):
        bad = [f for f in ALL_FORMULAS if f.verdict == "CUT"]
        assert len(bad) == 0, f"Unexpected CUT formulas: {[f.id for f in bad]}"


class TestScoreIntegrity:
    def test_all_scores_0_to_3(self):
        for f in ALL_FORMULAS:
            for attr in ["revenue", "growth", "speed", "data", "unique"]:
                val = getattr(f, attr)
                assert 0 <= val <= 3, f"{f.id}.{attr}={val}"

    def test_total_equals_sum(self):
        for f in ALL_FORMULAS:
            assert f.total == f.revenue + f.growth + f.speed + f.data + f.unique

    def test_no_duplicate_ids(self):
        ids = [f.id for f in ALL_FORMULAS]
        assert len(ids) == len(set(ids))


class TestCategoryDistribution:
    def test_trend_3(self):
        assert len([f for f in ALL_FORMULAS if f.category == "trend"]) == 3

    def test_post_5(self):
        assert len([f for f in ALL_FORMULAS if f.category == "post"]) == 5

    def test_account_9(self):
        assert len([f for f in ALL_FORMULAS if f.category == "account"]) == 9

    def test_threads_only_category_9(self):
        assert len([f for f in ALL_FORMULAS if f.category == "threads_only"]) == 9


class TestThreadsAPIAlignment:
    """Threads Graph API 실제 제공 필드 검증."""

    def test_engagement_uses_replies_not_comments(self):
        """Threads: replies (YouTube: comments)."""
        er = [f for f in ALL_FORMULAS if f.id == "B-4a"][0]
        assert "replies" in er.formula
        assert "comments" not in er.formula.lower()

    def test_follower_not_subscriber(self):
        vpf = [f for f in ALL_FORMULAS if f.id == "CH-2"][0]
        assert "follower" in vpf.formula.lower()
        assert "subscriber" not in vpf.formula.lower()

    def test_author_not_channel(self):
        zvph = [f for f in ALL_FORMULAS if f.id == "A-1"][0]
        assert "author" in zvph.formula.lower()

    def test_repost_rate_threads_only(self):
        rp = [f for f in ALL_FORMULAS if f.id == "T-1"][0]
        assert rp.origin == "threads_only"
        assert "reposts" in rp.formula

    def test_quote_rate_threads_only(self):
        qr = [f for f in ALL_FORMULAS if f.id == "T-2"][0]
        assert qr.origin == "threads_only"
        assert "quotes" in qr.formula

    def test_media_type_replaces_is_short(self):
        mt = [f for f in ALL_FORMULAS if f.id == "T-6"][0]
        assert "media_type" in mt.formula
        assert "TEXT_POST" in mt.formula
        assert "CAROUSEL_ALBUM" in mt.formula

    def test_viral_velocity_24h_not_48h(self):
        vv = [f for f in ALL_FORMULAS if f.id == "T-3"][0]
        assert "24" in vv.formula

    def test_no_watch_time_dependent_formulas(self):
        removed_ids = {"B-2a", "C-1b", "C-3a"}
        current_ids = {f.id for f in ALL_FORMULAS}
        assert not (removed_ids & current_ids), \
            f"watch_time 의존 수식이 남아있음: {removed_ids & current_ids}"

    def test_no_keyword_volume_dependent_formulas(self):
        removed_ids = {"E-1a", "D-1a", "D-1b", "D-1c", "E-1b", "E-2a", "E-2c"}
        current_ids = {f.id for f in ALL_FORMULAS}
        assert not (removed_ids & current_ids), \
            f"키워드 볼륨 의존 수식이 남아있음: {removed_ids & current_ids}"

    def test_no_revenue_api_dependent_formulas(self):
        removed_ids = {"B-6", "E-2b", "E-3b"}
        current_ids = {f.id for f in ALL_FORMULAS}
        assert not (removed_ids & current_ids), \
            f"수익 API 의존 수식이 남아있음: {removed_ids & current_ids}"

    def test_no_youtube_shorts_formulas(self):
        removed_ids = {"B-1", "B-3b", "B-5"}
        current_ids = {f.id for f in ALL_FORMULAS}
        assert not (removed_ids & current_ids), \
            f"YouTube Shorts 수식이 남아있음: {removed_ids & current_ids}"


class TestMemoFormat:
    """모든 메모가 명사형(~지수, ~점수, ~비율 등)으로 끝나는지."""

    NOUN_ENDINGS = [
        "지수", "점수", "비율", "등급", "계수", "강도",
        "속도", "가속도", "배수", "조회수",
        "플래그", "판별기", "신호",
        "참여율", "전환율",
    ]

    def test_all_memos_noun_ending(self):
        for f in ALL_FORMULAS:
            has_noun = any(f.memo.endswith(n) for n in self.NOUN_ENDINGS)
            assert has_noun, (
                f"{f.id} memo '{f.memo}' does not end with a noun form. "
                f"Expected endings: {self.NOUN_ENDINGS}"
            )


class TestDevelopmentPriority:
    def test_top_tier_threads_native_present(self):
        top = [f for f in ALL_FORMULAS if f.total == 14]
        ids = {f.id for f in top}
        assert "T-1" in ids  # repost_rate
        assert "T-2" in ids  # quote_rate

    def test_common_must_migrated(self):
        ids = {f.id for f in ALL_FORMULAS}
        assert "A-1" in ids
        assert "A-3" in ids
        assert "CH-1" in ids
        assert "CH-3" in ids
