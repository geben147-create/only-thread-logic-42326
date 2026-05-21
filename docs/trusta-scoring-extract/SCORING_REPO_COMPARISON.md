# SCORING_REPO_COMPARISON.md

> **목적**: TRUSTA / LEXlogicThread Discovery 엔진에 어떤 scoring repo를 어느 정도까지 차용할지 결정하기 위한 read-only 비교 보고서.
> **모드**: 분석 전용. 원본 repo 코드는 한 줄도 수정하지 않음.
> **생성일**: 2026-05-21
> **기준 repo**: `geben147-create/only-thread-logic-42326` (canonical)

---

## 1. 3개 repo 한눈에 비교표

| 항목 | only-thread-logic-42326 | Kar-auto-OnlyLogic | test_logic20_30_only |
|---|---|---|---|
| **플랫폼** | Threads (Meta) | YouTube | YouTube |
| **마지막 푸시** | 2026-05-17 (가장 최신) | 2026-04-11 | 2026-04-04 |
| **수식 개수** | **26개** (공통 17 + Threads 9) | **34개** (트렌드 7 + 영상 12 + 채널 9 + 광고/ROI 6) | **33개** (Video 21 + Channel 8 + Composite 4) |
| **파일 수 / 용량** | 33 / 92KB | 43 / 723KB | 166 / 413KB |
| **주 언어** | Python + TypeScript (이중 구현) | Python + Jupyter Notebook | Python + TS + JS |
| **광고/ROI 카테고리** | ❌ 없음 (Threads API 한계로 의도적 삭제) | ✅ 있음 (6개) | ❌ 없음 (Monetization은 영상에 흡수) |
| **3축 분리 (video/channel/X)** | post / account 2축 | 트렌드 / 영상 / 채널 / 광고 4축 | Video / Channel / Composite 3층 |
| **수익 의존 수식** | 0개 | RPM, revenue_estimate, seasonal_RPM | RPM Proxy, rev_velocity |
| **튜닝 환경** | optimizer.py (LLM-driven weight tuning) | train.py + orchestrator.py + best_weights.json (5회 반복 학습 로그) | (없음) |
| **테스트 인프라** | 4개 테스트 (evaluator/formulas/pipeline/triage) + golden_vectors.json (1e-9 교차검증) | 2개 (dummy data, formula triage) | 다수 (yt-scoring-api 내부) |
| **언어 무관 SPEC** | ✅ SPEC.md ("math is the contract") | ✅ SOTDA_DESIGN_PRD.md | ❌ (코드 종속) |
| **문서 품질** | ⭐⭐⭐⭐⭐ FORMULA_MASTER + SPEC + INTEGRATION + MULTI_SNS + AUDIT + explosion_logic | ⭐⭐⭐⭐ FORMULA_MASTER + PRD + scoring_rules_explosion | ⭐⭐⭐ .planning 방대 (9 phase) 하지만 산만 |
| **TRUSTA 적합도** | ★★★★★ 그대로 기준 | ★★★ 구조 패턴만 차용 | ★ 보조 참고 |

---

## 2. Repo별 역할 정의

### 🥇 only-thread-logic-42326 — **TRUSTA Canonical Math**
- TRUSTA Discovery의 **Threads 26개 수식 정본**.
- Python (`sotda/`) ↔ TypeScript (`typescript/src/`) 양쪽이 `golden_vectors.json` 1e-9 톨러런스로 교차검증됨.
- SPEC.md가 언어 무관 계약으로 작동 → Rust, Go, Java 등 어디서든 재구현 가능.
- **건드리지 말 것**. 모든 변경은 SPEC + golden_vectors 동시 갱신을 거쳐야 함.

### 🥈 Kar-auto-OnlyLogic — **Ad/ROI 구조 패턴 참고**
- YouTube 기반 34개 수식. 광고/인플루언서 ROI 6개가 **카테고리로 분리**되어 있음 → 구조 패턴 좋음.
- `best_weights.json`의 LLM 가중치 반복 튜닝 워크플로우는 TRUSTA optimizer.py 패턴 참고용.
- **수식 자체는 RPM/revenue 의존 → Threads에 직접 이식 금지**.
- 차용 대상: ① 4축 분리 사고법, ② weighted-sum composite 골격, ③ Q4 시즈널 계수 개념(RPM 분리).

