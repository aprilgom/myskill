---
name: architecture-cartography
description: Audit, evaluate, review, map, or score a software repository folder's technical architecture; use for architecture quality reviews, module boundary analysis, dependency/coupling hotspots, API/data contract clarity, runtime/deployment shape, testability/change isolation, architecture documentation, evolution risk, high-ROI architecture improvements, and architecture-score.json or architecture-map.html dashboards.
---

# Architecture Cartography

이 스킬은 레포지토리의 기술 아키텍처를 구조적으로 평가합니다. 산출물은 JSON 점수표, 단일 HTML 대시보드, ROI 순 액션 리스트입니다.

## Workflow

1. 대상 repo를 정합니다. 사용자가 경로를 주지 않으면 현재 작업 디렉터리를 사용합니다.
2. 자동 스캐너를 실행해 구조 신호와 1차 점수를 만듭니다.

```bash
python3 <skill-dir>/scripts/score.py <repo-path> \
  --json <output-path>/architecture-score.json
```

3. 필요하면 `references/architecture-rubric.md`를 읽고 자동 점수를 수동 보정합니다.
   - 자동 점수는 증거 baseline입니다.
   - 수동 보정은 coupling 의도, 도메인 경계, runtime trade-off, legacy constraints처럼 코드 스캔만으로 판단하기 어려운 항목에만 적용합니다.
4. `render_dashboard.py`로 `assets/template.html`과 JSON 값을 합쳐 `architecture-map.html`을 만듭니다. 사용자가 출력 경로를 지정하지 않으면:
   - repo에 `docs/`가 있으면 `docs/architecture-map.html`, `docs/architecture-score.json`
   - 없으면 repo root의 `architecture-map.html`, `architecture-score.json`

```bash
python3 <skill-dir>/scripts/render_dashboard.py \
  <output-path>/architecture-score.json \
  --template <skill-dir>/assets/template.html \
  --out <output-path>/architecture-map.html
```

5. HTML을 브라우저로 열어 대시보드가 깨지지 않는지 확인합니다. 최소 확인 항목은 점수, 카테고리 바, 리스크 테이블, ROI 액션 테이블이 모두 렌더링되고 `{{PLACEHOLDER}}`가 남지 않는 것입니다. 사용자가 열지 말라고 하면 경로만 보고합니다.
   - 브라우저 확인 도구를 사용할 수 없으면 생성된 HTML에서 `{{` 또는 `}}` 잔여 placeholder가 없는지, 핵심 섹션 텍스트가 있는지 정적으로 확인하고 한계를 보고합니다.
6. 마지막 보고는 한국어로 짧게 작성합니다: 총점/등급, 핵심 리스크 1-2개, Top 3 ROI 액션, 생성 파일 경로.

## Trigger Boundaries

Use this skill for repository-level architecture understanding and change-risk prioritization. Do not use it as the primary skill for general code review, security audits, frontend performance/Core Web Vitals, accessibility, Codex-readiness, or skill quality evaluation unless the user's request explicitly frames those topics as architecture concerns.

## Rubric

총 100점입니다. 자세한 기준은 필요할 때 `references/architecture-rubric.md`를 읽습니다.

| Cat | Name | Points |
|-----|------|--------|
| A | Module Boundaries & Ownership | 20 |
| B | Dependency Direction & Coupling | 20 |
| C | API & Data Contract Clarity | 15 |
| D | Runtime & Deployment Shape | 10 |
| E | Testability & Change Isolation | 15 |
| F | Architecture Documentation & Decisions | 10 |
| G | Evolution Risk & Complexity Hotspots | 10 |

등급:
- 90-100: Architecture-Native
- 75-89: Architecture-Ready
- 60-74: Architecture-Assisted
- 40-59: Architecture-Fragile
- <40: Architecture-Hostile

## What The Script Checks

- repo layout: top-level modules, `apps/*`, `packages/*`, `services/*`, `libs/*`
- language/framework hints: package manifests, build files, config files, source extensions
- dependency signals: TypeScript/JavaScript, Python, Go, Rust, Java/Kotlin/C# import/use patterns
- coupling hotspots: high fan-in/fan-out files, cross-layer imports, relative import depth
- contracts: OpenAPI/GraphQL/protobuf/schema files, database migrations, typed model locations
- runtime shape: Docker, compose, Kubernetes, Terraform, serverless, Procfile, CI deploy hints
- testability: test file placement, test-to-source ratio, integration/e2e markers
- docs: `ARCHITECTURE.md`, `docs/architecture*`, ADRs, Mermaid diagrams
- risk: large files, mixed concern names, config sprawl, generated/vendor boundaries

## Output Rules

- Treat the script as an evidence collector, not an oracle.
- Prefer concrete file paths, counts, and dependency examples over generic architecture advice.
- ROI actions must include `Effort`, `Impact`, and `Priority`.
- Do not recommend rewrites unless smaller boundary, contract, or testability actions cannot address the risk.
- Keep the dashboard a restrained technical report: light surface, compact cards, simple bars/tables, no decorative map theme.

## Output Format

Use this final report shape unless the user asks for something else:

```markdown
**Score**
<total>/100 - <grade>
Mode: heuristic baseline + manual architecture review

**Key Findings**
1. <highest-risk architecture finding with evidence path/count>
2. <second finding, if material>

**Top ROI Actions**
1. [<Effort>, priority <score>] <action> - <impact>
2. [<Effort>, priority <score>] <action> - <impact>
3. [<Effort>, priority <score>] <action> - <impact>

Generated: <architecture-score.json>, <architecture-map.html>
```

## Files

- `scripts/score.py` - architecture signal scanner and baseline scorer, Python stdlib only
- `scripts/render_dashboard.py` - fills `assets/template.html` from `architecture-score.json`
- `references/architecture-rubric.md` - detailed scoring rubric
- `assets/template.html` - single-file dashboard template
