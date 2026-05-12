# Codex-Ready Codebase Rubric · v1 (100 pt)

이 루브릭은 "Codex가 이 repo에서 안전하게 변경하고 검증할 수 있는가"를 평가합니다. 코드 품질 자체보다 agent 작업성, 검증성, 안전 경계를 봅니다.

| Cat | Name | Points |
|-----|------|--------|
| A | Codex Navigation & Scope Coverage | 15 |
| B | AGENTS.md / Context Quality | 20 |
| C | Local Development Workflow Clarity | 15 |
| D | Architecture & Dependency Mapping | 15 |
| E | Verification Gates & Testability | 20 |
| F | Safety, Secrets & Change Boundaries | 10 |
| G | Agent Outcome Evidence | 5 |

## A. Codex Navigation & Scope Coverage · /15

핵심 module마다 `AGENTS.md` 또는 `CODEX.md` 같은 Codex-native context가 있는지 봅니다. `CLAUDE.md`와 `README.md`는 보조 신호입니다. root `AGENTS.md` / `CODEX.md`가 없으면 진입점 부재로 감점합니다.

## B. AGENTS.md / Context Quality · /20

좋은 context는 짧고 실행 중심이어야 합니다.

| Sub | Points | Criteria |
|-----|--------|----------|
| Conciseness | 4 | context가 10-80 lines 수준으로 유지 |
| Quick Commands | 4 | test/lint/build/typecheck 명령이 복붙 가능 |
| Key Files | 4 | 실제 수정에 필요한 핵심 파일 경로 제시 |
| Non-Obvious Rules | 4 | gotcha, hidden rule, warning 명시 |
| Cross References | 4 | 관련 module/docs로 relative link 연결 |

## C. Local Development Workflow Clarity · /15

Codex가 로컬에서 작업을 끝낼 수 있는지 봅니다.

| Sub | Points | Criteria |
|-----|--------|----------|
| Entry points | 3 | 어디서 시작할지 명확 |
| Setup/install | 3 | bootstrap/install 명령 존재 |
| Verification commands | 3 | test/lint/build/typecheck 명시 |
| Known failures | 3 | flaky/slow/known failing tests 설명 |
| Done criteria | 3 | 완료 보고 전 확인할 evidence 기준 |

## D. Architecture & Dependency Mapping · /15

`ARCHITECTURE.md`, `docs/architecture.md`, Mermaid diagram, workspace graph files(`turbo.json`, `nx.json`, `pnpm-workspace.yaml`)를 봅니다. 변경 영향 범위를 추적할 수 있어야 합니다.

## E. Verification Gates & Testability · /20

| Sub | Points | Criteria |
|-----|--------|----------|
| Reference Accuracy | 5 | context가 언급한 path가 실제 존재 |
| Review Evidence | 4 | CODEOWNERS / PR template / review checklist |
| Task Validation | 8 | package/build/test infra + context에 검증 명령 |
| Agent Workflow Tests | 3 | evals/benchmarks/tests/agent 등 |

## F. Safety, Secrets & Change Boundaries · /10

Codex가 파일을 직접 수정하므로 안전 경계가 중요합니다.

- secrets/env 취급 규칙
- `.env.example` 또는 `.env.sample`
- `.gitignore`의 env/secrets 보호
- generated/vendor/migration file 주의사항
- destructive command 금지 또는 주의
- dirty worktree에서 사용자 변경 보존 규칙

## G. Agent Outcome Evidence · /5

Codex 작업 성공률, tool calls, completion time, rework rate, human clarification count, task pass rate 같은 측정 근거가 있는지 봅니다.

## ROI Actions

액션은 다음 형식을 씁니다.

- Effort: S (<1h), M (1-4h), L (4h+)
- Impact: task당 시간 절감, 검증 실패 감소, 사고 방지처럼 구체적으로 작성
- Priority: impact_score / effort_hours
