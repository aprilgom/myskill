---
name: codex-archived-token-efficiency
description: Analyze, review, audit, score, evaluate, and improve Codex Desktop/CLI archived session JSONL logs for Codex-only token usage, cache efficiency, context pressure, tool-call density, and HTML dashboards. Trigger for prompts that explicitly mention Codex archived session token efficiency, archived Codex usage reports, ~/.codex/archived_sessions, Codex archived cached input ratio, Codex archived session costs, or Codex archived context bloat. Do not use for current/live Codex sessions, generic token-efficiency advice, non-Codex app/session reports, prompt compression, OpenAI API billing analysis, or Claude Code logs; use a live-session or domain-specific skill instead.
---

# Codex Archived Token Efficiency

Codex가 `~/.codex/archived_sessions/*.jsonl`에 남기는 세션 로그를 파싱해서 세션별 토큰 사용량, cached input 비율, output 밀도, 긴 컨텍스트 압박, 큰 출력 패턴을 집계하고 HTML 리포트를 만든다.

Codex 로그는 Claude Code 로그와 다르다. Claude는 assistant message의 `usage` 필드를 주로 읽지만, Codex는 `event_msg`의 `token_count.info.last_token_usage`에 turn별 토큰 사용량이 기록된다. 이 스킬은 `last_token_usage`를 누적해서 세션 totals를 만든다. `total_token_usage`는 누적값이라 세션 합산에 다시 더하면 중복 계산된다.

## 빠른 원칙

- 사용자가 경로를 주면 해당 repo cwd와 일치하는 Codex 세션만 필터링한다.
- 경로가 없으면 `~/.codex/archived_sessions` 전체를 분석한다.
- 비용은 API 가격에 대응한 추정치일 뿐이다. Codex 구독 과금과 1:1로 맞는다고 말하지 않는다.
- 스크립트는 현재 스킬 폴더의 `scripts/`를 사용한다. 예시는 `SKILL_DIR=/path/to/codex-archived-token-efficiency`로 쓴다.

## 동작 흐름

### 1. 대상 결정

현재 repo만 보고 싶으면 `--repo "$(pwd)"`를 사용한다. 전체 Codex 사용량을 보려면 `--repo`를 빼고 실행한다. 특정 로그 폴더를 분석할 때는 `--sessions-dir`를 직접 지정한다.

### 2. 세션 분석 실행

```bash
SKILL_DIR="${SKILL_DIR:-$HOME/.codex/skills/codex-archived-token-efficiency}"
python3 "$SKILL_DIR/scripts/analyze_sessions.py" \
  --repo "$(pwd)" \
  --out /tmp/codex_session_analysis.json
```

전체 archived sessions:

```bash
python3 "$SKILL_DIR/scripts/analyze_sessions.py" \
  --out /tmp/codex_session_analysis.json
```

계산 항목:

| 필드 | 설명 |
|---|---|
| `input_tokens` | Codex turn 입력 토큰 합 |
| `cached_input_tokens` | cached input 토큰 합 |
| `cache_hit_ratio` | `cached_input_tokens / input_tokens` |
| `output_tokens` | 모델 출력 토큰 합 |
| `reasoning_output_tokens` | 로그가 제공하는 reasoning output 토큰 |
| `total_tokens` | turn별 total token 합 |
| `cost_usd` | API-equivalent 추정 비용 |

### 3. 점수화

`analyze_sessions.py`는 각 세션을 4개 지표로 점수화한다.

| 지표 | 가중치 | 측정 |
|---|---:|---|
| Cached input utilization | 45% | cached input ratio. 90% 이상이 만점. |
| Output density | 25% | output/input 비율. 너무 낮으면 탐색 위주, 너무 높으면 긴 독백 신호. |
| Context pressure | 20% | uncached input 비율. 낮을수록 좋다. |
| Tool economy | 10% | output 1k 토큰당 tool call 수. 높으면 탐색 thrash 가능성. |

### 4. 대시보드 생성

