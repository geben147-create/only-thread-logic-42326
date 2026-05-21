# BLOCKED_YOUTUBE_LOGICS.md

> **목적**: Kar-auto-OnlyLogic 및 test_logic20_30_only에서 TRUSTA Threads Discovery로 **이식하면 안 되는 로직**의 종합 차단 목록.
> **모드**: 차단 사양서. 미래 Captain이 "광고 점수 만들자" 충동에 빠질 때 참조.
> **근거**: thread-logic FORMULA_MASTER.md `🔴 삭제된 17개 섹션` + Threads Graph API v1.0 (2024) 명세.

---

## 1. Threads에서 누락된 데이터 → 차단 사유 매핑

| 사유 코드 | 누락 데이터 | YouTube 제공 | Threads 제공 |
|---|---|---|---|
| **NO_RPM** | niche-specific RPM | ✅ AdSense | ❌ |
| **NO_REVENUE** | creator earnings API | ✅ Analytics | ❌ |
| **NO_SEARCH_VOL** | keyword search volume | ✅ Keyword Planner | ❌ |
| **NO_RESULT_COUNT** | search result count | ✅ Search API | ❌ |
| **NO_WATCH_TIME** | watch_time / avg_view_duration | ✅ Analytics | ❌ |
| **NO_DURATION** | video duration | ✅ | ⚠️ VIDEO 한정, API 미제공 |
| **NO_COMPLETION** | completion_rate | ✅ | ❌ |
| **NO_NLP** | comment sentiment | (외부 NLP 필요) | (외부 NLP 필요) |

---

## 2. Kar-auto-OnlyLogic 차단 목록 (광고/ROI 6개 + 관련)

| 로직명 | repo | 원래 목적 | 금지 이유 | 대체 가능한 Threads 로직 |
|---|---|---|---|---|
| `opportunity_score` (E-2a) | Kar-auto | 적게 올려도 터지는 키워드 발견 | `vol`, `rpm`, `gap` 입력 자체 부재 (NO_SEARCH_VOL + NO_RPM) | **구조 패턴**만 차용 → commercialFitScore의 weighted-sum 골격 |
| `competition` (E-1b) | Kar-auto | 상위 경쟁자 강도 | `result_count` 미제공 (NO_RESULT_COUNT) | 없음 (Threads는 키워드 검색 결과 카운트 X) |
| `revenue_estimate` (E-2b) | Kar-auto | 월 예상 수익 ($420/mo) | `niche_RPM` 자체 부재 (NO_RPM + NO_REVENUE) | 없음 — `commercialFitScore`로 의사결정 대체 |
| `RPM Proxy` (B-6) | Kar-auto | 금융×미국×12월 = 3배 | AdSense 종속 룩업 (NO_RPM) | 없음 |
| `rank_probability` (E-2c) | Kar-auto | 하꼬도 상위노출 확률 | `competition` 연쇄 의존 (NO_RESULT_COUNT) | 없음 |
| `seasonal_adjust` (E-3b) | Kar-auto | Q4=1.3x, Q1=0.85x 광고비 | RPM 의존 → 시즈널 RPM 보정용 (NO_RPM) | `modified_z`의 롤링 윈도우가 시즈널 트래픽 변동을 자연 흡수 |

---

## 3. test_logic20_30_only 차단 목록 (YouTube 33개 중 Threads 불가)

