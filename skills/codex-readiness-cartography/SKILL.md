---
name: codex-readiness-cartography
description: Audits any repository for Codex-readiness using a 100-point rubric across Codex navigation, AGENTS.md/context quality, local development workflow clarity, architecture mapping, verification gates, safety boundaries, and agent outcome evidence. Produces JSON score data, a professional HTML dashboard, and ROI-ranked actions. Trigger when the user asks whether a repo is ready for Codex, coding agents, agentic coding, AI coding workflows, "Codex readiness", "Codex-ready map", "agent-friendly repo audit", or wants a visual/actionable readiness report for Codex.
---

# Codex-Readiness Cartography

이 스킬은 레포가 Codex로 안전하게 수정, 테스트, 검증, 완료 보고까지 가능한지 평가합니다. 산출물은 JSON 점수표, 단일 HTML 대시보드, ROI 순 액션 리스트입니다.

## Workflow

1. 대상 repo를 정합니다. 사용자가 경로를 주지 않으면 현재 작업 디렉터리를 사용합니다.
2. 자동 채점 스크립트를 실행합니다.

```bash
python3 ~/.codex/skills/codex-readiness-cartography/scripts/score.py <repo-path> \
  --json <output-path>/codex-readiness-score.json
```

3. JSON을 바탕으로 `assets/template.html`을 복사해 dashboard를 채웁니다. 사용자가 경로를 지정하지 않으면 다음 우선순위를 씁니다.
   - repo에 `docs/`가 있으면 `docs/codex-readiness-map.html`, `docs/codex-readiness-score.json`
   - 없으면 repo root의 `codex-readiness-map.html`, `codex-readiness-score.json`
4. 브라우저에서 HTML을 열어 시각적으로 확인합니다. 사용자가 열지 말라고 하면 경로만 보고합니다.
5. 마지막 보고는 한국어로 짧게: 총점/등급, 최약점 1-2개, Top 3 ROI 액션, 생성 파일 경로.

## Rubric

총 100점입니다. 자세한 기준은 필요할 때 `references/scoring-rubric.md`를 읽습니다.

| Cat | Name | Points |
|-----|------|--------|
| A | Codex Navigation & Scope Coverage | 15 |
| B | AGENTS.md / Context Quality | 20 |
| C | Local Development Workflow Clarity | 15 |
| D | Architecture & Dependency Mapping | 15 |
| E | Verification Gates & Testability | 20 |
| F | Safety, Secrets & Change Boundaries | 10 |
| G | Agent Outcome Evidence | 5 |

등급:
- 90-100: Codex-Native
- 75-89: Codex-Ready
- 60-74: Codex-Assisted
- 40-59: Codex-Fragile
- <40: Codex-Hostile

## What The Script Checks

- 핵심 module: repo root의 코드 디렉터리와 `apps/*`, `packages/*`, `services/*`
- Codex context: `AGENTS.md`, `CODEX.md` 우선, `CLAUDE.md`, `README.md`는 보조
- context 품질: 길이, quick commands, key file refs, hidden rules, cross-links
- local workflow: setup/install, test/lint/build/typecheck, known failures, done criteria
- architecture: `ARCHITECTURE.md`, `docs/architecture.md`, Mermaid, workspace graph files
- verification: path reference accuracy, CI/build/test infra, CODEOWNERS, PR template, evals
- safety: secrets/env handling, generated/vendor/migration boundaries, destructive command cautions
- outcomes: agent evals, benchmark results, telemetry/task metrics hints

## Style

- Dashboard는 전문 기술 대시보드 톤으로 작성합니다.
- light surface, Inter + JetBrains Mono, blue/green/amber/red accents를 유지합니다.
- 판타지 지도, 이모지 장식, 과도한 은유는 쓰지 않습니다.
- ROI 액션은 `Effort`, `Impact`, `Priority`가 보이게 작성합니다.

## Files

- `scripts/score.py` - Codex-readiness 자동 채점기, Python stdlib only
- `references/scoring-rubric.md` - 상세 루브릭
- `assets/template.html` - HTML 대시보드 출발 템플릿
