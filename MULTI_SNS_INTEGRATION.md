# MULTI_SNS_INTEGRATION.md — 여러 SNS 로직을 하나의 프로그램에 같이 쓰기

> 시나리오: 당신은 **하나의 프로그램**에 Threads, X (Twitter), 향후 YouTube/Instagram 등 **여러 SNS 로직을 순차적으로 적용**하려 합니다. 이 문서는 충돌 방지와 안전한 공존 방법을 정리합니다.

---

## 1. 패키지 네이밍 규칙 (충돌 방지의 핵심)

모든 SOTDA 파생 레포는 고유 Python 패키지명을 씁니다. 같은 Python 프로세스 안에서 여러 레포를 동시에 import해도 서로 밟지 않습니다.

| 플랫폼 | 레포 | Python 패키지 | pip 이름 |
|---|---|---|---|
| Threads | only-thread-logic-42326 | `sotda` | `sotda-threads` |
| X (Twitter) | only-twitter-logic-4.24.26 | `sotda_x` | `sotda-x` |
| YouTube (향후) | only-youtube-logic-* | `sotda_yt` | `sotda-yt` |
| Instagram (향후) | only-instagram-logic-* | `sotda_ig` | `sotda-ig` |
| TikTok (향후) | only-tiktok-logic-* | `sotda_tt` | `sotda-tt` |
| LinkedIn (향후) | only-linkedin-logic-* | `sotda_li` | `sotda-li` |

**규칙**:
- pip 이름: `sotda-<platform>` (하이픈)
- Python 패키지: `sotda_<shortcode>` (언더스코어)
- 새 플랫폼 추가 시 같은 패턴을 따르면 자동으로 충돌 없음

---

## 2. 설치 (공존)

```bash
pip install git+https://github.com/geben147-create/only-thread-logic-42326.git
pip install git+https://github.com/geben147-create/only-twitter-logic-4.24.26.git
# 향후: pip install git+https://github.com/geben147-create/only-youtube-logic-*.git
```

두 패키지는 서로 다른 디렉토리에 설치됩니다. 의존성도 각자 독립.

---

## 3. 프로그램 안에서 사용 (충돌 없는 import)

### ✅ 권장 — 네임스페이스 import

```python
import sotda           # Threads
import sotda_x         # X (Twitter)

threads_pipeline = sotda.ExplosionScoringPipeline()
x_pipeline       = sotda_x.ExplosionScoringPipeline()

# 같은 클래스 이름이지만 다른 모듈 → 서로 간섭 없음
```

### ✅ 권장 — 별칭 import

```python
from sotda import ExplosionScoringPipeline as ThreadsScorer
from sotda_x import ExplosionScoringPipeline as XScorer
```

### ⚠️ 위험 — 별칭 없이 같은 이름 직접 import

```python
from sotda import ExplosionScoringPipeline     # Threads 버전
from sotda_x import ExplosionScoringPipeline   # X가 덮어씀!
# → 나중 import한 X 버전만 남음
```

### ⚠️ 절대 금지 — wildcard import

```python
from sotda.formulas import *
from sotda_x.formulas import *    # 같은 이름 함수 모두 덮어씀
```

---

## 4. 플랫폼 간 점수 비교 (정규화)

각 플랫폼의 `final_score`는 서로 다른 기준치에서 계산되므로 **절대값 비교 금지**입니다.

### ❌ 잘못된 비교
```python
threads_score = 300   # Threads post
x_score       = 400   # X tweet
# "X가 더 잘했다" ← WRONG. 플랫폼 baseline이 다름.
```

### ✅ 올바른 비교 — 플래그 기반

```python
threads_result = threads_pipeline.score(...)   # usability_flag: 'HIGH'
x_result       = x_pipeline.score(...)          # usability_flag: 'HIGH'
# 둘 다 자기 플랫폼 기준 'HIGH' → 동등한 성과
```

### ✅ 올바른 비교 — z-score 기반

```python
# z-score는 계정 자신의 평균 대비이므로 플랫폼 무관
threads_z = threads_result.post_burst_score     # 4.2σ
x_z       = x_result.tweet_burst_score          # 3.8σ
# 4.2σ가 3.8σ보다 큰 폭발 → 플랫폼 무관하게 비교 가능
```

