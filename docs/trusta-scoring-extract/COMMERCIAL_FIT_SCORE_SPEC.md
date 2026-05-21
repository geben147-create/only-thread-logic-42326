# COMMERCIAL_FIT_SCORE_SPEC.md

> **목적**: TRUSTA Discovery에 `commercialFitScore` (광고/협업 적합도 점수)를 **신규 수식 0개로** 도입하기 위한 설계 사양서.
> **모드**: 설계 문서 / 코드 없음 / 마이그레이션 없음.
> **기준**: `only-thread-logic-42326`의 26개 수식 중 6개를 재조합.
> **출력 범위**: 0 ~ 100 (정수 권장).

---

## 1. commercialFitScore의 목적

광고주 또는 협업 제안자가 단 하나의 질문에 답하기 위한 점수:

> "이 Threads 계정 / 게시물에 광고나 협업을 맡길 만한가?"

`videoScore` (게시물이 잘 나갔는가) 와 `channelScore` (계정이 건강한가) 와는 **다른 의사결정 축**이다.
바이럴이라고 광고에 적합한 것도 아니고, 건강하다고 sponsor-safe인 것도 아니기 때문이다.

---

## 2. Threads에서 직접 광고 / RPM 점수를 만들면 안 되는 이유

| 데이터 | YouTube | Threads | 결과 |
|---|---|---|---|
| niche-specific RPM | ✅ AdSense | ❌ 없음 | revenue_estimate 계산 불가 |
| video monetization status | ✅ | ❌ 없음 | mid-roll eligibility 판단 불가 |
| watch time / retention | ✅ Analytics | ❌ 없음 | RPM × retention 가중 불가 |
| search volume | ✅ Keyword Planner | ❌ 없음 | opportunity_score의 vol 항 불가 |
| result_count | ✅ Search API | ❌ 없음 | competition 점수 불가 |
| creator earnings API | ✅ | ❌ 없음 | revenue projection 불가 |

→ **Kar-auto-OnlyLogic의 광고/ROI 6개 (E-2a, E-1b, E-2b, B-6, E-2c, E-3b) 수식 자체는 입력 변수부터 Threads에 존재하지 않는다.** 추정/가짜 데이터로 채우면 false-positive 폭증.

대안: **Threads가 실제로 측정 가능한 신호**(진성팔로워, 팔로워전환, 운영안정성, 외부링크도달, 참여율, 종합 신뢰)만 재조합 → `commercialFitScore`.

---

## 3. 기존 26개 로직 중 commercialFitScore 후보

| ID | 수식 | 광고주 관점 재해석 | 데이터 출처 (Threads API) |
|---|---|---|---|
| **CH-6** `audience_credibility` | "팔로워가 진짜인가? 가짜 인플루언서 거르기" | follower_demographics 일관성 + engagement_rate |
| **C-2b** `follower_conversion` | "광고 1회당 얼마나 팔로워가 늘어나는가" | followers_gained / views |
| **CH-7** `account_health_score` | "이 계정 전반적으로 sponsor-safe한가" | 7-indicator composite |
| **T-9** `link_attachment_penalty` (역수) | "외부 링크(스폰서 URL)가 도달율을 얼마나 잃는가" | link_attachment_url 존재 여부 |
| **CH-5** `posting_consistency` | "광고 일정 협의 후 납기 신뢰 가능한가" | post timestamp stdev |
| **B-4a** `engagement_rate` | "청중이 광고 콘텐츠에 반응할 가능성" | (likes + replies) / views |

---

## 4. 추천 가중치

| ID | 수식 | 가중치 | 근거 |
|---|---|---|---|
| CH-6 audience_credibility | **25%** | 진성 팔로워 = sponsor risk #1. NoxInfluencer 업계 표준. |
| C-2b follower_conversion | **20%** | 가장 직접적인 ROI 신호 (광고 1회 = 팔로워 X명). |
| CH-7 account_health_score | **20%** | 종합 신뢰. 이미 7-지표 가중합이라 다양성 확보. |
| T-9 link_attachment_penalty (역수) | **15%** | 광고는 외부링크가 본질. Meta의 -30% 페널티를 회피하는 계정/포맷이 유리. |
| CH-5 posting_consistency | **10%** | 광고 일정/캠페인 운영 신뢰성. |
| B-4a engagement_rate | **10%** | 청중 반응성. 다른 지표와 상관관계 높아 비중 낮춤. |
| **합계** | **100%** | |

> ⚠️ 이 가중치는 v0.1 초안이다. TRUSTA가 실 데이터로 backtest 후 `best_weights.json` 패턴(Kar-auto에서 차용)으로 튜닝하는 것이 다음 단계.

---

## 5. 계산식 초안

### 5.1 정규화 (모든 입력을 0-100 스케일로)

```
norm_credibility   = (audience_credibility == "REAL") ? 100 : 30
norm_conversion    = clamp(follower_conversion / 0.02 * 100, 0, 100)        // 2% = 100
norm_health        = account_health_score                                     // 이미 0-100
norm_link_inverse  = (link_attachment_url != null) ? 70 : 100                // T-9 역수 직관화
norm_consistency   = clamp(posting_consistency * 100, 0, 100)                // 0-1 → 0-100
norm_engagement    = clamp(engagement_rate / 0.05 * 100, 0, 100)             // 5% = 100
```

