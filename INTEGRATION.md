# INTEGRATION.md - Threads scoring logic integration guide

이 문서는 `only-thread-logic-42326`을 다른 프로그램에 붙이는 방법을 설명합니다.

이 저장소는 **순수 점수 계산 라이브러리**입니다. Threads 토큰, API 호출, DB 저장, 스케줄러는 각 애플리케이션이 담당하고, 이 라이브러리는 입력값을 받아 점수만 계산합니다.

## 아키텍처 원칙

```text
Your application
├── Stores Threads tokens in its own .env or secret manager
├── Calls Threads Graph API
├── Builds PostStats and TopicContext
└── Imports sotda for scoring only

only-thread-logic-42326
├── No tokens
├── No API calls
├── No database writes
└── Pure formulas and pipeline
```

이 원칙 덕분에 SNS 생성기, 법률/컴플라이언스 모니터링, NLP 연구, 마케팅 대시보드, 알림 시스템 등 어떤 프로그램에도 같은 방식으로 통합할 수 있습니다.

## 설치

```bash
pip install git+https://github.com/geben147-create/only-thread-logic-42326.git
```

운영 환경에서는 특정 태그로 고정하는 것을 권장합니다.

```bash
pip install git+https://github.com/geben147-create/only-thread-logic-42326.git@v0.3.0
```

`requirements.txt` 예시:

```text
sotda-threads @ git+https://github.com/geben147-create/only-thread-logic-42326.git@v0.3.0
```

로컬 개발:

```bash
git clone https://github.com/geben147-create/only-thread-logic-42326.git
pip install -e ./only-thread-logic-42326
```

## 최소 통합 예시

```python
from sotda import ExplosionScoringPipeline, PostStats, TopicContext

pipeline = ExplosionScoringPipeline()

stats = PostStats(
    post_id="17841400000000000_9876543",
    current_vph=500,       # views / hours_since_post
    author_avg_vph=120,    # author's recent average VPH
    author_std_vph=45,     # author's recent VPH standard deviation
)

topic = TopicContext(
    topic="#ai",
    saturation_index=0.8,  # 0.0 = niche, 1.0 = saturated
)

result = pipeline.score(stats, topic)
print(result.to_dict())
```

애플리케이션 쪽에서 해야 할 일은 세 가지입니다.

1. Threads Graph API에서 게시물 조회수와 timestamp를 가져옵니다.
2. 작성자의 최근 게시물로 `author_avg_vph`, `author_std_vph`를 계산합니다.
3. 해시태그나 topic tag의 최근 빈도로 `saturation_index`를 계산합니다.

## 사용 패턴

### SNS 자동 생성기

`usability_flag == "HIGH"`인 게시물을 few-shot positive example로 사용합니다.

### 컴플라이언스 모니터링

특정 키워드 게시물의 확산을 감시하고 `HIGH` 또는 `viral` 신호가 나오면 알림이나 검토 큐로 보냅니다.

### NLP 연구

게시물 코퍼스에 확산 점수 라벨을 붙여 분류, 랭킹, 이상치 연구 데이터로 사용합니다.

### 마케팅 대시보드

브랜드 계정 게시물의 `final_score`, `post_burst_score`, `red_ocean_multiplier` 추이를 시계열로 저장합니다.

### 경쟁 분석

경쟁 계정의 outlier 게시물을 추출해 벤치마크 후보로 사용합니다.

## 제공 API

### Pipeline facade

일반적인 통합에는 이 세 가지를 사용하면 충분합니다.

- `PostStats`
- `TopicContext`
- `ExplosionScoringPipeline`

### 개별 공식

더 세밀하게 조합하려면 `sotda.formulas`에서 필요한 공식만 가져올 수 있습니다.

```python
from sotda import formulas as f

er = f.engagement_rate(likes=420, replies=55, views=12_500)
rp = f.repost_rate(reposts=110, views=12_500)
mz = f.modified_z(current_views, baseline_views_list)
health = f.account_health_score(er_norm, consistency_norm, vpf_norm, eff_norm, freq_norm, conv_norm, cred_norm)
high_thr, low_thr = f.media_type_branch("VIDEO")
```

전체 목록은 `sotda.formulas.__all__` 또는 [docs/FORMULA_MASTER.md](docs/FORMULA_MASTER.md)를 확인하세요.

## 자주 생기는 실수

| 실수 | 결과 | 해결 |
|---|---|---|
| `author_avg_vph=0`으로 채점 | z-score가 의미 없어짐 | 최소 30개 최근 게시물로 baseline 계산 |
| 게시 직후 1시간 미만에 채점 | VPH 노이즈가 큼 | 최소 6시간 후 1차 채점 권장 |
| `saturation_index`를 항상 0.5로 고정 | Phase 2가 의미 없어짐 | 최근 7일 해시태그 빈도로 정규화 |
| 이 저장소 안에 `.env` 저장 | 공개 저장소에 토큰 노출 위험 | 토큰은 사용하는 애플리케이션 루트에만 저장 |
| 플랫폼 간 `final_score` 직접 비교 | 잘못된 순위 해석 | `usability_flag` 또는 z-score로 비교 |

## 선택 기능: weight tuning

기본 가중치는 내장 `TEST_BATTERY`에서 100% fitness를 목표로 튜닝되어 있습니다. 도메인 데이터에 맞게 조정하려면 로컬에서만 다음 흐름을 사용하세요.

1. 애플리케이션에서 100-200건의 게시물과 human label을 수집합니다.
2. 로컬 복사본의 `sotda/evaluator.py::TEST_BATTERY`를 교체합니다.
3. `python -m sotda.optimizer --cycles 10`을 실행합니다.
4. 생성된 `data/best_weights.json`을 애플리케이션 설정으로 가져갑니다.
5. 공개 저장소에 사내 데이터나 비공개 label을 PR하지 않습니다.

## 통합 체크리스트

- [ ] `pip install git+...` 성공
- [ ] `from sotda import PostStats, TopicContext, ExplosionScoringPipeline` import 성공
- [ ] `.env`는 애플리케이션 루트에만 존재
- [ ] Threads Graph API 토큰은 Meta Developer Console에서 발급
- [ ] 최소 30개 최근 게시물로 author baseline 계산
- [ ] 게시 후 최소 6시간 뒤 채점
- [ ] `ScoringResult.usability_flag`를 애플리케이션 의사결정 로직에 연결
