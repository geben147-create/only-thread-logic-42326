# only-thread-logic-42326 — SOTDA Threads v0.1.0

> **Threads Graph API 게시물 폭발(viral/surge) 스코어링 라이브러리.**
> 26개 수식 + 3-phase 파이프라인을 **어떤 프로그램에든** 가져다 쓸 수 있는 순수 Python 라이브러리.

외부 의존성 0개. 토큰/API 호출 코드 없음 (의도적으로 pure). 테스트 44/44 통과, 내장 TEST_BATTERY 100% fitness.

---

## 무엇을 하나

두 레이어의 API를 제공합니다:

### Layer 1 — 개별 수식 26개 (pick-and-mix)

당신 프로그램에 필요한 것만 골라 씁니다:

```python
from sotda import formulas as f

# 🔵 Threads 전용
f.repost_rate(reposts=110, views=12500)       # 0.0088
f.quote_rate(quotes=30, views=12500)          # 0.0024
f.viral_velocity_24h(reposts=110, hours_since_post=12)  # 9.17 reposts/h
f.reply_ratio(replies=55, views=12500)        # 0.0044
f.share_rate(shares=18, views=12500)          # 0.00144
f.quote_to_reply_ratio(quotes=30, replies=55) # 0.545
f.threads_satisfaction(0.05, 0.03, 0.02, 0.01) # 100.0 (완벽 게시물)
f.media_type_branch("VIDEO")                  # (220.0, 80.0)
f.link_attachment_penalty("https://...")      # 0.7

# 🟢 공통 (YouTube와 동일)
f.engagement_rate(likes=420, replies=55, views=12500)  # 0.038
f.like_ratio(420, 12500)                      # 0.0336
f.modified_z(1_000_000, baseline_views)       # 6737.7 (viral outlier)
f.alert_level(z_score=5.5)                    # "viral"
f.account_momentum(200_000, 100_000, 1500, 1000)  # 3.0x
f.outlier_ratio(50_000, 10_000)               # 5.0x
f.audience_credibility(0.06)                  # "REAL"
# ... 총 26개 (17 공통 + 9 Threads 전용)
```

### Layer 2 — 조합된 3-Phase 파이프라인 (권장 시작점)

개별 수식들이 미리 조합된 버전:

```python
from sotda import ExplosionScoringPipeline, PostStats, TopicContext

pipeline = ExplosionScoringPipeline()
result = pipeline.score(
    PostStats(post_id="threads_42", current_vph=500,
              author_avg_vph=120, author_std_vph=45),
    TopicContext(topic="#ai", saturation_index=0.8),
)
print(result.to_dict())
# {'post_burst_score': 8.44, 'red_ocean_multiplier': 1.4,
#  'final_score': 590.8, 'usability_flag': 'HIGH', 'corrections_applied': []}
```

`usability_flag`(`HIGH`/`MEDIUM`/`LOW`)를 당신 프로그램의 판단 기준으로 쓰면 됩니다.

---

## 누가 쓰면 좋은가

Threads 게시물 성능을 수치화할 필요가 있는 **모든 프로그램**:

- SNS 자동 생성기 (HIGH 게시물을 few-shot positive로)
- 법률/컴플라이언스 모니터 (viral 감지 시 알림)
- 한국어 NLP 연구 (폭발 여부를 라벨로)
- 마케팅 대시보드 (포맷별 효과 비교)
- 경쟁사 분석 (outlier 게시물 벤치마크)
- 알림 시스템 (surge 발생 시 푸시)
- 기타 Threads 데이터를 다루는 어떤 것이든

통합 방법은 모두 동일 — 자세히는 [`INTEGRATION.md`](INTEGRATION.md) 참조.

---

## 설치

```bash
# 당신의 프로젝트에서:
pip install git+https://github.com/geben147-create/only-thread-logic-42326.git

# 로컬 개발:
git clone https://github.com/geben147-create/only-thread-logic-42326.git
pip install -e ./only-thread-logic-42326
```

Python 3.10+ 필요. dev 의존성은 pytest만.

---

## 3-Phase 파이프라인

1. **Phase 1 (z-VPH)**: 계정 대비 상대 폭발 감지 (`(current_vph - author_avg) / author_std`) + 소규모 계정 보정 (log1p + std floor)
2. **Phase 2 (Red Ocean)**: 해시태그/토픽 포화도 기반 승수 (레드오션에서 터지면 더 가치있음)
3. **Phase 3 (Output)**: `final = z * mult * 50 + 50` → HIGH/MEDIUM/LOW 플래그

상세: [`docs/explosion_logic.md`](docs/explosion_logic.md)

---

## Threads API 기반 26개 수식

- 🟢 **공통 17개**: YouTube와 동일 수식, 필드명만 rename (`channel→author`, `comments→replies`, `subscribers→followers`)
- 🔵 **Threads 전용 9개**: `reposts`/`quotes`/`shares`/`media_type` 활용 신규 수식
- 🔴 **삭제 17개**: Threads API가 `watch_time`·키워드볼륨·수익·Shorts 미제공이라 구현 불가

상세: [`docs/FORMULA_MASTER.md`](docs/FORMULA_MASTER.md)

---

## 구조

```
only-thread-logic-42326/
├── README.md                  # 이 파일
├── INTEGRATION.md             # 어떤 프로그램에든 통합하는 방법
├── pyproject.toml             # pip install -e . 가능
├── .env.example               # 토큰은 여기 아님 — 당신 프로젝트에
├── docs/
│   ├── FORMULA_MASTER.md      # 26개 수식 전체
│   └── explosion_logic.md     # 3-phase 알고리즘 근거
├── sotda/                     # 메인 패키지 (import 대상)
│   ├── pipeline.py            # 3-phase (이것이 90% 사용 대상)
│   ├── evaluator.py           # 내장 TEST_BATTERY
│   ├── generator.py           # (선택) autoresearch용 LLM 래퍼
│   └── optimizer.py           # (선택) autoresearch 루프
├── examples/
│   └── basic_usage.py         # 10줄짜리 통합 예시
└── tests/
    ├── test_pipeline.py
    ├── test_evaluator.py
    └── test_formula_triage.py # 26 수식 정합성 검증
```

당신이 쓸 것은 `sotda/pipeline.py` 하나뿐입니다. `evaluator.py`/`generator.py`/`optimizer.py`는 이 레포 자체를 튜닝하기 위한 부속품.

---

## 테스트

```bash
pytest                     # 전체 44 테스트
python examples/basic_usage.py   # 통합 예시 실행
```

---

## (선택 기능) LLM 기반 가중치 자동 튜닝

karpathy/autoresearch 패턴을 차용한 **선택 기능**입니다. 당신 프로그램이 정상 동작하는 데 필요 없습니다.

만약 내장 TEST_BATTERY 대신 당신 도메인 데이터로 가중치를 튜닝하고 싶다면:

```bash
python -m sotda.optimizer --dry-run --cycles 1  # 평가만
python -m sotda.optimizer --cycles 5            # LLM 호출 (Claude CLI 필요)
```

자동으로 `results.tsv`에 누적 (gitignored). 자세한 워크플로우는 [`program.md`](program.md).

---

## 참고

- Threads Graph API: https://developers.facebook.com/docs/threads
- karpathy/autoresearch (methodology 영감): https://github.com/karpathy/autoresearch

---

*v0.1.0 | Threads 전용 | 2026-04-23 | MIT License*
