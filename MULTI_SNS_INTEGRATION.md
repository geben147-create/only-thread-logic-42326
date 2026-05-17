# MULTI_SNS_INTEGRATION.md - Using multiple SOTDA packages together

이 문서는 하나의 애플리케이션에서 Threads, X, YouTube, Instagram 등 여러 SOTDA 로직 패키지를 함께 사용할 때의 충돌 방지 규칙을 정리합니다.

## 패키지 네이밍 규칙

각 플랫폼 패키지는 고유한 Python import name을 가져야 합니다.

| Platform | Repository | Python package | pip name |
|---|---|---|---|
| Threads | `only-thread-logic-42326` | `sotda` | `sotda-threads` |
| X/Twitter | `only-twitter-logic-4.24.26` | `sotda_x` | `sotda-x` |
| YouTube | `only-youtube-logic-*` | `sotda_yt` | `sotda-yt` |
| Instagram | `only-instagram-logic-*` | `sotda_ig` | `sotda-ig` |
| TikTok | `only-tiktok-logic-*` | `sotda_tt` | `sotda-tt` |
| LinkedIn | `only-linkedin-logic-*` | `sotda_li` | `sotda-li` |

권장 규칙:

- pip package: `sotda-<platform>`
- Python package: `sotda_<shortcode>`
- 플랫폼별 public class 이름은 같아도 import 경로는 달라야 합니다.

## 설치

```bash
pip install git+https://github.com/geben147-create/only-thread-logic-42326.git@v0.3.0
pip install git+https://github.com/geben147-create/only-twitter-logic-4.24.26.git@v0.1.0
```

## 안전한 import 패턴

### 모듈 단위 import

```python
import sotda      # Threads
import sotda_x    # X/Twitter

threads_pipeline = sotda.ExplosionScoringPipeline()
x_pipeline = sotda_x.ExplosionScoringPipeline()
```

### 별칭 import

```python
from sotda import ExplosionScoringPipeline as ThreadsScorer
from sotda_x import ExplosionScoringPipeline as XScorer

threads_pipeline = ThreadsScorer()
x_pipeline = XScorer()
```

### 피해야 할 import

```python
from sotda import ExplosionScoringPipeline
from sotda_x import ExplosionScoringPipeline
```

두 번째 import가 첫 번째 이름을 덮어씁니다.

```python
from sotda.formulas import *
from sotda_x.formulas import *
```

동일한 공식 이름이 충돌하므로 wildcard import는 사용하지 마세요.

## 플랫폼 간 점수 비교

각 플랫폼의 `final_score`는 서로 다른 baseline과 입력 신호를 사용합니다. 따라서 숫자를 직접 비교하면 안 됩니다.

잘못된 비교:

```python
threads_score = 300
x_score = 400
# x_score가 더 높으므로 X 게시물이 더 좋다? 잘못된 해석입니다.
```

권장 비교:

```python
threads_result = threads_pipeline.score(...)
x_result = x_pipeline.score(...)

# 각 플랫폼 내부 기준에서 HIGH인지 비교
threads_result.usability_flag == "HIGH"
x_result.usability_flag == "HIGH"

# 또는 account-relative z-score를 비교
threads_z = threads_result.post_burst_score
x_z = x_result.tweet_burst_score
```

## 다언어 포팅

이 저장소의 Python 구현은 reference implementation입니다. 다른 언어로 포팅할 때는 다음 순서를 따르세요.

1. [SPEC.md](SPEC.md)에서 공식과 타입을 확인합니다.
2. [golden_vectors.json](golden_vectors.json)을 테스트 데이터로 사용합니다.
3. 대상 언어에서 같은 함수를 구현합니다.
4. 모든 golden vector를 통과하면 compliant로 봅니다.

### 통합 패턴 A: Python scoring service

```text
Rust/Go/Swift app -> HTTP/gRPC -> Python sotda service -> score
```

빠르게 붙이기 좋고, Python 구현을 그대로 사용할 수 있습니다.

### 통합 패턴 B: Native port

```text
Go app -> import go_sotda_threads -> score in-process
```

성능과 배포 단순성이 중요할 때 적합합니다. 반드시 golden vector 검증을 통과해야 합니다.

### 통합 패턴 C: CLI subprocess

```text
Any app -> python -m sotda_cli score --input-json ...
```

간단하지만 성능과 에러 처리가 약합니다. 임시 통합용으로만 권장합니다.

## 버전 고정

운영 애플리케이션에서는 반드시 태그를 고정하세요.

```text
sotda-threads @ git+https://github.com/geben147-create/only-thread-logic-42326.git@v0.3.0
sotda-x       @ git+https://github.com/geben147-create/only-twitter-logic-4.24.26.git@v0.1.0
```

## 체크리스트

- [ ] 플랫폼별 Python package name이 충돌하지 않음
- [ ] wildcard import를 사용하지 않음
- [ ] class는 모듈 단위 또는 alias로 구분함
- [ ] 플랫폼 간 `final_score` 숫자를 직접 비교하지 않음
- [ ] 비교는 `usability_flag` 또는 z-score 중심으로 수행함
- [ ] 각 플랫폼 토큰은 사용하는 애플리케이션의 secret manager에만 저장함
- [ ] 다언어 포트는 `golden_vectors.json`을 통과함

요약: **다른 패키지 이름, 모듈 단위 import, flag/z-score 기반 비교**만 지키면 여러 SOTDA 패키지를 한 애플리케이션에서 안전하게 함께 사용할 수 있습니다.
