# Monetization Cartography Rubric

Use this reference when the automatic scorer needs manual review. Keep the review focused on whether the project can generate revenue, not whether it is venture-scale or investable.

## Scoring Principles

- Score evidence, not optimism.
- Reward proof of buyer behavior more than product description.
- Reward a narrow paid path over a broad unpaid audience.
- Mark unknowns explicitly rather than filling gaps with assumptions.
- If evidence is trapped in unreadable scans or images, note extraction failure before penalizing.

## Expert Decision Model

Use the 100-point score to decide how far the evidence can safely support a revenue decision:

- `Monetization-Ready` means the artifact set contains buyer, price, and revenue proof strong enough to support a monetization review or scale-up decision after manual verification.
- `Revenue Experiment Ready` means the evidence is sufficient to run a paid experiment, but not enough to claim repeatable revenue.
- `Monetization Hypothesis Formed` means the buyer/problem/offer story is plausible, but payment evidence or conversion proof is still incomplete.
- `Revenue Evidence Thin` means commercial language exists, but the project needs sharper buyer, price, or channel proof before testing.
- `Not Yet Monetizable` means the materials do not yet support a paid offer decision.

Manual judgment should answer four questions before accepting any high score:

1. Who pays, and what budget, trigger, or pain gives them reason to pay now?
2. What exactly is sold, at what price, and through what package or contract path?
3. What evidence shows payment intent or paid behavior rather than general interest?
4. What channel or sales motion can put the offer in front of the payer repeatedly?

If any answer is missing, keep the score as a heuristic baseline and route the gap into the top revenue actions.

## Domain-Specific Failure Modes

Watch for these false positives and cap or downgrade the affected category unless concrete evidence resolves them:

- Audience proxy: downloads, traffic, followers, GitHub stars, waitlists, or community size are not revenue traction without a payer, price, and conversion path.
- Generic monetization prose: words like revenue, subscription, enterprise, ROI, marketplace, or scalable do not prove monetization unless tied to a specific buyer and offer.
- User-buyer confusion: a well-described user segment does not establish who controls budget or signs the purchase.
- Pricing theater: tier names, ads, or "subscription later" language do not count as pricing without an amount, paid SKU, quote, checkout, or contract ask.
- Pilot ambiguity: pilots, LOIs, partnerships, or interviews are weak unless they are paid, dated, tied to conversion, or show budget confirmation.
- Hidden service labor: software revenue claims are weaker when onboarding, delivery, support, or expert work costs are not reflected in margin or cost-to-serve evidence.
- Channel optimism: launch plans, virality, app stores, marketplaces, or social posts are not distribution proof without buyer access and a conversion step.

## A. Customer & Buyer Clarity - 15

High score:
- ICP or segment is named precisely.
- Economic buyer and user are distinguished when different.
- The target buyer has a clear budget owner or purchasing trigger.

Low score:
- “Everyone”, “creators”, “developers”, or “SMBs” without a specific buyer.
- Users are described, but no payer is named.
- The project only documents features.

## B. Pain Severity & Willingness To Pay - 15

High score:
- Pain is frequent, expensive, urgent, or tied to revenue, risk, or saved labor.
- Evidence includes paid pilots, LOIs, preorders, budget confirmation, or strong interview quotes.
- ROI can be stated in time, money, risk, or conversion terms.

Low score:
- Pain is framed as convenience or preference.
- Interview count exists but no payment signal exists.
- The buyer can solve the problem manually at low cost.

## C. Pricing & Packaging - 15

High score:
- Price points, packaging tiers, seats, usage, subscriptions, one-time fees, or service bundles are defined.
- Packaging maps to buyer value and ability to pay.
- Free plan, trial, or onboarding has a clear conversion role.

Low score:
- “Monetize later” or “ads/subscription” without a price.
- Pricing exists but does not match the buyer or usage pattern.
- No paid SKU or checkout path is described.

## D. Revenue Evidence & Traction - 15

High score:
- MRR, ARR, paid pilots, contracts, paid users, retention, renewal, pipeline, or conversion data exists.
- Evidence distinguishes revenue from vanity metrics.
- Customer count and time window are clear.

Low score:
- Only downloads, GitHub stars, waitlist signups, or traffic.
- Revenue is mentioned without amount, payer, or date.
- Pilots are unpaid and not tied to conversion.

## E. Unit Economics & Margin - 15

High score:
- Gross margin, cost to serve, CAC, LTV, payback, churn, ACV, or ARPU are stated.
- Costs include compute, support, onboarding, marketplace fees, and service labor when relevant.
- The project can plausibly serve customers profitably.

Low score:
- No cost or margin model.
- Heavy human service component is hidden inside “software”.
- Acquisition cost is ignored despite paid channels or sales motion.

## F. Distribution & Conversion Path - 15

High score:
- Acquisition channels are named and connected to conversion steps.
- Sales motion, marketplace, partnerships, content, community, or outbound path is credible for the buyer.
- Funnel assumptions or conversion targets exist.

Low score:
- “Launch on social” or “word of mouth” without a path to buyers.
- Audience exists but buyer access is unclear.
- Sales cycle, onboarding, and close motion are undefined.

## G. Revenue Experiment Readiness - 10

High score:
- Next experiment is concrete: who, offer, price, channel, success metric, and timebox.
- Checkout, billing, preorder, waitlist qualification, or paid onboarding can be tested soon.
- The experiment tests buyer behavior, not only interest.

Low score:
- Next step is more building with no commercial test.
- Experiment measures clicks or signups but not payment intent.
- No owner, metric, timebox, or offer is specified.

## Manual Review Guidance

Use automatic scores as a baseline. Adjust only when there is clear evidence the keyword scan over- or under-counted:

- Raise a category when evidence is specific but phrased in unusual language.
- Lower a category when keyword hits are generic, duplicated, or unrelated to revenue.
- Keep evidence paths and metric values in the final explanation.
- When evidence conflicts, prefer the most recent dated artifact.

Manual review is mandatory when:

- The report total is 70+ or the grade says `Revenue Experiment Ready` / `Monetization-Ready`.
- The target is keyword-dense, especially when many monetization words appear in one generic marketing document.
- `extras.manual_review_required` is true or `extras.manual_review_checks` contains core proof gaps.
- A category score is high without a concrete path to the source file and a specific buyer, price, payer, paid pilot, contract, MRR/ARR, or conversion proof.

For each category, require:

- Evidence path: the file or artifact that supports the score.
- Buyer/payer proof: who pays, who uses it, and what budget or trigger exists.
- Price proof: stated price, paid SKU, package, paid pilot, or checkout/preorder ask.
- Revenue proof: MRR, ARR, paid customer, contract, LOI, renewal, retention, or dated conversion evidence.
- Gap action: if proof is absent, add an unknown/gap action instead of presenting the score as confirmed.

Generic words like revenue, monetization, subscription, enterprise, marketplace, conversion, ROI, scalable, customer success, or growth do not prove monetization without buyer, price, payer, or traction evidence.