| 로직명 | repo | 원래 목적 | 금지 이유 | 대체 가능한 Threads 로직 |
|---|---|---|---|---|
| `RPM Proxy` (#9) | test_logic | 영상별 RPM 추정 | NO_RPM | 없음 |
| `Mid-Roll Eligible` (#16) | test_logic | 8분 이상 중간광고 가능 | NO_DURATION | 없음 |
| `Shorts Flag` (#17) | test_logic | 60초 이하 Shorts 판별 | NO_DURATION → T-6 media_type_branch가 TEXT/IMAGE/VIDEO/CAROUSEL로 대체 | T-6 `media_type_branch` |
| `Monetization Eligibility Proxy` (#21) | test_logic | 수익화 가능 여부 | NO_REVENUE | 없음 |
| `Hot Video Rule` (#10) | test_logic | 상위 3-10% 핫영상 플래그 | views/threshold 자체는 가능하나, "Hot"의 정의가 niche_RPM 기반 | `modified_z > 5.0` (viral) flag로 대체 |
| `Title Keyword Match` (#11) | test_logic | 검색 의도 매칭 | search volume 부재 (NO_SEARCH_VOL) | 없음 (직접 Threads keyword_search top/recent로만 보조 가능) |
| `Description Completeness` (#12) | test_logic | 설명 길이/링크 수 점수 | Threads는 본문 1글 단위, 분리된 description 필드 없음 | 없음 |
| `Tag Optimization` (#13) | test_logic | 태그 개수×다양성 | Threads는 hashtag 한정 | 부분: hashtag_count 기반 별도 수식 필요 (현재 없음) |
| `Metadata Completeness` (#14) | test_logic | 제목+설명+태그 종합 | 위 3개 종합 의존 | 없음 |
| `Title Length Score` (#15) | test_logic | 제목 글자수 최적화 | YouTube SEO 종속 | 없음 |
| `Channel Velocity` (#22) | test_logic | 30일 총 조회/일 | views_30d / posts_30d로 측정 가능 | `content_efficiency` (CH-4) |
| `Channel Revenue Velocity` (#26) | test_logic | channel_velocity × RPM / 1000 | NO_RPM | 없음 |
| `High-RPM Video Ratio` (#27) | test_logic | RPM 상위 영상 비율 | NO_RPM | 없음 |
| `Upload Efficiency Index` (#28) | test_logic | velocity / uploads_per_month | 일부 가능 (posts_30d로 대체) | `content_efficiency` (CH-4) |
| `FINAL_SCORE` (#33) | test_logic | (video×0.7 + channel×0.3) × red_ocean | TRUSTA 사용자 의도: overallScore 단일 합산 비중점 (사용자 §3) | 채택 안 함 — 3개 score 별도 노출 |
| `VIDEO_DECISION_FLAG` | test_logic | YT용 4단계 분류 | YouTube niche threshold 종속 | `alert_level` (D-4a) |
| `usage_candidate` | test_logic | 우리가 찍어볼 만한 주제 | benchmarking 의도, Threads는 imitability 모델 다름 | T-6 media_type_branch + audience_credibility로 보조 가능 |

---

## 4. 공통 차단 (3개 repo 어디서 오든 차단)

| 패턴 | 차단 이유 | 대체 |
|---|---|---|
| `* / niche_RPM` 또는 `niche_RPM * *` | NO_RPM | (없음 — `commercialFitScore`로 의사결정 대체) |
| `* * search_volume *` | NO_SEARCH_VOL | (없음) |
| `* * result_count *` | NO_RESULT_COUNT | (없음) |
| `watch_time / *` 또는 `completion_rate` | NO_WATCH_TIME / NO_COMPLETION | `threads_satisfaction` (T-5) — retention 대체 합성 |
| `video_duration` 기반 분기 | NO_DURATION | `media_type_branch` (T-6) — TEXT/IMAGE/VIDEO/CAROUSEL |
| `comment_sentiment` 직접 호출 | 외부 NLP 의존 (범위 밖) | (없음) |
| `is_short` / `shorts_*` | NO_DURATION 연쇄 | `media_type_branch` (T-6) |
| 외부 키워드 갭 분석 (`gap_score`) | NO_SEARCH_VOL | (없음) |

---

## 5. 차단 위반 감지 가이드

TRUSTA 코드에 다음이 등장하면 **즉시 review 필요** (Threads 컨텍스트에서):

- `rpm`, `RPM`, `cpm`, `CPM`, `niche_rpm`, `niche_RPM`
- `revenue`, `earnings`, `monetization`
- `search_volume`, `keyword_volume`, `kw_vol`
- `result_count`, `competition_score` (단, `red_ocean_multiplier`는 OK — 토픽 saturation은 외부 데이터 아님)
- `watch_time`, `completion_rate`, `avg_view_duration`, `retention`
- `video_duration`, `is_short`, `shorts_flag`, `mid_roll_eligible`
- `comment_sentiment`, `sentiment_score`

→ 이 키워드들이 Threads 스코어링 코드에 나타나면 **차단 위반**.

---

## 6. 차단된 로직을 우회하려는 시도에 대한 가이드

| 우회 시도 | 평가 |
|---|---|
| "추정 RPM 룩업 테이블 직접 만들기" | ❌ 금지. False-positive 폭증, 광고주 신뢰 손실. |
| "외부 API(예: SimilarWeb)로 search volume 가져오기" | ⚠️ 범위 외. 별도 ADR 필요. 현재 스코어링 범위에서 제외. |
| "comment 텍스트로 sentiment 추정" | ⚠️ NLP 파이프라인은 SCORING 범위 외. 별도 ADR 필요. |
| "duration이 없으니 본문 글자수로 대체" | ⚠️ Threads media_type_branch (T-6)가 이미 분기 제공. 추가 변수 불필요. |
| "revenue 못 구하니 followers × 0.001로 추정" | ❌ 금지. 가짜 단위 환산은 신뢰도 0. |

---

## 7. 차단 룰의 미래 해제 조건

이 차단 목록은 **Threads API가 해당 데이터를 제공하기 시작하면** 항목별 재검토 가능:

- Threads가 `niche_RPM` 또는 `creator_earnings` API를 제공하기 시작 → §2의 광고/ROI 수식 재검토
- Threads가 `result_count`를 제공하기 시작 → competition / rank_probability 재검토
- Threads가 `watch_time` 또는 `completion_rate`를 제공하기 시작 → satisfaction 보강

재검토 시 반드시:
1. thread-logic SPEC.md + golden_vectors.json 동시 갱신
2. 본 문서 (BLOCKED_YOUTUBE_LOGICS.md)의 해당 항목 이력 추가
3. TRUSTA Discovery에 `scoring.version` bump 후 재계산 트리거

---

*read-only 차단 사양 종료. 차단 룰의 해제는 Threads API 명세 변경이 선행 조건.*
