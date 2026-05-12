---
name: github-monetization-cartography
description: Evaluate whether a GitHub repository has enough observable repository evidence to support a revenue experiment or monetization path. Use for GitHub repo monetization checks, open-source monetization readiness, repo-to-business feasibility, paid OSS support potential, GitHub Marketplace readiness, sponsor/SaaS/plugin monetization review, and "can this repo make money?" questions limited to repository evidence. Produces a 100-point score, JSON, HTML dashboard, and ROI-ranked revenue experiments. Do not use for VC investment recommendations, company valuation, tax/legal advice, or broad startup diligence.
---

# GitHub Monetization Cartography

This skill evaluates whether a GitHub repository contains enough evidence to support a monetization experiment. It is repository-evidence first: scripts collect observable signals from files, package metadata, docs, examples, issue templates, release notes, sponsorship files, and optional exported GitHub metadata. Do not treat stars, forks, or downloads as revenue proof.

## Workflow

1. Identify the target repository path. If the user gives a GitHub URL, clone or fetch it only if the user has asked you to evaluate that repo and network access is available. If no path is provided, use the current working directory.
2. Run the repository evidence scanner.

```bash
python3 <skill-dir>/scripts/score.py <target-path> \
  --json <output-path>/github-monetization-score.json
```

3. If `manual_review_required` is true, read `references/github-monetization-rubric.md` and inspect the cited evidence paths. Manual review is mandatory when:
   - score is 70 or higher,
   - demand proxy signals are high but revenue proof is weak,
   - the repo has keyword-dense marketing text,
   - binary or unsupported files may contain pricing, customer, or traction evidence.
4. Render the HTML dashboard.

```bash
python3 <skill-dir>/scripts/render_dashboard.py \
  <output-path>/github-monetization-score.json \
  --template <skill-dir>/assets/template.html \
  --out <output-path>/github-monetization-map.html
```

5. Open the HTML dashboard when useful and verify score bars, evidence, risks, actions, and extraction gaps render correctly. If the user asks not to open it, report the file path only.
6. Final answer in the user's language by default. Keep it short: score/grade, 1-2 repo evidence findings, Top 3 revenue actions, generated paths.

Default output location:
- If the target has `docs/`, write to `docs/github-monetization-score.json` and `docs/github-monetization-map.html`.
- Otherwise write to the target root.
- If the user provides an output path, use that path.

## Expert Model

A competent GitHub monetization reviewer asks:

- Who is the buyer or budget owner, not just who is the developer user?
- Is repository activity a durable demand proxy or just curiosity?
- Can the project be packaged, supported, hosted, licensed, or distributed through a credible paid path?
- Is there any concrete price, paid user, contract, sponsor, pilot, billing, or conversion evidence?
- Would maintenance and support costs make the likely revenue path unattractive?

The scanner is an evidence collector, not an oracle. It may identify repo-native signals, but manual review must decide whether the repo supports a serious paid experiment.

## Rubric

Total score is 100 points:

| Cat | Name | Points |
|-----|------|--------|
| A | Buyer & Use Case Clarity | 15 |
| B | Demand Proxy Quality | 15 |
| C | Productization Readiness | 15 |
| D | Monetization Path Fit | 15 |
| E | Revenue Proof & Conversion Evidence | 15 |
| F | Maintenance Economics | 10 |
| G | Distribution Surface | 10 |
| H | Revenue Experiment Readiness | 5 |

Grades:
- 85-100: Repo Monetization-Ready
- 70-84: GitHub Revenue Experiment Ready
- 55-69: Monetization Hypothesis Formed
- 35-54: Repo Demand Evidence Thin
- <35: Not Yet Monetizable From Repo Evidence

## What The Script Checks

- Text files: `.md`, `.txt`, `.csv`, `.tsv`, `.json`, `.html`, `.yml`, `.yaml`, `.toml`, `.xml`
- Archive text: `.docx`, `.pptx`, `.xlsx`
- Repo metadata: package manifests, release/changelog files, issue templates, funding files, license files, docs, examples, demos
- Optional exported metadata files: files mentioning stars, forks, downloads, sponsors, dependents, issues, discussions, package download counts
- Buyer signals: buyer, ICP, persona, enterprise, teams, agency, compliance, procurement, developer platform users
- Demand proxies: stars, forks, downloads, dependents, issues, discussions, feature requests, adoption, integrations
- Productization: install, quickstart, docs, examples, demo, releases, semver, API, Docker, hosted deployment
- Monetization paths: hosted, cloud, SaaS, Pro, Enterprise, support, consulting, license, marketplace, plugin, sponsor
- Revenue proof: paid users, sponsors, Stripe, billing, pricing, contracts, pilots, MRR, ARR, conversion
- Maintenance economics: support load, issue backlog, churn, SLA, cost to serve, maintainers, dependency risk
- Distribution: GitHub Marketplace, package registries, integrations, SEO docs, website, partners
- Experiments: waitlist, landing page, checkout, sponsor tiers, trial, paid onboarding, next revenue test

## Output Rules

- Do not invent stars, downloads, customers, revenue, prices, conversion rates, or support cost.
- Stars, forks, and downloads are demand proxies only; they cannot satisfy revenue proof by themselves.
- High demand with no buyer, price, or conversion path must produce a risk and manual review note.
- Open-source popularity should not be treated as monetization readiness unless the repo shows packaging, distribution, or paid workflow evidence.
- Call out extraction gaps for binary, scanned, unsupported, or unreadable files.
- ROI actions must include `effort`, `impact`, and `priority`.

## Validation

Before reporting completion, run:

```bash
python3 -m py_compile <skill-dir>/scripts/score.py <skill-dir>/scripts/render_dashboard.py <skill-dir>/scripts/self_test.py
python3 <skill-dir>/scripts/self_test.py
python3 <skill-dir>/scripts/score.py <target-path> --json /tmp/github-monetization-score.json --markdown
python3 <skill-dir>/scripts/render_dashboard.py /tmp/github-monetization-score.json \
  --template <skill-dir>/assets/template.html \
  --out /tmp/github-monetization-map.html
```

Then verify `/tmp/github-monetization-map.html` is non-empty and contains no unresolved `{{PLACEHOLDER}}` tokens.

## Common Pitfalls

- Treating GitHub stars as willingness to pay.
- Scoring package downloads as revenue evidence without a buyer, price, or paid conversion path.
- Ignoring license, support burden, and hosted-service feasibility.
- Penalizing a repo for lacking VC-scale market proof; this skill only evaluates monetization experiment readiness.
- Letting generic code quality replace repo-to-revenue evidence.

## Output Format

```markdown
**Score**
<total>/100 - <grade>
Mode: GitHub repo evidence baseline + manual monetization review

**Repo Monetization Read**
1. <highest-impact finding with evidence path/metric>
2. <second finding, if material>

**Top Revenue Actions**
1. [<Effort>, priority <score>] <action> - <impact>
2. [<Effort>, priority <score>] <action> - <impact>
3. [<Effort>, priority <score>] <action> - <impact>

Generated: <github-monetization-score.json>, <github-monetization-map.html>
```

## Files

- `scripts/score.py` - GitHub repo monetization evidence scanner
- `scripts/render_dashboard.py` - fills `assets/template.html` from score JSON
- `scripts/self_test.py` - bundled smoke tests
- `references/github-monetization-rubric.md` - detailed scoring rubric
- `assets/template.html` - single-file dashboard template
