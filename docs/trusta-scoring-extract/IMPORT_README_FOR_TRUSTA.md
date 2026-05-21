# IMPORT_README_FOR_TRUSTA.md

> **이 번들은 코드가 아니라 "설계 소스"입니다.**
> TRUSTA 프로젝트에 복사해 넣을 5개 문서(MD 4 + JSON 1)만 포함되어 있으며,
> **실행 가능한 코드, 마이그레이션, 패키지 의존성, 시크릿은 단 한 줄도 없습니다.**

---

## 1. TRUSTA 프로젝트에 넣을 위치 제안

```
TRUSTA_repo_root/
└── docs/
    └── scoring-audit/
        └── external/              ← 이 번들 5개 파일이 여기로
            ├── SCORING_REPO_COMPARISON.md
            ├── TRUSTA_SCORING_TAXONOMY_MAP.json
            ├── COMMERCIAL_FIT_SCORE_SPEC.md
            ├── BLOCKED_YOUTUBE_LOGICS.md
            └── IMPORT_README_FOR_TRUSTA.md   ← 자기 자신
```

이유:
- `docs/` 하위 = 코드와 분리된 설계 자료 영역
- `scoring-audit/external/` = 외부 repo 분석 결과임을 명시 (TRUSTA 내부 결정과 구분)
- 파일명에 `EXTERNAL` 또는 `external/` 경로가 있으므로, 향후 누군가 "코드처럼" 다루는 오해 방지

---

## 2. TRUSTA 개발 Captain에게 줄 다음 프롬프트

````
너는 TRUSTA / LEXlogicThread Discovery 엔진의 scoring taxonomy 설계 Captain이다.

작업 위치:
TRUSTA repo root.

배경:
docs/scoring-audit/external/ 에 외부 scoring repo 3개를 분석한 read-only 번들이
이미 들어와 있다. 이 번들을 기준으로 TRUSTA 안에 scoring 설계를 결정하는 것이 목표다.

읽어야 할 파일 (순서대로):
1. docs/scoring-audit/external/IMPORT_README_FOR_TRUSTA.md  ← 가장 먼저
2. docs/scoring-audit/external/SCORING_REPO_COMPARISON.md   ← 3 repo 비교 결론
3. docs/scoring-audit/external/TRUSTA_SCORING_TAXONOMY_MAP.json ← 26개 로직 카테고리 매핑
4. docs/scoring-audit/external/COMMERCIAL_FIT_SCORE_SPEC.md ← 광고 점수 설계
5. docs/scoring-audit/external/BLOCKED_YOUTUBE_LOGICS.md    ← 이식 금지 목록

기준:
- only-thread-logic-42326의 26개 수식 = canonical math (건드리지 말 것)
- commercialFitScore는 신규 수식 0개, 기존 6개 재조합
- YouTube RPM/revenue/search_volume/watch_time 의존 로직 이식 금지
- videoScore / channelScore / commercialFitScore를 별도 노출 (overallScore는 기본 null)

목표:
1. TRUSTA Discovery DB 스키마에 JSONB scoring 컬럼이 이미 존재하는지 확인
2. 존재한다면 → migration 0개로 출시 가능
3. 존재하지 않는다면 → 신규 migration 1개 설계만 제시 (실행 X)
4. UI에 3개 score를 분리해서 보여줄 영역 식별
5. 현재 코드에 §6 BLOCKED 키워드(rpm, revenue, watch_time 등)가 등장하는지 grep 진단

절대 금지:
- 코드 수정 금지
- migration 실행 금지
- 패키지 설치 금지
- git add / commit / push 금지
- 외부 API key 추가 금지

출력:
- 발견된 JSONB 컬럼 위치 (또는 부재)
- TRUSTA 내부 scoring 코드 현황 진단
- BLOCKED 키워드 grep 결과
- migration 필요 여부 (yes/no)
- 다음 단계 권장 (구현 전에 사람 결정 필요한 항목)

보고만 하고 멈춰라.
````

---

## 3. 이 번들의 본질 (명시적)

| 항목 | 상태 |
|---|---|
| **실행 가능한 코드** | ❌ 없음 |
| **마이그레이션 파일** | ❌ 없음 |
| **API 라우트** | ❌ 없음 |
| **패키지 의존성** | ❌ 없음 |
| **시크릿/토큰/키** | ❌ 없음 |
| **원본 repo 통째 복사본** | ❌ 없음 |
| **설계 결정 (DECISIONS.md 류)** | ❌ 없음 (TRUSTA Captain 권한) |
| **분석 보고서 (MD)** | ✅ 4개 |
| **카테고리 매핑 (JSON)** | ✅ 1개 |
| **재현 가능한 가중치 / 등급 / 정규화 규칙** | ✅ 문서에 명시 |

