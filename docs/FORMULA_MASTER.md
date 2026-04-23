# SOTDA Threads Formula Master — v0.1.0

> Threads Graph API v1.0 (2024) 기반 26개 수식
> = 공통 17 (YouTube ⇄ Threads rename only) + Threads 전용 9 (reposts/quotes/shares/media_type)

---

## Threads API 필드 매핑

| YouTube 필드 | Threads 필드 | 상태 | 비고 |
|---|---|---|---|
| views | views (Media Insights) | 동일 | — |
| likes | likes | 동일 | — |
| comments | **replies** | rename | 이름만 다름 |
| subscribers | **followers** | rename | 이름만 다름 |
| channel | **account / owner** | rename | 이름만 다름 |
| shares | shares | 동일 | Threads도 제공 |
| (없음) | **reposts** | Threads 고유 | 리트윗 유사 |
| (없음) | **quotes** | Threads 고유 | 인용 게시 |
| (없음) | **is_quote_post** | Threads 고유 | 인용 여부 플래그 |
| (없음) | **link_attachment_url** | Threads 고유 | 외부 링크 (Meta 알고리즘 페널티) |
| (없음) | **media_type** (TEXT/IMAGE/VIDEO/CAROUSEL) | Threads 고유 | 포맷 분기 |
| (없음) | **follower_demographics** | Threads 고유 | 국가/도시/연령/성별 |
| video_duration | ⚠️ VIDEO 한정, duration API 미제공 | 제한 | Shorts/Long 분기 불가 |
| watch_time | ❌ | **미제공** | retention/completion 계산 불가 |
| search_volume | ❌ | **미제공** | Threads 키워드 볼륨 API 없음 |
| niche_RPM | ❌ | **미제공** | Threads 크리에이터 수익 API 없음 |

---

## 🟢 공통 수식 (17개) — YouTube ⇄ Threads 동일 로직

**Rename 규칙**: `channel→author/account`, `subscribers→followers`, `comments→replies`, `video→post`.

### 1. 트렌드 감지 — 통계/도메인 무관 (3개)

| 순위 | 점수 | ID | 수식 | 직관 메모 | 공식 |
|------|------|-----|------|----------|------|
| 1 | 14 MUST | D-3b | **modified_z** | 바이럴 즉시 감지 지수 | `0.6745 * (x - median) / MAD` |
| 2 | 14 MUST | D-4a | **alert_level** | 트렌드 긴급도 등급 | `z>5=viral, >3.5=surge, >3=trending, >2=watch` |
| 3 | 13 MUST | D-2a | **surge_z** | 스파이크 감지 지수 | `(today - rolling_mean) / rolling_std` |

### 2. 게시물 분석 (5개)

| 순위 | 점수 | ID | 수식 | 직관 메모 | 공식 (Threads) |
|------|------|-----|------|----------|------|
| 1 | 14 MUST | A-1 | **z-VPH** | 계정 대비 조회 폭발 강도 | `(current_vph - author_avg_vph) / author_std_vph` |
| 2 | 14 MUST | A-3 | **final_score** | 게시물 종합 폭발 점수 | `z_vph * multiplier * 50 + 50` |
| 3 | 12 MUST | B-4a | **engagement_rate** | 게시물 참여율 | `(likes + replies) / views` |
| 4 | 12 MUST | C-1a | **like_ratio** | 조회 대비 좋아요 비율 | `likes / views` |
| 5 | 10 KEEP | A-2 | **red_ocean_multiplier** | 레드오션 경쟁 가속 계수 | `1 + min(topic_saturation * weight, cap - 1)` |

### 3. 계정 분석 (9개)

| 순위 | 점수 | ID | 수식 | 직관 메모 | 공식 (Threads) |
|------|------|-----|------|----------|------|
| 1 | 14 MUST | CH-1 | **account_momentum** | 계정 월간 가속도 | `(views_30d/prev) * (followers_30d/prev)` |
| 2 | 14 MUST | CH-2 | **views_per_follower** | 팔로워 대비 조회 비율 | `avg_views_90d / total_followers` |
| 3 | 14 MUST | CH-3 | **outlier_ratio** | 계정 평균 대비 돌파 배수 | `post_views / account_avg_views` |
| 4 | 14 MUST | CH-4 | **content_efficiency** | 게시물당 평균 조회수 | `views_30d / posts_30d` |
| 5 | 12 MUST | CH-5 | **posting_consistency** | 게시 간격 안정성 지수 | `1 / (1 + stdev(post_intervals_90d))` |
| 6 | 11 KEEP | CH-6 | **audience_credibility** | 팔로워 진성도 판별 등급 | `follower_rate >= 5% ? REAL : SUSPICIOUS` |
| 7 | 11 KEEP | C-2b | **follower_conversion** | 게시물당 팔로워 전환율 | `followers_gained / views` |
| 8 | 11 KEEP | CH-7 | **account_health_score** | 계정 종합 건강 점수 | 7-indicator weighted composite |
| 9 | 8 KEEP | D-4b | **growth_trigger** | 계정 급성장 트리거 신호 | `growth_7d > 200% → surge` |

#### CH-7 account_health_score 가중치