```bash
python3 "$SKILL_DIR/scripts/build_dashboard.py" \
  --input /tmp/codex_session_analysis.json \
  --out /tmp/codex_efficiency_report.html \
  --repo-name "$(basename "$(pwd)")"
open /tmp/codex_efficiency_report.html
```

대시보드는 전체 세션 수, 총 토큰, cached input 비율, 평균 점수, API-equivalent 비용 추정, 토큰 사용량 상위 세션을 보여준다.

### 5. 비효율 패턴 검출

사용자가 "왜 토큰이 많이 쓰였는지", "어떤 패턴이 문제인지"를 물으면 패턴 검출기를 실행한다.

```bash
python3 "$SKILL_DIR/scripts/detect_patterns.py" \
  --repo "$(pwd)" \
  --out /tmp/codex_pattern_analysis.json

python3 "$SKILL_DIR/scripts/build_patterns_dashboard.py" \
  --input /tmp/codex_pattern_analysis.json \
  --out /tmp/codex_patterns_report.html
open /tmp/codex_patterns_report.html
```

검출 패턴:

| 패턴 | 신호 | 주요 조치 |
|---|---|---|
| context-bloat | input tokens 100k+ 이벤트 | 주제 분리, 새 세션 시작, 큰 컨텍스트 유지 줄이기 |
| giant-tool-outputs | 50k chars 이상 응답/결과 | `head`, `rg`, `limit`, 필요한 범위만 읽기 |
| poor-cache-util | input 30k+에서 cached ratio <50% | 긴 세션 중 큰 instruction/asset 변경 최소화 |
| subagent/tool overuse | output 대비 tool call 과다 | 작은 조회는 직접 처리, 병렬 작업만 위임 |
| reasoning/output spikes | output tokens 8k+ 이벤트 | 요구사항을 좁히고 중간 산출물로 나누기 |

### 6. 검증

보고 전 아래를 확인한다.

```bash
python3 -m py_compile "$SKILL_DIR/scripts/analyze_sessions.py" \
  "$SKILL_DIR/scripts/build_dashboard.py" \
  "$SKILL_DIR/scripts/detect_patterns.py" \
  "$SKILL_DIR/scripts/build_patterns_dashboard.py"

test -s /tmp/codex_session_analysis.json
test -s /tmp/codex_efficiency_report.html
```

스크립트 변경 후에는 synthetic fixture 검증도 실행한다.

```bash
python3 "$SKILL_DIR/scripts/validate_fixtures.py"
```

패턴 리포트를 만들었다면:

```bash
test -s /tmp/codex_pattern_analysis.json
test -s /tmp/codex_patterns_report.html
```

JSON의 `totals.sessions` 또는 `totals.sessions_total`이 0이면 비용/절감안을 단정하지 않는다.

## Output Format

최종 보고는 Korean으로 짧게 작성한다.

```markdown
**요약**
- 분석 범위: <repo 또는 archived_sessions 전체>, <세션 수>개 세션
- 총 토큰: <n>, cached input <x%>
- 평균 효율: <score>/<grade 또는 점수>

**우선순위 개선 3개**
1. <개선안> - 근거 <지표>
2. <개선안> - 근거 <지표>
3. <개선안> - 근거 <지표>

**산출물**
- `/tmp/codex_efficiency_report.html`
- `/tmp/codex_patterns_report.html` (실행한 경우)

**주의**
- 비용은 API-equivalent 추정치이며 Codex 구독 과금과 다를 수 있음.
```

## 에지 케이스

- `~/.codex/archived_sessions`가 없으면 "분석할 Codex archived session 로그가 없음"이라고 보고한다.
- matching repo 세션이 없으면 전체 분석을 제안하되 임의로 전체 분석 결과를 repo 결과처럼 말하지 않는다.
- `token_count` 이벤트가 없는 구버전/특수 로그는 건너뛴다.
- `session_index.jsonl`은 thread 이름과 updated_at 색인용이다. 토큰 분석에는 archived session JSONL을 우선 사용한다.