### 🥉 test_logic20_30_only — **보조 비교용**
- YouTube 33개 + supabase migration 샘플 + yt-scoring-api FastAPI 풀스택.
- `.planning/` 166파일은 보일러플레이트 과다.
- 차용 가치: ① niche-specific min-max 정규화 패턴 (`NICHE_RANGES`), ② FastAPI 라우터 구조 (필요시).
- **수식은 거의 전부 YouTube 종속 → 이식 금지**.

---

## 3. TRUSTA에 쓸 것 vs 쓰지 말 것

### ✅ 그대로 사용 (only-thread-logic-42326 26개 전체)

```
공통 17개 (YouTube ⇄ Threads rename only):
  Trend       : modified_z, alert_level, surge_z
  Post        : z_vph, red_ocean_multiplier, final_score_v1, engagement_rate, like_ratio
  Account     : account_momentum, views_per_follower, outlier_ratio, content_efficiency,
                posting_consistency, audience_credibility, follower_conversion,
                account_health_score, growth_trigger

Threads 전용 9개:
  repost_rate, quote_rate, viral_velocity_24h, reply_ratio, threads_satisfaction,
  media_type_branch, share_rate, quote_to_reply_ratio, link_attachment_penalty
```

### 🟡 구조 패턴만 차용 (Kar-auto-OnlyLogic)

- 4축 분리 사고법 (트렌드 / 영상 / 채널 / 광고)
- `opportunity_score = w1*A + w2*B + ... ` 형태의 weighted-sum composite 골격
- `best_weights.json` 반복 튜닝 + reasoning 로그 패턴
- Q4 시즈널 가속 개념 (단, RPM 의존 부분은 제외)

### 🟡 패턴만 참고 (test_logic20_30_only)

- niche별 min-max 정규화 (`NICHE_RANGES[niche]["er"] = (0, 15)`)
- FastAPI 라우터 분리 (`api/v1/scoring.py`, `discover.py`)

### 🚫 절대 이식 금지 (`BLOCKED_YOUTUBE_LOGICS.md` 참조)

- 모든 RPM/revenue/watch_time/search_volume/result_count 의존 수식
- YouTube duration/Shorts 분기 (T-6 media_type_branch로 대체 완료)
- comment_sentiment (외부 NLP 의존)

---

## 4. 최종 추천

> **"thread-logic 26 = canonical math, commercialFitScore = 기존 6개 재조합, Kar-auto/test_logic은 구조 패턴만 추출"**

1. **수학 레이어**는 `only-thread-logic-42326`을 깨지 말 것. SPEC.md + golden_vectors.json이 계약.
2. **commercialFitScore는 신규 수식 0개**. 기존 26개 중 `audience_credibility / follower_conversion / account_health_score / link_attachment_penalty(역수) / posting_consistency / engagement_rate` 6개를 weighted-sum으로 재조합.
3. **광고 수익 추정 (RPM, revenue) 금지**. Threads API가 데이터를 제공하지 않음. 이를 시도하는 모든 수식은 차단.
4. **튜닝 워크플로우는 Kar-auto의 `best_weights.json` 패턴을 thread-logic optimizer.py로 가져올 수 있음** (선택사항).
5. **저장 시 분류 메타데이터**: `scoreType: ["video", "channel", "commercial"]` + `primaryCategory` 단일 enum.
6. **DB migration은 0개 가능** (JSONB 컬럼이 있으면). 데이터 규모가 커질 때만 컬럼 승격 (별도 문서 §8 참조).

---

## 5. 다음 단계 산출물

이 번들에 포함된 다른 4개 파일:

| 파일 | 역할 |
|---|---|
| `TRUSTA_SCORING_TAXONOMY_MAP.json` | 26개 로직의 trusta_category / score_type / use_in_* 매핑 |
| `COMMERCIAL_FIT_SCORE_SPEC.md` | commercialFitScore 가중치 + 계산식 + JSON metadata 예시 |
| `BLOCKED_YOUTUBE_LOGICS.md` | YouTube 기반 차단 로직 목록 + 차단 이유 + Threads 대체 |
| `IMPORT_README_FOR_TRUSTA.md` | TRUSTA repo에 어디 넣을지 + 다음 Captain 프롬프트 + 확인 질문 5개 |

---

*read-only Captain 보고서 종료. 코드/migration/commit 일체 없음.*