### 5.2 가중합

```
commercialFitScore =
    0.25 * norm_credibility
  + 0.20 * norm_conversion
  + 0.20 * norm_health
  + 0.15 * norm_link_inverse
  + 0.10 * norm_consistency
  + 0.10 * norm_engagement
```

### 5.3 출력 등급 (UI 표시용, 기존 thread-logic 등급체계 재사용)

| 점수 | 등급 | 색상 | 광고주 메시지 |
|---|---|---|---|
| 80-100 | Excellent | Green | 즉시 협업 추천 |
| 60-79 | Good | Light Green | 검토 후 협업 가능 |
| 40-59 | Average | Yellow | 보완 후 재검토 |
| 20-39 | Below Avg | Orange | 비추천 |
| 0-19 | Poor | Red | 거절 |

### 5.4 Edge cases / 가드

| 상황 | 동작 |
|---|---|
| `views <= 0` (신규 게시물) | engagement_rate, follower_conversion → 0 처리. `commercialFitScore`는 계산하되 `confidence: "low"` flag 부여. |
| `total_followers <= 0` | audience_credibility → "SUSPICIOUS" 강제, 전체 점수 보수적. |
| `posts_lifetime < 5` | posting_consistency 미정의, 0 처리 + `confidence: "low"` flag. |
| account_health_score 계산 불가 (CH-7 입력 부족) | 해당 컴포넌트 0 처리, 다른 5개로 가중합 재정규화 (가중치 합 = 0.80, 결과를 × 1.25). |

---

## 6. 저장 시 JSON metadata 예시

```json
{
  "scoring": {
    "version": "sotda-threads-v0.1.0",
    "scoredAt": "2026-05-21T12:34:56.789Z",
    "scoreType": ["video", "channel", "commercial"],
    "primaryCategory": "commercial",
    "scores": {
      "videoScore":         73.2,
      "channelScore":       85.1,
      "commercialFitScore": 62.4,
      "overallScore":       null
    },
    "breakdown": {
      "video": {
        "z_vph":                2.1,
        "engagement_rate":      0.042,
        "repost_rate":          0.018,
        "quote_rate":           0.011,
        "viral_velocity_24h":   8.3,
        "reply_ratio":          0.035,
        "threads_satisfaction": 68.2,
        "share_rate":           0.009,
        "quote_to_reply_ratio": 0.31,
        "red_ocean_multiplier": 1.22,
        "final_score_v1":       178.4
      },
      "channel": {
        "account_momentum":      1.14,
        "views_per_follower":    0.094,
        "outlier_ratio":         3.8,
        "content_efficiency":    12500,
        "posting_consistency":   0.81,
        "follower_conversion":   0.018,
        "account_health_score":  85.1,
        "audience_credibility":  "REAL",
        "growth_trigger":        false
      },
      "commercial": {
        "norm_credibility":  100,
        "norm_conversion":   90,
        "norm_health":       85.1,
        "norm_link_inverse": 100,
        "norm_consistency":  81,
        "norm_engagement":   84,
        "commercialFitScore": 62.4
      }
    },
    "flags": {
      "alertLevel":  "watch",
      "credibility": "REAL",
      "mediaType":   "CAROUSEL_ALBUM",
      "confidence":  "high"
    },
    "modifiers": {
      "red_ocean_multiplier":    1.22,
      "link_attachment_penalty": 1.0
    }
  }
}
```

### Storage 권장사항

- **JSONB 컬럼 1개에 위 구조 전체 저장 → migration 0개로 출시 가능**.
- 정렬/필터가 필요한 3개 score (`videoScore`, `channelScore`, `commercialFitScore`)는 데이터가 충분히 모이면 컬럼 승격 검토.
- `scoring.version` 필드 필수 → 수식 업데이트 시 재계산 트리거 키.

---

## 7. 명시적 비목표 (Non-Goals)

1. ❌ **광고 수익 추정 (revenue/USD prediction)** — Threads는 RPM 데이터를 제공하지 않음. 추정조차 시도하지 않음.
2. ❌ **competition 분석** — Threads search API는 result_count를 제공하지 않음.
3. ❌ **seasonal RPM adjustment** — Kar-auto의 Q4 1.3x는 RPM 종속이므로 채택하지 않음. (시즈널 트래픽 보정은 별도 modified_z 롤링 윈도우로 자연 흡수됨.)
4. ❌ **인플루언서 등급 절대 비교** — 도메인/언어/시장이 다른 계정 간 직접 비교는 norm 후에도 위험. 동일 niche 내 상대 순위만 권장.

---

## 8. 다음 단계 체크리스트 (TRUSTA Captain용)

- [ ] TRUSTA Discovery에 JSONB 컬럼이 이미 존재하는지 확인 (있으면 migration 0개)
- [ ] 위 §5 가중치를 v0.1 초안으로 박고, backtest 데이터 수집 시작
- [ ] `confidence: low` 케이스(신규 계정, 게시물 부족)의 UI 처리 정책 결정
- [ ] `overallScore: null` 유지 vs 가중합 노출 정책 결정 (사용자는 별도 보고 선호)
- [ ] thread-logic optimizer.py에 Kar-auto `best_weights.json` 튜닝 패턴 차용 여부 결정

---

*read-only 설계 사양 종료. 구현은 TRUSTA Captain의 권한.*
