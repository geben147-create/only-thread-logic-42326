# only-thread-logic-42326 — SOTDA Threads v0.1.0

> **Threads Graph API 전용** 게시물 폭발 감지 스코어링 엔진.
> 26개 수식 (17 공통 rename + 9 Threads 전용) + 3-phase 파이프라인 + LLM 기반 가중치 자동 튜닝.

---

## 설치

```bash
# uv (권장)
uv pip install -e .

# pip
pip install -e ".[dev]"
```

Python 3.10+ 필요. 외부 의존성 0개 (pytest만 dev-deps).

---

## 60초 퀵스타트

```python
from sotda import ExplosionScoringPipeline, PostStats, TopicContext

pipeline = ExplosionScoringPipeline()

post = PostStats(
    post_id="threads_42",
    current_vph=500,         # Threads Media Insights views / hours_since_post
    author_avg_vph=100,      # 최근 author 게시물들의 평균 VPH
    author_std_vph=50,
)
topic = TopicContext(topic="#tech", saturation_index=0.3)

result = pipeline.score(post, topic)
print(result.to_dict())
# {'post_burst_score': 8.0, 'red_ocean_multiplier': 1.15, 'final_score': 510.0,
#  'usability_flag': 'HIGH', 'corrections_applied': []}
```

---

## 구조

```
only-thread-logic-42326/
├── README.md                  # 이 파일
├── program.md                 # LLM 에이전트 행동 강령 (karpathy 스타일)
├── pyproject.toml             # 설치 + 의존성
├── .gitignore
├── docs/
│   ├── FORMULA_MASTER.md      # 26개 수식 전체 (공통 17 + Threads 전용 9)
│   └── explosion_logic.md     # 3-phase 알고리즘 근거
├── sotda/                     # 메인 패키지
│   ├── __init__.py
│   ├── pipeline.py            # 3-phase (PostStats / TopicContext / ScoringResult)
│   ├── evaluator.py           # 6개 Threads 시나리오 TEST_BATTERY
│   ├── generator.py           # Claude CLI 기반 가중치 제안 LLM
│   └── optimizer.py           # 메인 루프 (dry-run 포함)
├── tests/
│   ├── conftest.py
│   ├── test_pipeline.py       # Phase 1/2/3 + 소규모 계정 보정
│   ├── test_evaluator.py      # TEST_BATTERY 스모크
│   └── test_formula_triage.py # 26 수식 정합성 + Threads API alignment
└── results.tsv                # 자동 누적 (cycle, fitness, status, 가중치, reasoning)
```

---

## Threads API 기반 설계

### 🟢 공통 17개 (YouTube → Threads rename만으로 동일 수식 사용)

`channel→author`, `subscribers→followers`, `comments→replies`, `video→post` 매핑만 수행:

- 트렌드 감지: `modified_z`, `alert_level`, `surge_z` (통계/도메인 무관)
- 게시물 분석: `z-VPH`, `final_score`, `engagement_rate`, `like_ratio`, `red_ocean_multiplier`
- 계정 분석: `account_momentum`, `views_per_follower`, `outlier_ratio`, `content_efficiency`, `posting_consistency`, `audience_credibility`, `follower_conversion`, `account_health_score`, `growth_trigger`

### 🔵 Threads 전용 9개 (Threads API 고유 필드 기반 신규)

- `repost_rate`, `quote_rate`, `viral_velocity_24h` (reposts/quotes 기반)
- `reply_ratio`, `share_rate`, `quote_to_reply_ratio`
- `threads_satisfaction` (retention 미제공 대응 재구성)
- `media_type_branch` (TEXT/IMAGE/VIDEO/CAROUSEL 포맷 분기)
- `link_attachment_penalty` (외부 링크 도달 페널티)

### 🔴 삭제 17개 (Threads API 미지원)

- watch_time 미제공 (3) — retention/completion 불가
- Shorts/duration 없음 (3) — media_type으로 대체
- 수익 API 없음 (3) — Threads 크리에이터 수익 API 없음
- 키워드 볼륨 없음 (7) — Threads는 keyword_search만 (볼륨 미제공)
- NLP 외부 의존 (1) — 범위 밖

상세: [`docs/FORMULA_MASTER.md`](docs/FORMULA_MASTER.md)

---

## 3-Phase Explosion Scoring

1. **Phase 1 (z-VPH)**: 계정 대비 상대 폭발 감지 + 소규모 계정 보정 (log1p + std floor)
2. **Phase 2 (Red Ocean)**: 해시태그/토픽 포화도 기반 승수
3. **Phase 3 (Output)**: `z * multiplier * 50 + 50` → HIGH/MEDIUM/LOW

상세: [`docs/explosion_logic.md`](docs/explosion_logic.md)

---

## LLM 기반 가중치 자동 튜닝 (autoresearch 스타일)

karpathy/autoresearch의 program.md 패턴을 적용:

```bash
# Dry-run (LLM 없이 현재 가중치 평가만)
python -m sotda.optimizer --dry-run --cycles 1

# 실제 LLM 최적화 (Claude CLI 필요)
python -m sotda.optimizer --cycles 5
```

자동으로 `results.tsv`에 누적:

```
cycle   fitness  status    min_vph_thr  std_floor  ocean_weight  ocean_cap  high_thr  low_thr  reasoning
0       83.33    baseline  50.0         5.0        0.5           1.5        200.0     75.0
1       100.00   keep      50.0         5.0        0.5           1.5        210.0     75.0     raised high_threshold by 10
```

튜닝 대상 (WeightConfig 6개):
- `min_vph_threshold` (10-200)
- `min_std_floor` (1-20)
- `red_ocean_weight` (0.1-2.0)
- `red_ocean_cap` (1.1-3.0)
- `high_threshold` (100-400)
- `low_threshold` (30-150)

---

## 테스트

```bash
pytest                 # 전체
pytest -v              # verbose
pytest tests/test_pipeline.py  # 파이프라인만
```

현재 커버리지:
- `test_pipeline.py` — Phase 1/2/3 + 소규모 계정 보정 + 출력 분리
- `test_evaluator.py` — TEST_BATTERY 스모크 + 기본 가중치 baseline fitness
- `test_formula_triage.py` — 26 수식 + Threads API alignment (reposts/quotes/replies 검증, watch_time/키워드볼륨/수익API 의존 수식 부재 확인)

---

## 참고

- **Threads Graph API v1.0**: https://developers.facebook.com/docs/threads
- **karpathy/autoresearch** (methodology 영감): https://github.com/karpathy/autoresearch
- **원본 YouTube 버전** (v4.2 34 formulas): 내부 프로젝트 Kar-auto-OnlyLogic

---

*v0.1.0 | Threads 전용 | 2026-04-23*
