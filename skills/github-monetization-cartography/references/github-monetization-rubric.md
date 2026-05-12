# GitHub Monetization Rubric

## Target

A GitHub repository, local clone, source export, or repo evidence bundle.

## Decision

The score supports one decision: whether repo evidence is strong enough to run a concrete revenue experiment, and which experiment should be attempted first.

It does not decide company valuation, fundability, legal compliance, or whether the project will become a large business.

## Expert Evaluation Model

GitHub repositories expose two kinds of evidence:

1. Repo-native product evidence: docs, installation, examples, releases, package metadata, license, support channels, funding files, issue templates, integrations.
2. Repo-native market proxy evidence: stars, forks, issues, discussions, dependents, downloads, external mentions, sponsor activity.

Strong monetization review separates these from actual revenue proof. Demand proxies are useful for prioritizing outreach or experiments, but they do not prove willingness to pay. A repo with 20,000 stars and no buyer, price, or paid conversion path should not score as monetization-ready.

## Categories

### A. Buyer & Use Case Clarity - 15

Full evidence:
- README or docs identify a specific user segment and buyer or budget owner.
- Use cases connect to costly, urgent, repeated, or business-critical workflows.
- Examples show who adopts the project and why.

Partial evidence:
- Clear developer user but no economic buyer.
- Broad problem framing with some concrete use cases.

Low evidence:
- Tool is technically described but the repo does not say who needs it or why they would pay.

Proxy validity:
- README, docs, examples, and issue templates are valid evidence because they shape adoption and sales conversations.

Manual review:
- Decide whether the named user is also the payer. Developer love alone is not budget authority.

### B. Demand Proxy Quality - 15

Full evidence:
- Multiple demand proxies align: stars, forks, issues, discussions, dependents, downloads, integrations, community adoption, repeated feature requests.
- Activity is recent and tied to real use, not only launch curiosity.

Partial evidence:
- Some stars/downloads or active issues, but little evidence of production use.

Low evidence:
- No visible adoption, stale activity, or only vanity metrics.

Proxy validity:
- GitHub engagement can indicate attention and usage, but it is weak proof of payment.

Manual review:
- Check recency and quality of demand. High stars with stale issues may signal abandoned interest.

### C. Productization Readiness - 15

Full evidence:
- Clear install path, quickstart, examples, API docs, tests, releases, changelog, versioning, deployment instructions, and stable packaging.

Partial evidence:
- Usable project with docs but missing release discipline, examples, or deployment clarity.

Low evidence:
- Interesting code but hard to install, evaluate, or trust.

Proxy validity:
- Paid conversion usually requires low-friction evaluation and a stable surface.

Manual review:
- Determine whether docs support a buyer demo, not only a contributor setup.

### D. Monetization Path Fit - 15

Full evidence:
- Repo naturally supports one or more paid paths: hosted SaaS, managed cloud, enterprise license, paid support, GitHub Marketplace app, plugin marketplace, compliance package, team collaboration tier, or professional services wedge.
- License and architecture do not undermine the paid path.

Partial evidence:
- Plausible path exists but is not documented or packaged.

Low evidence:
- Repo is useful but hard to charge for, easy to self-host with no differentiated paid layer, or license conflicts with the proposed model.

Proxy validity:
- Architecture, license, integrations, and packaging determine whether attention can become revenue.

Manual review:
- Evaluate whether the path is credible for the audience and ecosystem.

### E. Revenue Proof & Conversion Evidence - 15

Full evidence:
- Concrete pricing, paid customers, sponsors, paid pilots, contracts, invoices, MRR/ARR, Stripe/billing, sponsor tiers, or conversion funnel.

Partial evidence:
- Sponsor button, pricing page, waitlist, or paid pilot intent without proof of payment.

Low evidence:
- No price, payer, paid workflow, or conversion path.

Proxy validity:
- This category requires direct revenue or conversion evidence. Popularity proxies are not enough.

Manual review:
- Verify that "paid", "enterprise", and "sponsor" language refers to actual buyer behavior, not aspirational copy.

### F. Maintenance Economics - 10

Full evidence:
- Support burden appears manageable or monetizable through support tiers, hosted service, automation, docs, SLA, or enterprise plans.
- Issue backlog, dependency posture, and maintainer model are visible.

Partial evidence:
- Some support docs or issue handling, but cost-to-serve is unclear.

Low evidence:
- Heavy support load, stale issues, unstable dependencies, unclear maintainers, or no path to fund maintenance.

Proxy validity:
- GitHub issues, templates, release cadence, and support docs reveal cost-to-serve risks.

Manual review:
- Decide whether support demand is a revenue wedge or an unbounded liability.

### G. Distribution Surface - 10

Full evidence:
- Repo has credible channels: package registries, GitHub Marketplace, integrations, docs SEO, website, partner ecosystem, examples that drive adoption, or app/plugin stores.

Partial evidence:
- One usable channel exists but conversion path is weak.

Low evidence:
- Users must discover and evaluate the project by accident.

Proxy validity:
- Distribution is observable through metadata, links, package files, docs, marketplace files, and integrations.

Manual review:
- Check whether the channel reaches buyers or only free users.

### H. Revenue Experiment Readiness - 5

Full evidence:
- Next paid experiment is obvious and can be launched with existing repo assets: sponsor tiers, paid support page, hosted trial, enterprise intake, paid plugin listing, or checkout.

Partial evidence:
- Experiment is plausible but needs copy, landing page, or buyer segmentation.

Low evidence:
- No actionable revenue experiment can be inferred from repo evidence.

Proxy validity:
- Experiment readiness is the bridge from evidence to action.

Manual review:
- Choose the smallest experiment that can validate willingness to pay.

## Score Caps And Red Flags

- If no buyer/use-case evidence exists, total score should rarely exceed 45.
- If no price, sponsor, billing, paid pilot, or revenue proof exists, total score should rarely exceed 69.
- If the repo is abandoned or impossible to install, total score should rarely exceed 55.
- If demand proxies are strong but revenue proof is absent, flag "popularity without monetization proof."
- If license terms conflict with the likely paid path, flag manual legal/business review without giving legal advice.
- If extraction fails for files likely to contain business evidence, do not score them as missing proof; report extraction gaps.

## ROI Actions

Revenue actions should convert missing evidence into the next experiment:

- Define buyer and paid use case from top issues/discussions.
- Add pricing hypothesis and sponsor/support tiers.
- Create hosted demo, trial, or paid support intake.
- Package enterprise deployment/support docs.
- Add marketplace or registry listing metadata.
- Run paid pilot outreach to users visible in issues, discussions, dependents, or integrations.
