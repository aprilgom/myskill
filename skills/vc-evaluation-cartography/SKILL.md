---
name: vc-evaluation-cartography
description: Evaluate startup or venture investment opportunities from pitch decks, data rooms, investment memos, KPI exports, financial models, or diligence packets. Uses a 100-point VC rubric and produces JSON score data, an investment committee style HTML dashboard, and ROI-ranked diligence actions. Trigger for VC evaluation, startup assessment, investment memo scoring, pitch deck review, deal cartography, diligence dashboard, venture readiness, fundraising-readiness, or whether a startup is investable. Do not use for public-company valuation, stock analysis, M&A fairness opinions, credit underwriting, or legal diligence unless framed as venture investment review.
---

# VC Evaluation Cartography

이 스킬은 스타트업 투자 검토 자료를 VC 관점에서 구조적으로 평가합니다. 산출물은 JSON 점수표, 단일 HTML 대시보드, ROI 순 diligence 액션 리스트입니다. 재무/법률 조언이 아니라 투자 검토용 분석 산출물로 다룹니다.

## Workflow

1. 평가 대상을 정합니다. 사용자가 경로를 주지 않으면 현재 작업 디렉터리를 사용합니다.
2. 자동 스캐너를 실행해 자료실의 문서 신호와 1차 점수를 만듭니다.

```bash
python3 <skill-dir>/scripts/score.py <target-path> \
  --json <output-path>/vc-evaluation-score.json
```

3. 필요하면 `references/vc-rubric.md`를 읽고 자동 점수를 수동 보정합니다.
   - 자동 점수는 evidence baseline입니다.
   - 수동 보정은 시장의 실제 크기, 창업자-시장 적합도, 경쟁 역학, 투자 라운드 맥락처럼 텍스트 스캔만으로 판단하기 어려운 항목에만 적용합니다.
4. `render_dashboard.py`로 `assets/template.html`과 JSON 값을 합쳐 `vc-evaluation-map.html`을 만듭니다.

```bash
python3 <skill-dir>/scripts/render_dashboard.py \
  <output-path>/vc-evaluation-score.json \
  --template <skill-dir>/assets/template.html \
  --out <output-path>/vc-evaluation-map.html
```

5. HTML을 브라우저로 열어 점수, 카테고리 바, 핵심 리스크, diligence 액션이 렌더링되는지 확인합니다. 사용자가 열지 말라고 하면 경로만 보고합니다.
6. 마지막 보고는 한국어로 짧게 작성합니다: 총점/등급, 핵심 투자 논점 1-2개, Top 3 diligence 액션, 생성 파일 경로.

기본 저장 위치:
- 대상 폴더에 `docs/`가 있으면 `docs/vc-evaluation-map.html`, `docs/vc-evaluation-score.json`
- 없으면 대상 루트의 `vc-evaluation-map.html`, `vc-evaluation-score.json`
- 사용자가 명시한 출력 경로가 있으면 그 경로 우선

## Rubric

총 100점입니다. 자세한 기준은 필요할 때 `references/vc-rubric.md`를 읽습니다.

| Cat | Name | Points |
|-----|------|--------|
| A | Market Size & Timing | 15 |
| B | Problem Urgency & Customer Pain | 10 |
| C | Product, Technology & Roadmap | 10 |
| D | Traction & Customer Evidence | 15 |
| E | Business Model & Unit Economics | 10 |
| F | Go-to-Market & Distribution | 10 |
| G | Team & Founder-Market Fit | 10 |
| H | Financial Plan & Fundraising Fit | 10 |
| I | Moat, Competition & Defensibility | 5 |
| J | Key Risks & Diligence Gaps | 5 |

등급:
- 90-100: IC-Ready
- 75-89: Strong Diligence Candidate
- 60-74: Promising but Incomplete
- 40-59: High-Risk / Needs Evidence
- <40: Not Yet Investable

## What The Script Checks

- 대상 자료: `.md`, `.txt`, `.csv`, `.tsv`, `.json`, `.html`, `.pdf`, `.pptx`, `.docx`, `.xlsx` 파일명과 추출 가능한 텍스트
- market 신호: TAM/SAM/SOM, market growth, timing, regulatory or platform shifts
- customer/problem 신호: ICP, pain, workflow, ROI, interviews, LOI, pilots
- product 신호: demo, roadmap, architecture, IP, model, integrations, compliance
- traction 신호: ARR/MRR, revenue, growth, retention, churn, pipeline, customers, cohorts
- economics 신호: ACV, gross margin, CAC, LTV, payback, pricing
- GTM 신호: sales motion, channel, partner, funnel, conversion, sales cycle
- team 신호: founder background, hiring plan, advisors, domain expertise
- fundraising 신호: round, valuation, runway, burn, use of funds, milestones
- risk 신호: competition, dependency, concentration, legal, security, data gaps

## Output Rules

- Treat the script as an evidence collector, not an oracle.
- Prefer concrete document names, metric values, customer counts, and missing evidence over generic startup advice.
- Mark unknowns explicitly. Do not invent traction, market size, valuation, or customer names.
- Call out extraction gaps when binary PDFs, scans, images, or unsupported spreadsheets are present but text could not be read.
- ROI actions are diligence actions and must include `Effort`, `Impact`, and `Priority`.
- Keep the dashboard investment committee style: light surface, compact scorecards, simple bars/tables, no decorative map theme.

## Validation

Before reporting completion, run:

```bash
python3 -m py_compile <skill-dir>/scripts/score.py <skill-dir>/scripts/render_dashboard.py
python3 <skill-dir>/scripts/score.py <target-path> --json /tmp/vc-evaluation-score.json --markdown
python3 <skill-dir>/scripts/render_dashboard.py /tmp/vc-evaluation-score.json \
  --template <skill-dir>/assets/template.html \
  --out /tmp/vc-evaluation-map.html
```

Then verify `/tmp/vc-evaluation-map.html` is non-empty and contains no unresolved `{{PLACEHOLDER}}` tokens.

## Common Pitfalls

- Do not treat a high score as an investment recommendation. It means available evidence is strong enough for the next review step.
- Do not score scanned PDFs as missing business evidence without saying text extraction failed.
- Do not let filename hints override missing content for critical categories such as traction, unit economics, and fundraising fit.
- Do not use this for broad finance analysis unless the target is a venture-backed startup or startup investment opportunity.

## Output Format

Use this final report shape unless the user asks for something else:

```markdown
**Score**
<total>/100 - <grade>
Mode: heuristic baseline + manual VC review

**Key Findings**
1. <highest-impact investment finding with evidence path/metric>
2. <second finding, if material>

**Top Diligence Actions**
1. [<Effort>, priority <score>] <action> - <impact>
2. [<Effort>, priority <score>] <action> - <impact>
3. [<Effort>, priority <score>] <action> - <impact>

Generated: <vc-evaluation-score.json>, <vc-evaluation-map.html>
```

## Files

- `scripts/score.py` - VC evidence scanner and baseline scorer, Python stdlib only
- `scripts/render_dashboard.py` - fills `assets/template.html` from `vc-evaluation-score.json`
- `references/vc-rubric.md` - detailed scoring rubric
- `assets/template.html` - single-file dashboard template
