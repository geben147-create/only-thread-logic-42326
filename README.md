# only-thread-logic-42326 - SOTDA Threads v0.3.0

Threads Graph API 게시물의 확산 가능성(viral/surge)을 점수화하는 순수 로직 라이브러리입니다.

이 저장소에는 토큰, API 호출, 데이터 수집 코드가 없습니다. 어떤 애플리케이션에서든 Threads 데이터를 직접 수집한 뒤 `sotda`에 넘기면 26개 공식과 3-phase 파이프라인으로 점수를 계산할 수 있습니다.

## 핵심 특징

- Threads 전용 공식 9개와 공통 확산 공식 17개, 총 26개 공식 제공
- `PostStats` 입력에서 `ScoringResult` 출력까지 이어지는 3-phase 파이프라인 제공
- Python 패키지와 TypeScript 포트 포함
- `golden_vectors.json`으로 언어 간 계산 결과 검증 가능
- 외부 런타임 의존성 없음

## 빠른 사용

```python
from sotda import ExplosionScoringPipeline, PostStats, TopicContext

pipeline = ExplosionScoringPipeline()

result = pipeline.score(
    PostStats(
        post_id="threads_42",
        current_vph=500,
        author_avg_vph=120,
        author_std_vph=45,
    ),
    TopicContext(topic="#ai", saturation_index=0.8),
)

print(result.to_dict())
# {
#   "post_burst_score": 8.44,
#   "red_ocean_multiplier": 1.4,
#   "final_score": 640.78,
#   "usability_flag": "HIGH",
#   "corrections_applied": []
# }
```

`usability_flag`는 `HIGH`, `MEDIUM`, `LOW` 중 하나입니다. 이 값은 알림, 대시보드 우선순위, 생성 모델의 positive example 선별 등에 바로 연결할 수 있습니다.

## 개별 공식 사용

```python
from sotda import formulas as f

# Threads 전용
f.repost_rate(reposts=110, views=12_500)       # 0.0088
f.quote_rate(quotes=30, views=12_500)          # 0.0024
f.viral_velocity_24h(reposts=110, hours_since_post=12)
f.reply_ratio(replies=55, views=12_500)
f.share_rate(shares=18, views=12_500)
f.quote_to_reply_ratio(quotes=30, replies=55)
f.threads_satisfaction(0.05, 0.03, 0.02, 0.01)
f.media_type_branch("VIDEO")                   # (220.0, 80.0)
f.link_attachment_penalty("https://example.com")

# 공통 확산/계정 분석
f.engagement_rate(likes=420, replies=55, views=12_500)
f.like_ratio(likes=420, views=12_500)
f.modified_z(1_000_000, [900, 1000, 1200, 1500])
f.alert_level(z_score=5.5)                     # "viral"
f.account_momentum(200_000, 100_000, 1500, 1000)
f.outlier_ratio(50_000, 10_000)
f.audience_credibility(0.06)                   # "REAL"
```

## 설치

```bash
pip install git+https://github.com/geben147-create/only-thread-logic-42326.git
```

로컬 개발:

```bash
git clone https://github.com/geben147-create/only-thread-logic-42326.git
cd only-thread-logic-42326
pip install -e ".[dev]"
pytest
```

## 3-Phase 파이프라인

1. **Phase 1: z-VPH**
   - 현재 VPH가 작성자 평소 VPH 대비 얼마나 튀는지 계산합니다.
   - `(current_vph - author_avg_vph) / author_std_vph`
   - 작은 계정의 과도한 z-score를 막기 위해 `std_floor`와 `log1p` 보정을 적용합니다.

2. **Phase 2: Red Ocean Multiplier**
   - 포화된 주제에서 터진 게시물은 수요가 검증된 신호로 보고 가중치를 줍니다.
   - `1 + min(saturation_index * weight, cap - 1)`

3. **Phase 3: Output**
   - `final_score = z * multiplier * 50 + 50`
   - 최종적으로 `HIGH`, `MEDIUM`, `LOW` 플래그를 반환합니다.

자세한 설명은 [docs/explosion_logic.md](docs/explosion_logic.md)를 참고하세요.

## Threads API 기반 공식 구성

- **공통 17개**: YouTube/X/Threads에 공통으로 적용 가능한 확산, 계정, 이상치 분석 공식
- **Threads 전용 9개**: `reposts`, `quotes`, `shares`, `media_type`, `link_attachment_url` 기반 공식
- **제외된 공식**: Threads API가 제공하지 않는 watch time, retention, Shorts duration, revenue, keyword volume 기반 공식

전체 공식 목록은 [docs/FORMULA_MASTER.md](docs/FORMULA_MASTER.md)에 정리되어 있습니다.

## 프로젝트 구조

```text
only-thread-logic-42326/
├── README.md
├── INTEGRATION.md
├── MULTI_SNS_INTEGRATION.md
├── SPEC.md
├── golden_vectors.json
├── sotda/
│   ├── formulas.py
│   ├── pipeline.py
│   ├── evaluator.py
│   ├── generator.py
│   └── optimizer.py
├── tests/
├── docs/
├── examples/
└── typescript/
```

`sotda/pipeline.py`가 일반적인 통합 진입점입니다. `evaluator.py`, `generator.py`, `optimizer.py`는 선택적인 weight tuning/autoresearch 도구입니다.

## 검증

```bash
pytest
node --experimental-strip-types typescript/test/verify_golden.mjs
```

현재 기준:

- Python 테스트: 132개 통과
- TypeScript golden vector: 39/39 통과

## 참고

- Threads Graph API: https://developers.facebook.com/docs/threads
- Autoresearch methodology: https://github.com/karpathy/autoresearch

MIT License