| 가중치 | 지표 | 직관 메모 | Threads API 소스 |
|--------|------|----------|------|
| **25%** | engagement_rate | 반응이 센 계정 | (likes + replies) / views |
| **15%** | posting_consistency | 꾸준함 = 알고리즘 신뢰 | post timestamp stdev |
| **15%** | views_per_follower | 팔로워가 살아있는가 | avg_views_90d / followers_count |
| **15%** | content_efficiency | 적게 올려도 터진다 | views_30d / posts_30d |
| **10%** | posting_frequency | 게시 빈도 | posts_30d |
| **10%** | follower_conversion | 팔로워 전환력 | followers_gained / views |
| **10%** | audience_credibility | 가짜 없는 진성 팔로워 | follower_demographics 일관성 |

---

## 🔵 Threads 전용 수식 (9개) — reposts / quotes / shares / media_type 활용

| 순위 | 점수 | ID | 수식 | 직관 메모 | 공식 |
|------|------|-----|------|----------|------|
| 1 | 14 MUST | T-1 | **repost_rate** | 리포스트 바이럴 증폭 비율 | `reposts / views` |
| 2 | 14 MUST | T-2 | **quote_rate** | 인용 유발 비율 | `quotes / views` |
| 3 | 13 MUST | T-3 | **viral_velocity_24h** | 초기 24시간 확산 속도 | `reposts / min(hours_since_post, 24)` |
| 4 | 12 MUST | T-4 | **reply_ratio** | 답글 유발 비율 | `replies / views` |
| 5 | 12 MUST | T-5 | **threads_satisfaction** | Threads 종합 만족 지수 | `0.35*reply_ratio_n + 0.30*repost_rate_n + 0.20*quote_rate_n + 0.15*follower_gain_n` |
| 6 | 11 KEEP | T-6 | **media_type_branch** | 포맷 분기 판별기 | `media_type in {TEXT_POST, IMAGE, VIDEO, CAROUSEL_ALBUM} → threshold 조정` |
| 7 | 10 KEEP | T-7 | **share_rate** | 외부 공유 비율 | `shares / views` |
| 8 | 10 KEEP | T-8 | **quote_to_reply_ratio** | 논쟁성 지수 | `quotes / replies` |
| 9 | 9 KEEP | T-9 | **link_attachment_penalty** | 외부 링크 도달 페널티 계수 | `link_attachment_url != null ? 0.7 : 1.0` |

### T-5 threads_satisfaction 가중치 (retention 미제공 대응)

| 가중치 | 지표 | 정규화 방식 | 근거 |
|--------|------|----------|------|
| **35%** | reply_ratio | `replies / views * 100 / 0.05` (5% 목표) | 대화 유발이 최고 신호 |
| **30%** | repost_rate | `reposts / views * 100 / 0.03` (3% 목표) | 자발적 확산 |
| **20%** | quote_rate | `quotes / views * 100 / 0.02` (2% 목표) | 2차 창작 유발 |
| **15%** | follower_gain | `(new_followers / views) / 0.01 * 100` | 계정 성장 기여 |

### T-6 media_type_branch 임계값

| media_type | high_threshold | low_threshold | 특성 |
|-----------|---------------|---------------|------|
| TEXT_POST | 180 | 70 | 1-6h에 대부분 결판, 빠른 decay |
| IMAGE | 200 | 75 | 중간, Instagram 교차 노출 |
| VIDEO | 220 | 80 | 느리게 자라지만 오래 감 |
| CAROUSEL_ALBUM | 210 | 78 | 저장 유도, 지속 노출 |

---

## 🔴 삭제된 수식 (17개, YouTube 원본 대비)

| 카테고리 | 삭제 ID | 이유 |
|---|---|---|
| watch_time 미제공 (3) | B-2a completion_rate, C-1b avg_view_pct, C-3a satisfaction_v1 | Threads Insights API가 watch_time/retention 미제공 |
| Shorts/duration 없음 (3) | B-1 is_short, B-3b shorts_vph, B-5 content_type_branch | Threads는 media_type 4종으로 구분 → T-6으로 대체 |
| 수익 API 없음 (3) | B-6 rpm_proxy, E-2b revenue_estimate, E-3b seasonal_adjust | Threads 크리에이터 수익 API 없음 |
| 키워드 볼륨 없음 (7) | E-1a search_volume, D-1a demand, D-1b supply, D-1c gap_score, E-1b competition, E-2a opportunity_score, E-2c rank_probability | Threads는 keyword_search(top/recent)만 제공, 볼륨 미제공 |
| NLP 외부 의존 (1) | C-2a comment_sentiment | Threads API는 감성 점수 미제공, 외부 NLP 파이프라인은 범위 밖 |

---

## 등급 체계

| 점수 | 등급 | 색상 |
|------|------|------|
| 80-100 | Excellent | Green |
| 60-79 | Good | Light Green |
| 40-59 | Average | Yellow |
| 20-39 | Below Avg | Orange |
| 0-19 | Poor | Red |

## 알림 등급

| Modified Z | 등급 | 색상 | 행동 |
|------------|------|------|------|
| > 5.0 | Viral | Red | 즉시 대응 |
| > 3.5 | Surge | Orange | 푸시 알림 |
| > 3.0 | Trending | Yellow | 인앱 알림 |
| > 2.0 | Watch | Blue | 모니터링 |

---

## Display 규칙

| 타입 | 변환 | 예시 |
|------|------|------|
| 비율 (0-1) | x100, X.X% | 0.042 → **4.2%** |
| 점수 (합산) | 정수 + 색상 + 등급 | 56 → **56 Average** |
| 대수 | K/M 축약 | 12400 → **12.4K** |
| z-score | 등급 매핑 | 4.2 → **Surge** |
| 속도 | X.X /h | 12.5 → **12.5 rp/h** |
