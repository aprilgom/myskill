---
name: monetization-cartography
description: Assess whether a project, product, repo, README, pitch packet, KPI export, pricing page, customer research, or business memo has enough evidence to be monetized. Produces a 100-point monetization-readiness score, JSON, HTML dashboard, and ROI-ranked revenue experiments. Trigger for monetization checks, revenue potential, pricing readiness, paid user evidence, business model viability, or whether a project can make money. Do not use for VC investment recommendations, public-company valuation, tax/legal advice, or broad startup diligence unless the user only wants monetization feasibility.
---

# Monetization Cartography

This skill evaluates whether a project has enough evidence to monetize. Outputs are JSON score data, a single-file HTML dashboard, and ROI-ranked revenue actions. Do not treat it as investment, valuation, legal, or tax advice.

## Workflow

1. 평가 대상을 정합니다. 사용자가 경로를 주지 않으면 현재 작업 디렉터리를 사용합니다.
2. 자동 스캐너를 실행해 프로젝트 문서의 수익화 신호와 1차 점수를 만듭니다.

```bash
python3 <skill-dir>/scripts/score.py <target-path> \
  --json <output-path>/monetization-score.json
```

3. 필요하면 `references/monetization-rubric.md`를 읽고 자동 점수를 수동 보정합니다.
   - 자동 점수는 evidence baseline입니다.
   - 수동 보정은 실제 구매자 맥락, 가격 민감도, 경쟁 대체재, 유통 제약처럼 텍스트 스캔만으로 판단하기 어려운 항목에만 적용합니다.
   - `manual_review_required`가 true이거나 점수가 높거나 키워드가 과밀하면 evidence path와 buyer/price/revenue proof를 확인합니다.
4. `render_dashboard.py`로 `assets/template.html`과 JSON 값을 합쳐 `monetization-map.html`을 만듭니다.

```bash
python3 <skill-dir>/scripts/render_dashboard.py \
  <output-path>/monetization-score.json \
  --template <skill-dir>/assets/template.html \
  --out <output-path>/monetization-map.html
```

5. HTML을 브라우저로 열어 점수, 카테고리 바, 핵심 리스크, 수익화 액션이 렌더링되는지 확인합니다. 사용자가 열지 말라고 하면 경로만 보고합니다.
6. Write the final report in the user's language by default. Use Korean only when requested or clearly implied. Keep it short: score/grade, 1-2 monetization findings, Top 3 revenue actions, generated file paths.

기본 저장 위치:
- 대상 폴더에 `docs/`가 있으면 `docs/monetization-map.html`, `docs/monetization-score.json`
- 없으면 대상 루트의 `monetization-map.html`, `monetization-score.json`
- 사용자가 명시한 출력 경로가 있으면 그 경로 우선

## Rubric

총 100점입니다. 자세한 기준은 필요할 때 `references/monetization-rubric.md`를 읽습니다.

| Cat | Name | Points |
|-----|------|--------|
| A | Customer & Buyer Clarity | 15 |
| B | Pain Severity & Willingness To Pay | 15 |
| C | Pricing & Packaging | 15 |
| D | Revenue Evidence & Traction | 15 |
| E | Unit Economics & Margin | 15 |
| F | Distribution & Conversion Path | 15 |
| G | Revenue Experiment Readiness | 10 |

등급:
- 85-100: Monetization-Ready
- 70-84: Revenue Experiment Ready
- 55-69: Monetization Hypothesis Formed
- 35-54: Revenue Evidence Thin
- <35: Not Yet Monetizable

## What The Script Checks

- 대상 자료: `.md`, `.txt`, `.csv`, `.tsv`, `.json`, `.html`, `.pdf`, `.pptx`, `.docx`, `.xlsx` 파일명과 추출 가능한 텍스트
- customer 신호: ICP, buyer, persona, segment, customer, user
- WTP 신호: pain, urgency, ROI, budget, LOI, paid pilot, customer interviews
- pricing 신호: pricing, subscription, monthly, annual, seat, package, starter/team/enterprise
- revenue 신호: MRR, ARR, paid customers, contracts, pilots, retention, conversion
- economics 신호: CAC, LTV, payback, gross margin, cost to serve, churn, ACV
- distribution 신호: channel, marketplace, partner, funnel, sales, trial, conversion
- experiment 신호: checkout, billing, Stripe, preorder, landing page, onboarding, next test

## Output Rules

- Treat the script as an evidence collector, not an oracle.
- Prefer concrete document names, metric values, buyer segments, price points, and experiment names over generic business advice.
- Mark unknowns explicitly. Do not invent customers, revenue, price points, conversion rates, or margin.
- Mandatory manual review is required for high scores, keyword-dense targets, or missing core proof signals.
- Call out extraction gaps when binary PDFs, scans, images, or unsupported spreadsheets are present but text could not be read.
- ROI actions are revenue actions and must include `Effort`, `Impact`, and `Priority`.
- Keep the dashboard decision-oriented: light surface, compact scorecards, simple bars/tables, no decorative map theme.

## Validation

Before reporting completion, run:

```bash
python3 -m py_compile <skill-dir>/scripts/score.py <skill-dir>/scripts/render_dashboard.py <skill-dir>/scripts/self_test.py
python3 <skill-dir>/scripts/self_test.py
python3 <skill-dir>/scripts/score.py <target-path> --json /tmp/monetization-score.json --markdown
python3 <skill-dir>/scripts/render_dashboard.py /tmp/monetization-score.json \
  --template <skill-dir>/assets/template.html \
  --out /tmp/monetization-map.html
```

Then verify `/tmp/monetization-map.html` is non-empty and contains no unresolved `{{PLACEHOLDER}}` tokens.

## Common Pitfalls

- Do not answer “yes, it can make money” from a high score alone. Say the evidence supports a revenue experiment or monetization review.
- Do not drift into VC investability. This skill ignores team fundraising fit, valuation, fund strategy, and exit outcomes unless they directly affect monetization.
- Do not treat open-source stars, downloads, or traffic as revenue evidence unless there is a buyer, price, or conversion path.
- Do not punish a project for missing venture-scale market data; this rubric asks whether it can monetize, not whether it can become a fund-returning company.
- Do not score scanned PDFs as missing evidence without saying text extraction failed.

## Output Format

Use this final report shape unless the user asks for something else:

```markdown
**Score**
<total>/100 - <grade>
Mode: heuristic baseline + manual monetization review

**Monetization Read**
1. <highest-impact revenue finding with evidence path/metric>
2. <second finding, if material>

**Top Revenue Actions**
1. [<Effort>, priority <score>] <action> - <impact>
2. [<Effort>, priority <score>] <action> - <impact>
3. [<Effort>, priority <score>] <action> - <impact>

Generated: <monetization-score.json>, <monetization-map.html>
```

## Files

- `scripts/score.py` - monetization evidence scanner and baseline scorer, Python stdlib only
- `scripts/render_dashboard.py` - fills `assets/template.html` from `monetization-score.json`
- `scripts/self_test.py` - bundled smoke tests for scorer and renderer
- `references/monetization-rubric.md` - detailed scoring rubric
- `assets/template.html` - single-file dashboard template