---

## 5. 충돌 위험 체크리스트

프로그램에 새 SOTDA 레포를 추가할 때 확인:

- [ ] 패키지명(`sotda_X`) 충돌 없음 — 위 명명 규칙 따름
- [ ] Import 시 모든 class를 별칭으로 구분하거나 모듈 단위로 접근
- [ ] `from ... import *` 없음
- [ ] 플랫폼 간 `final_score` 절대값 비교 금지 — 플래그 또는 z-score만 비교
- [ ] 각 플랫폼 토큰은 각자의 `.env`에, 절대 레포 안에 들어가지 않음
- [ ] `requirements.txt`에 3개 이상 SOTDA 패키지가 공존한다면 각자 pin된 버전으로 (`@v0.3.0` 등)

---

## 6. 다언어 프로그램에서 쓰기 (Python 외)

이 레포는 Python 구현이지만 **수식 자체는 언어 무관**합니다. TypeScript/Go/Rust/Java 등으로 포팅할 때:

1. `SPEC.md` 읽기 — 각 수식의 수학적 정의 + 의사코드
2. `golden_vectors.json` 다운로드 — 입력/기대 출력 테스트 벡터
3. 당신 언어로 함수 구현
4. golden vectors 전부 통과하면 compliant

### 크로스-언어 통합 패턴 A: 마이크로서비스
```
[Rust 생성기] --HTTP--> [Python sotda 서버] --점수--> [Rust 생성기]
```
- Python 레포를 작은 FastAPI 서버로 감싸 REST/gRPC 노출
- 다른 언어 서비스가 HTTP로 점수 요청

### 크로스-언어 통합 패턴 B: 네이티브 포팅
```
[Go 프로그램] --import--> [go_sotda_x port]
```
- 당신 언어로 직접 포팅 (SPEC + golden vectors로 검증)
- 네트워크 호출 없이 인프로세스 속도

### 크로스-언어 통합 패턴 C: CLI 서브프로세스
```
[Swift 앱] --subprocess--> [python -m sotda_x.cli score --input-json=...]
```
- CLI 래퍼를 Python으로 한 번 구현, 다른 언어에서 shell로 호출
- 설정 단순, 성능은 B > A > C

---

## 7. 버전 관리 전략 (여러 SOTDA 공존 시)

각 레포는 독립 버전을 씁니다. 당신 프로그램의 `requirements.txt`에 명시:

```
sotda-threads @ git+https://github.com/geben147-create/only-thread-logic-42326.git@v0.3.0
sotda-x       @ git+https://github.com/geben147-create/only-twitter-logic-4.24.26.git@v0.1.0
```

새 버전이 나와도 `@v0.3.0` 태그로 고정돼 있어 당신 프로그램은 안 깨집니다. 업그레이드는 수동으로 태그만 바꾸면 됩니다.

---

## 8. 자주 하는 실수 + 해결

| 실수 | 증상 | 해결 |
|---|---|---|
| `from sotda import ExplosionScoringPipeline` 후 `from sotda_x import ExplosionScoringPipeline` | Threads 버전이 X 버전에 덮어씀 | 둘 중 하나 별칭으로 (`as ThreadsScorer`) |
| 플랫폼 간 `final_score` 값 직접 비교 | 잘못된 우열 판정 | `usability_flag` 또는 `z_vph`로 비교 |
| SOTDA 레포에 토큰 `.env` 추가 | 공개 시 유출 | 당신 프로그램 루트에만 `.env`, SOTDA 레포는 pure library |
| 한 SOTDA 레포의 `TEST_BATTERY`를 당신 데이터로 교체 후 PR | 일반 사용자에 역효과 | 로컬에서만 교체, PR 금지 |
| 다언어 포팅 후 golden_vectors 검증 스킵 | 미묘한 계산 오차 | 반드시 `golden_vectors.json` 전부 통과 확인 |

---

## 9. 한 줄 요약

> **같은 이름 다른 패키지 + 모듈 단위 import + flag/z-score로만 비교** — 이 3가지만 지키면 SOTDA 레포 몇 개가 공존해도 충돌 없음.
