# INTEGRATION.md — 이 로직을 어떤 프로그램에든 통합하기

> 이 레포는 **어떤 프로그램에서든 Threads 게시물 폭발을 점수화할 필요가 있을 때** 가져다 쓰는 순수 스코어링 라이브러리입니다.
> 용도 예시: SNS 자동 생성기, 법률/컴플라이언스 모니터, 한국어 NLP 파이프라인, 마케팅 대시보드, 리서치 툴, 알림 시스템 등.
> 공통점은 하나 — "Threads 게시물의 폭발/확산을 수치로 판단해야 한다."

---

## 1. 아키텍처 전제 — 순수 라이브러리

```
┌─────────────────────────────────────────────────────────┐
│  당신이 개발 중인 프로그램 (private, 용도 무관)        │
│                                                          │
│  - SNS 생성기 / 법률 컴플라이언스 / NLP 툴 / 기타       │
│  - Threads 토큰 .env 보관 (이 레포 아님)                │
│  - Graph API 호출로 Insights 받아오기                   │
│  - import sotda  ◄──────┐                                │
│  - sotda로 점수만 계산   │                                │
└──────────────────────────┼───────────────────────────────┘
                           │ pip install
                           │
┌──────────────────────────┴───────────────────────────────┐
│  only-thread-logic-42326 (이 public 레포)               │
│                                                          │
│  - 순수 수학 (I/O 없음)                                 │
│  - PostStats in → ScoringResult out                     │
│  - 토큰/API 호출 코드 절대 없음                         │
└──────────────────────────────────────────────────────────┘
```

핵심 원칙:
- **이 public 레포에는 토큰도, API 호출 코드도 없습니다.** 앞으로도 그럴 것입니다.
- 당신의 프로그램이 Threads API에서 데이터를 받아 `PostStats`를 만들고 `sotda`에 넘깁니다.
- `sotda`는 input만 받아 점수를 돌려줍니다 — 용도에 무관.

---

## 2. 설치

당신의 프로그램에서:

```bash
# Git 직접 설치 (가장 간단)
pip install git+https://github.com/geben147-create/only-thread-logic-42326.git

# 또는 특정 태그 고정 (프로덕션 권장)
pip install git+https://github.com/geben147-create/only-thread-logic-42326.git@v0.1.0
```

`requirements.txt`에 추가:

```
sotda-threads @ git+https://github.com/geben147-create/only-thread-logic-42326.git@main
```

로컬 개발이면:

```bash
git clone https://github.com/geben147-create/only-thread-logic-42326.git
pip install -e ./only-thread-logic-42326
```

---

## 3. 최소 사용법 (어떤 프로그램이든 동일)

```python
from sotda import ExplosionScoringPipeline, PostStats, TopicContext

pipeline = ExplosionScoringPipeline()

# 당신의 프로그램이 어디서 어떻게 수집했든,
# Threads Graph API 필드만 넣으면 됩니다.
stats = PostStats(
    post_id="17841400000000000_9876543",
    current_vph=500,       # views / hours_since_post
    author_avg_vph=120,    # 최근 N일간 이 계정 게시물 VPH 평균
    author_std_vph=45,     # 〃 표준편차
)
topic = TopicContext(
    topic="#ai",
    saturation_index=0.8,  # 해시태그/토픽 포화도 0.0 ~ 1.0
)

result = pipeline.score(stats, topic)
print(result.to_dict())
# {'post_burst_score': 8.44, 'red_ocean_multiplier': 1.4,
#  'final_score': 590.8, 'usability_flag': 'HIGH', 'corrections_applied': []}
```

이게 전부입니다. 나머지는 당신의 프로그램이 알아서 합니다.

---

## 4. 용도별 통합 패턴 예시

### A. SNS 자동 생성기
발행 → 몇 시간 대기 → 점수 계산 → HIGH 점수 게시물을 다음 생성의 few-shot positive로

### B. 법률/컴플라이언스 모니터
특정 키워드 게시물 감시 → 폭발(viral/surge) 감지 시 알림 → 컴플라이언스 팀 에스컬레이션

### C. 한국어 NLP 연구 툴
한국어 게시물 코퍼스 수집 → 폭발 여부로 라벨 붙여 NLP 모델 학습 데이터로

### D. 마케팅 대시보드
브랜드 계정 게시물 모두 점수화 → 시간별 추이 그래프 → 효과 있는 포맷 식별

### E. 경쟁사 분석
경쟁사 계정 게시물 정기 점수화 → outlier_ratio 높은 게시물만 추려 벤치마크 대상

**모든 용도에서 통합 코드는 같습니다** — 위 3번의 10줄. 다른 건 당신 프로그램이 점수를 어떻게 쓰는지뿐.

---

## 5. 당신의 프로그램에서 쓰면 안 되는 것

- ❌ 이 레포에 토큰 커밋 (이 레포는 토큰을 읽지도 쓰지도 않음)
- ❌ `sotda/optimizer.py` — autoresearch 루프는 **선택 기능**. 필요 없으면 무시
- ❌ `sotda/evaluator.py`의 `TEST_BATTERY` — 내부 검증용. 건드리지 말 것

**당신이 쓸 것만 3개:**
- `PostStats` (input)
- `TopicContext` (input)
- `ExplosionScoringPipeline` (→ `ScoringResult` output)

---

## 6. 자주 발생하는 실수 (용도 무관)

| 실수 | 결과 | 해결 |
|---|---|---|
| `author_avg_vph=0` 넣음 | 모든 z-score 폭주 | 최소 30일 baseline 먼저 수집 |
| 게시 직후(1시간 미만) 채점 | VPH 노이즈 커서 오탐 | 최소 6시간 기다림 |
| `hashtag_saturation`을 매번 0.5로 하드코딩 | Phase 2 무의미해짐 | 해시태그 최근 7일 포스트 수로 normalize |
| 토큰을 `sotda/` 안에 `.env`로 넣음 | 공개 시 유출 | 당신 프로그램 루트에 `.env` — 이 레포엔 절대 X |

---

## 7. (선택) 가중치 튜닝

기본 가중치로 내장 TEST_BATTERY 100% fitness. 당신 도메인 데이터에서 flag가 자주 틀리면:

1. 당신 프로그램에서 100-200건 수집 (`post_id, actual_metrics, human_label`)
2. 이 레포를 clone해 **로컬에서만** `sotda/evaluator.py::TEST_BATTERY`를 당신 데이터로 교체
3. `python -m sotda.optimizer --cycles 10` 실행 → Claude가 가중치 제안
4. 나온 `data/best_weights.json`을 당신 프로그램 프로젝트로 복사
5. 프로그램에서 `Phase1PostExplosion(min_vph_threshold=...)` 식으로 주입

**교체한 TEST_BATTERY는 절대 이 public 레포에 PR하지 말 것** — 당신 도메인 특화라 일반 사용자에게 역효과.

---

## 8. 체크리스트

통합 전 확인:

- [ ] `pip install git+...` 성공
- [ ] `from sotda import PostStats, TopicContext, ExplosionScoringPipeline` import 성공
- [ ] `.env`는 당신 프로그램 루트에만 (이 레포에는 없음)
- [ ] Threads Graph API 토큰은 Meta Developer Console에서 발급
- [ ] 최소 30일치 당신 계정 게시물 VPH로 `author_avg_vph`, `author_std_vph` 계산 로직 구현
- [ ] 게시 후 최소 6시간 지난 뒤 채점
- [ ] `ScoringResult.usability_flag`를 당신 프로그램 내부 로직에 연결
