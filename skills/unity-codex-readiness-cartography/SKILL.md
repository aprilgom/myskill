---
name: unity-codex-readiness-cartography
description: Audits Unity projects for Codex-readiness using a 100-point rubric across Unity project navigation, AGENTS.md context quality, local Unity workflow clarity, scene/assembly architecture mapping, Unity verification gates, asset/package safety boundaries, and agent outcome evidence. Produces JSON score data, a professional HTML dashboard, and ROI-ranked actions. Trigger when the user asks whether a Unity project is ready for Codex, coding agents, AI coding workflows, "Unity Codex readiness", "Unity Codex-ready map", or wants a visual/actionable readiness report for a Unity repository.
---

# Unity Codex-Readiness Cartography

이 스킬은 Unity 프로젝트가 Codex로 안전하게 수정, 테스트, 검증, 완료 보고까지 가능한지 평가합니다. 일반 코드 레포 준비도에 더해 Unity 고유 구조(`Assets`, `Packages`, `ProjectSettings`, `.asmdef`, scene/prefab, EditMode/PlayMode 테스트, Unity 버전 고정)를 봅니다.
버전 관리는 Git과 Unity Version Control/Plastic SCM을 구분합니다. `.plastic/` 워크스페이스가 있으면 `cm status --header`, `ignore.conf`, changeset/checkin 규칙을 우선 평가하고, Git/GitHub 전용 파일을 요구하지 않습니다.

## Workflow

1. 대상 Unity repo를 정합니다. 사용자가 경로를 주지 않으면 현재 작업 디렉터리를 사용합니다.
2. 자동 채점 스크립트를 실행합니다.

```bash
python3 ~/.codex/skills/unity-codex-readiness-cartography/scripts/score.py <repo-path> \
  --json <output-path>/unity-codex-readiness-score.json
```

3. JSON을 바탕으로 `assets/template.html`을 복사해 dashboard를 채웁니다. 사용자가 경로를 지정하지 않으면 다음 우선순위를 씁니다.
   - repo에 `docs/`가 있으면 `docs/unity-codex-readiness-map.html`, `docs/unity-codex-readiness-score.json`
   - 없으면 repo root의 `unity-codex-readiness-map.html`, `unity-codex-readiness-score.json`
4. 브라우저에서 HTML을 열어 시각적으로 확인합니다. 사용자가 열지 말라고 하면 경로만 보고합니다.
5. 마지막 보고는 한국어로 짧게: 총점/등급, 최약점 1-2개, Top 3 ROI 액션, 생성 파일 경로.

## Output Format

마지막 보고는 다음 순서로 작성합니다.

- `총점/등급`: `<score>/100 · <grade>`
- `최약점`: 가장 낮은 카테고리 1-2개와 핵심 근거
- `Top 3 ROI 액션`: `Effort`, `Impact`, `Priority` 포함
- `Unity 안전 경계`: generated dirs 제외 여부, 외부 애셋 경계 누락 여부, `.meta`/ProjectSettings/package lock 주의사항
- `생성 파일`: JSON과 HTML dashboard 경로

## Rubric

총 100점입니다. 자세한 기준은 필요할 때 `references/scoring-rubric.md`를 읽습니다.

| Cat | Name | Points |
|-----|------|--------|
| A | Unity Navigation & Scope Coverage | 15 |
| B | AGENTS.md / Unity Context Quality | 20 |
| C | Local Unity Workflow Clarity | 15 |
| D | Scene, Assembly & Dependency Mapping | 15 |
| E | Unity Verification Gates & Testability | 20 |
| F | Asset, Package & Secret Safety Boundaries | 10 |
| G | Agent Outcome Evidence | 5 |

등급:
- 90-100: Codex-Native
- 75-89: Codex-Ready
- 60-74: Codex-Assisted
- 40-59: Codex-Fragile
- <40: Codex-Hostile

## What The Script Checks

- Unity project root: `Assets/`, `Packages/manifest.json`, `ProjectSettings/ProjectVersion.txt`
- VCS: `.plastic/` + `cm` + `ignore.conf` 또는 `.git/` + `.gitignore`를 감지해 각 스택에 맞는 branch/review/ignore evidence 평가
- 핵심 module: `Assets/*`, `Assets/Scripts/*`, `Assets/Scenes`, `Assets/Prefabs`, `Packages/*`
- Codex context: `AGENTS.md`, `CODEX.md` 우선, `CLAUDE.md`, `README.md`는 보조
- Unity context 품질: Unity version, editor/batchmode commands, scene/prefab ownership, asmdef/package refs, hidden rules
- local workflow: Unity install/version, package restore, EditMode/PlayMode tests, build command, known flaky/slow tests, done criteria
- architecture: `ARCHITECTURE.md`, `docs/architecture.md`, Mermaid, `.asmdef`, scene flow, package dependency map
- verification: path reference accuracy, Unity Test Framework, CI/batchmode 또는 Unity Version Control checkin evidence, agent evals
- safety: `.meta` files, generated `Library/Temp/Obj/Builds` exclusion, external asset/vendor boundaries, Addressables/build artifacts, secrets/env handling in `.gitignore` or `ignore.conf`, destructive command cautions
- outcomes: agent evals, benchmark results, telemetry/task metrics hints

## Unity Boundary Rules

- `Library/`, `Temp/`, `Obj/`, `Build/`, `Builds/`, `Logs/`, `UserSettings/`는 검증 대상이 아니라 재생성 산출물로 제외합니다.
- `Assets/Plugins`, `Assets/ThirdParty`, `Assets/Vendor`, `Assets/AssetStoreTools`, `Assets/AddressableAssetsData`, `Assets/StreamingAssets`는 외부 애셋 또는 런타임 데이터 후보로 보고 경계 문서가 없으면 Safety finding을 냅니다.
- `Packages/<name>/package.json`이 있는 폴더는 local package로 분석 대상입니다. `Packages/manifest.json`과 `Packages/packages-lock.json`은 의존성 계약으로 보고 의도 없는 변경 위험을 표시합니다.
- `.meta` 파일은 GUID 보존 대상입니다. 삭제/재생성/대량 포맷팅을 권장하지 않습니다.

## Style

- Dashboard는 전문 기술 대시보드 톤으로 작성합니다.
- light surface, Inter + JetBrains Mono, blue/green/amber/red accents를 유지합니다.
- 판타지 지도, 이모지 장식, 과도한 은유는 쓰지 않습니다.
- ROI 액션은 `Effort`, `Impact`, `Priority`가 보이게 작성합니다.

## Files

- `scripts/score.py` - Unity Codex-readiness 자동 채점기, Python stdlib only
- `references/scoring-rubric.md` - 상세 루브릭
- `assets/template.html` - HTML 대시보드 출발 템플릿
