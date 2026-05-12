---
name: mission-cartography
description: Evaluate whether a project, product, startup, nonprofit, internal initiative, README, pitch packet, strategy memo, roadmap, or documentation set has a clear and actionable mission. Produces a 100-point mission clarity score, JSON score data, a single-file HTML dashboard, and ROI-ranked alignment actions. Trigger for mission clarity, mission alignment, north star, product purpose, founder narrative, strategic focus, positioning consistency, or whether a project's mission is clear. Do not use for brand copywriting alone, legal nonprofit compliance, public-company strategy advice, or investment recommendations unless the user only wants mission evidence and alignment.
---

# Mission Cartography

This skill evaluates whether a target has a mission that is clear, evidence-backed, aligned with the product or work, and useful for strategic trade-offs. Outputs are JSON score data, a single-file HTML dashboard, and ROI-ranked mission alignment actions.

## Workflow

1. 평가 대상을 정합니다. 사용자가 경로를 주지 않으면 현재 작업 디렉터리를 사용합니다.
2. 자동 스캐너를 실행해 mission clarity와 alignment 신호의 1차 점수를 만듭니다.

```bash
python3 <skill-dir>/scripts/score.py <target-path> \
  --json <output-path>/mission-score.json
```

3. 필요하면 `references/mission-rubric.md`를 읽고 자동 점수를 수동 보정합니다.
   - 자동 점수는 evidence baseline입니다.
   - 수동 보정은 실제 사용자 pain의 진위, founder intent, 전략적 차별성, 조직 내 trade-off 사용성처럼 문서 스캔만으로 판단하기 어려운 항목에만 적용합니다.
   - mission 문구가 그럴듯하지만 대상 사용자, 문제 증거, 제품/로드맵 연결, 측정 지표가 약하면 manual review gap으로 남깁니다.
4. `render_dashboard.py`로 `assets/template.html`과 JSON 값을 합쳐 `mission-map.html`을 만듭니다.

```bash
python3 <skill-dir>/scripts/render_dashboard.py \
  <output-path>/mission-score.json \
  --template <skill-dir>/assets/template.html \
  --out <output-path>/mission-map.html
```

5. HTML을 브라우저로 열어 점수, 카테고리 바, mission findings, ROI actions, evidence notes가 렌더링되는지 확인합니다. 사용자가 열지 말라고 하면 경로만 보고합니다.
6. Write the final report in the user's language by default. Keep it short: score/grade, 1-2 mission findings, Top 3 alignment actions, generated file paths.

기본 저장 위치:
- 대상 폴더에 `docs/`가 있으면 `docs/mission-map.html`, `docs/mission-score.json`
- 없으면 대상 루트의 `mission-map.html`, `mission-score.json`
- 사용자가 명시한 출력 경로가 있으면 그 경로 우선

## Expert Model

A strong mission reviewer behaves like a founder-PM, product strategist, and skeptical external reviewer at once. They inspect the mission statement first, then test whether it names a real audience, a concrete problem, an intended change, the product or operating choices that support it, and the measurements that would prove progress.

The main decision is whether the mission is strong enough to guide product, roadmap, positioning, and organizational trade-offs. A polished slogan is weak evidence unless it is backed by user/problem evidence and repeated consistently across the artifacts that shape execution.

## Rubric

총 100점입니다. 자세한 기준은 `references/mission-rubric.md`를 읽습니다.

| Cat | Name | Points |
|-----|------|--------|
| A | Mission Clarity & Specificity | 18 |
| B | Audience & Stakeholder Definition | 14 |
| C | Problem Evidence & Urgency | 16 |
| D | Product & Roadmap Alignment | 18 |
| E | Strategic Trade-off Power | 12 |
| F | Measurement & Feedback Loops | 12 |
| G | Narrative Consistency Across Artifacts | 10 |

등급:
- 90-100: Mission-Led
- 75-89: Mission-Aligned
- 60-74: Mission-Formed
- 40-59: Mission-Fragile
- <40: Mission-Drifting

## What The Script Checks

- 대상 자료: `.md`, `.txt`, `.csv`, `.tsv`, `.json`, `.html`, `.pdf`, `.docx`, `.pptx`, `.xlsx` 파일명과 추출 가능한 텍스트
- mission 신호: mission, purpose, vision, north star, why we exist, intended change, outcome
- audience 신호: target user, customer, stakeholder, beneficiary, persona, segment, buyer
- problem 신호: pain, problem, urgency, unmet need, evidence, interview, research, complaint, risk
- product alignment 신호: roadmap, feature, priority, use case, workflow, value proposition, scope
- trade-off 신호: principles, not doing, focus, prioritization, strategy, decision criteria, constraints
- measurement 신호: KPI, metric, OKR, north-star metric, feedback loop, retention, adoption, success criteria
- consistency 신호: mission-like statements repeated across README, docs, pitch, roadmap, website, strategy files

## Output Rules

- Treat the script as an evidence collector, not an oracle.
- Prefer concrete mission statements, artifact names, repeated phrasing, user segments, problem evidence, roadmap links, and metric names over generic strategy advice.
- Mark unknowns explicitly. Do not invent users, customer research, metrics, strategy, founder intent, or product plans.
- Do not overcredit broad inspirational language. A slogan without audience, problem, product alignment, and measurement should score low or require manual review.
- Report extraction gaps when binary PDFs, scans, images, or unsupported files could contain mission evidence but text could not be read.
- ROI actions are mission alignment actions and must include `Effort`, `Impact`, and `Priority`.
- Keep the dashboard decision-oriented: light surface, compact scorecards, simple bars/tables, no decorative map theme.

## Validation

Before reporting completion, run:

```bash
python3 -m py_compile <skill-dir>/scripts/score.py <skill-dir>/scripts/render_dashboard.py <skill-dir>/scripts/self_test.py
python3 <skill-dir>/scripts/self_test.py
python3 <skill-dir>/scripts/score.py <target-path> --json /tmp/mission-score.json --markdown
python3 <skill-dir>/scripts/render_dashboard.py /tmp/mission-score.json \
  --template <skill-dir>/assets/template.html \
  --out /tmp/mission-map.html
```

Then verify `/tmp/mission-map.html` is non-empty and contains no unresolved `{{PLACEHOLDER}}` tokens.

## Common Pitfalls

- Treating a polished tagline as a clear mission.
- Counting generic words like “impact”, “empower”, or “transform” as strong evidence by themselves.
- Scoring mission clarity without checking whether the product, roadmap, and metrics reinforce it.
- Penalizing unreadable PDFs or image-based decks as missing evidence without reporting extraction failure.
- Rewriting the mission for the user instead of mapping evidence, risks, and next actions.
- Drifting into VC investability, brand copy critique, or legal nonprofit advice.

## Output Format

Use this final report shape unless the user asks for something else:

```markdown
**Score**
<total>/100 - <grade>
Mode: heuristic baseline + manual mission review

**Mission Read**
1. <highest-impact mission finding with evidence path/count>
2. <second finding, if material>

**Top Alignment Actions**
1. [<Effort>, priority <score>] <action> - <impact>
2. [<Effort>, priority <score>] <action> - <impact>
3. [<Effort>, priority <score>] <action> - <impact>

Generated: <mission-score.json>, <mission-map.html>
```

## Files

- `scripts/score.py` - mission evidence scanner and baseline scorer, Python stdlib only
- `scripts/render_dashboard.py` - fills `assets/template.html` from `mission-score.json`
- `scripts/self_test.py` - bundled smoke tests for scorer and renderer
- `references/mission-rubric.md` - detailed scoring rubric
- `assets/template.html` - single-file dashboard template
