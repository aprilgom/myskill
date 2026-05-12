# Unity Codex-Ready Project Rubric · v1 (100 pt)

이 루브릭은 "Codex가 이 Unity repo에서 안전하게 C# 코드, scene/prefab 관련 파일, packages, project settings를 변경하고 검증할 수 있는가"를 평가합니다. 게임 품질 자체보다 agent 작업성, Unity 재현성, 검증성, 안전 경계를 봅니다.

| Cat | Name | Points |
|-----|------|--------|
| A | Unity Navigation & Scope Coverage | 15 |
| B | AGENTS.md / Unity Context Quality | 20 |
| C | Local Unity Workflow Clarity | 15 |
| D | Scene, Assembly & Dependency Mapping | 15 |
| E | Unity Verification Gates & Testability | 20 |
| F | Asset, Package & Secret Safety Boundaries | 10 |
| G | Agent Outcome Evidence | 5 |

## A. Unity Navigation & Scope Coverage · /15

핵심 Unity 영역마다 `AGENTS.md` 또는 `CODEX.md` 같은 Codex-native context가 있는지 봅니다. root `AGENTS.md` / `CODEX.md`가 없으면 진입점 부재로 감점합니다. 핵심 영역은 `Assets/*`, `Assets/Scripts/*`, `Assets/Scenes`, `Assets/Prefabs`, local package를 포함합니다.

## B. AGENTS.md / Unity Context Quality · /20

좋은 Unity context는 짧고 실행 중심이어야 합니다.

| Sub | Points | Criteria |
|-----|--------|----------|
| Conciseness | 4 | context가 10-100 lines 수준으로 유지 |
| Quick Commands | 4 | Unity batchmode, EditMode/PlayMode test, build 명령이 복붙 가능 |
| Key Files | 4 | 실제 수정에 필요한 scene/prefab/script/asmdef/package 경로 제시 |
| Unity Rules | 4 | `.meta`, serialization, scene ownership, generated dirs, package lock 같은 Unity gotcha 명시 |
| Cross References | 4 | 관련 module/docs/scene/package로 relative link 연결 |

## C. Local Unity Workflow Clarity · /15

Codex가 로컬에서 작업을 끝낼 수 있는지 봅니다.

| Sub | Points | Criteria |
|-----|--------|----------|
| Entry points | 3 | 시작 scene, bootstrap, gameplay/editor 진입점 명확 |
| Setup/install | 3 | Unity version, Hub/editor path, package restore 절차 존재 |
| Verification commands | 3 | EditMode/PlayMode/build/batchmode 명령 명시 |
| Known failures | 3 | flaky/slow/known failing tests, platform-specific caveat 설명 |
| Done criteria | 3 | 완료 보고 전 evidence 기준, screenshots/logs/artifacts 기준 |

## D. Scene, Assembly & Dependency Mapping · /15

`ARCHITECTURE.md`, `docs/architecture.md`, Mermaid diagram, `.asmdef`, scene flow, package dependency map을 봅니다. 변경 영향 범위를 scene, prefab, assembly, package 단위로 추적할 수 있어야 합니다.

## E. Unity Verification Gates & Testability · /20

| Sub | Points | Criteria |
|-----|--------|----------|
| Reference Accuracy | 5 | context가 언급한 path가 실제 존재 |
| Review Evidence | 4 | CODEOWNERS / PR template / review checklist |
| Unity Validation | 8 | Unity Test Framework, EditMode/PlayMode tests, CI batchmode, build method |
| Agent Workflow Tests | 3 | evals/benchmarks/tests/agent 등 |

## F. Asset, Package & Secret Safety Boundaries · /10

Codex가 Unity 파일을 직접 수정하므로 안전 경계가 중요합니다.

- `.meta` 파일 보존 규칙
- `Library/`, `Temp/`, `Obj/`, `Build/`, `Builds/`, `Logs/`, `UserSettings/` 제외
- `Assets/Plugins`, `Assets/ThirdParty`, `Assets/Vendor`, `Assets/AssetStoreTools` 같은 외부 애셋 후보의 수정 가능/금지/주의 경계
- `Assets/AddressableAssetsData`, `Assets/StreamingAssets` 같은 런타임 데이터와 build artifact 경계
- `ProjectSettings/`, `Packages/manifest.json`, `packages-lock.json` 변경 주의
- scene/prefab YAML serialization 충돌 주의
- secrets/env 취급 규칙
- destructive command 금지 또는 주의
- dirty worktree에서 사용자 변경 보존 규칙

## G. Agent Outcome Evidence · /5

Codex 작업 성공률, Unity test pass rate, build time, scene smoke test result, tool calls, completion time, rework rate, human clarification count 같은 측정 근거가 있는지 봅니다.

## ROI Actions

액션은 다음 형식을 씁니다.

- Effort: S (<1h), M (1-4h), L (4h+)
- Impact: task당 시간 절감, Unity 검증 실패 감소, asset/package 사고 방지처럼 구체적으로 작성
- Priority: impact_score / effort_hours