→ 이 번들은 **TRUSTA 내부 의사결정의 입력**이지, 결정 그 자체가 아닙니다.

---

## 4. 구현 전 확인 질문 5개 (TRUSTA Captain → 사용자)

다음 질문에 답이 모이기 전에는 구현을 시작하지 말 것:

### Q1. JSONB 컬럼 현존 여부
TRUSTA Discovery 테이블 (예: `posts`, `accounts`, `scoring_results`)에 이미 JSONB 형식의 메타데이터 컬럼이 존재합니까?
- ✅ 있음 → migration 0개로 출시 가능
- ❌ 없음 → 037 (또는 그 이후) migration 1개 신규 설계 필요

### Q2. commercialFitScore 가중치 v0.1 채택 여부
`COMMERCIAL_FIT_SCORE_SPEC.md §4`의 가중치 (25/20/20/15/10/10) 를 그대로 박을지, 아니면 backtest 후 결정할지?
- ✅ 그대로 박기 → 즉시 구현 가능
- ⏸ backtest 후 → 데이터 수집 phase 먼저

### Q3. overallScore 노출 정책
3개 score (`videoScore`, `channelScore`, `commercialFitScore`) 외에 단일 `overallScore`도 UI에 노출할지?
- 사용자 의도 (§3): 별도 노출 = `null` 유지 권장
- 하지만 admin/internal 대시보드에서는 가중합 필요할 수 있음

### Q4. 정규화 기준 (NICHE_RANGES) 도입 여부
test_logic20_30_only의 `NICHE_RANGES[niche]` 패턴을 TRUSTA에도 도입할지?
- ✅ 도입 → niche-relative 비교 가능, 정확도 ↑, 복잡도 ↑
- ❌ 미도입 → 글로벌 통일 기준, 단순, 도메인 편향 위험

### Q5. Kar-auto 튜닝 워크플로우 차용 여부
Kar-auto의 `best_weights.json` + iterative LLM tuning 패턴을 thread-logic `optimizer.py`에 차용해 TRUSTA 가중치 튜닝 인프라로 만들지?
- ✅ 차용 → 데이터 모이는 대로 자동 가중치 개선
- ⏸ 보류 → 사람이 손으로 튜닝 (출시 후 결정)

---

## 5. 이 번들을 사용할 때의 원칙

1. **읽기 전용**. TRUSTA Captain은 이 번들의 5개 파일을 **수정하지 않는다**. 변경이 필요하면 외부 repo 재분석 결과로만 갱신.
2. **인용 OK, 복사 NO**. TRUSTA 내부 문서에서 본 번들을 인용할 수 있으나, 본문을 통째 복사하지 말 것 (단일 진실 원천 유지).
3. **버전 핀**. `TRUSTA_SCORING_TAXONOMY_MAP.json`의 `version: "trusta-taxonomy-v0.1.0"` 와 TRUSTA Discovery `scoring.version: "sotda-threads-v0.1.0"` 가 함께 움직여야 함.
4. **차단 룰은 보수적으로**. `BLOCKED_YOUTUBE_LOGICS.md`는 "지금은 안 됨"이지 "영원히 안 됨"이 아님. Threads API가 바뀌면 §7 해제 조건 따라 재검토.
5. **3개 score 분리 보존**. 사용자 의도(§3)에 따라 `videoScore` / `channelScore` / `commercialFitScore`는 **개별 의사결정 축**으로 보존.

---

## 6. 번들 파일 5개 요약

| 파일 | 한 줄 요약 |
|---|---|
| `SCORING_REPO_COMPARISON.md` | 3개 repo의 역할/기능/제약을 비교하고 only-thread-logic-42326을 canonical로 확정한 보고서 |
| `TRUSTA_SCORING_TAXONOMY_MAP.json` | 26개 수식 전체에 trusta_category / score_type / use_in_* 플래그를 기계 가독 형식으로 부여한 매핑표 |
| `COMMERCIAL_FIT_SCORE_SPEC.md` | 신규 수식 0개로 기존 6개를 재조합해 commercialFitScore를 만드는 사양서 (가중치/계산식/JSON 예시 포함) |
| `BLOCKED_YOUTUBE_LOGICS.md` | YouTube 기반 로직 중 Threads로 이식하면 안 되는 항목과 각 차단 사유 + 대체 Threads 로직 매핑 |
| `IMPORT_README_FOR_TRUSTA.md` | 이 번들 자기 자신의 사용법 + TRUSTA Captain용 다음 프롬프트 + 구현 전 확인 질문 5개 |

---

*read-only import guide 종료. TRUSTA 측 구현은 위 5개 질문 답이 모인 뒤에 시작.*
