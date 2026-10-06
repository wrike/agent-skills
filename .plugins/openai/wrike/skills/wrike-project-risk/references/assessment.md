# Assess risks

## Find the threat

- Name the commitment: objective, milestone, or constraint. Stay within the requested projects.
- Read its prerequisites. Check relevant tasks, descriptions, comments, and approvals.
- Explain the chain: **cause → possible event → effect on the commitment**.
- Check whether the dependency is real. Date order alone proves nothing.
- Check later updates, completed work, approvals, buffers, and alternatives. Drop concerns already resolved.
- Link the evidence. Date and attribute comments. Label assumptions.
- Missing approval or deliverable? Check the relevant item before calling it missing. Cannot verify? Say what is unknown and why it matters.
- Need an attachment's evidence? Read it. Its title is not evidence. Respect access restrictions.
- Need complete counts? Retrieve all pages and relevant branches. Otherwise label counts partial. Parent approval checks do not cover child tasks.

## Check patterns when useful

- Growing overdue work. Concentrated ownership. Intake exceeding completion.
- Count unique items. Avoid counting the same work as both parent and subtasks. State the scope.
- Compare complete periods. Check task size, project phase, and holidays before claiming deterioration.
- Task counts do not prove overload. Quiet, overdue, or unassigned tasks do not automatically threaten delivery.
- No named assignee? Check job-role allocation, especially for blueprint tasks. If roles are hidden, ownership is unknown.
- Connect the pattern to the commitment. No connection, no supported risk.

## Classify

- **Risk:** might happen; could affect the objective.
- **Issue:** already happened. Explain recovery and any further risk.
- **Unknown:** evidence missing or conflicting. Identify the fact needed.
- **Resolved / immaterial:** exclude from active risks.

Score risks only. Give urgent issues and unknowns their own next action. Generic possibilities belong in requested brainstorming, labeled as such.

## Score

Default: **pmo-li-v1**. Use another method only when the user requests it. Do not search or ask for scoring policies. Existing field ratings do not override this rubric.

Judge likelihood within the assessment horizon:

| Score | Likelihood |
|---|---|
| 1 | Rare: exceptional circumstances needed; strong verified protections. |
| 2 | Unlikely: possible path, but evidence points against occurrence. |
| 3 | Possible: credible path; evidence favors neither outcome. |
| 4 | Likely: conditions favor occurrence unless intervention works. |
| 5 | Almost certain: imminent; little credible prevention remains. |

Unknown is not 3. Already happened is an issue, not 5.

Judge impact if the event happens:

| Score | Impact |
|---|---|
| 1 | Negligible: absorbed within documented tolerances. |
| 2 | Low: local disruption; recoverable within existing authority and tolerance. |
| 3 | Moderate: meaningful objective/milestone effect; planned adjustment needed. |
| 4 | High: major commitment threatened; substantial intervention needed. |
| 5 | Critical: essential objective fails or consequence is explicitly unacceptable. |

Use the highest supported impact across schedule, scope, cost, quality, or operations. Explain it. Do not add impacts or invent universal dollar/day thresholds.

**Score = likelihood × impact.** Map the score to a priority band using the table below.

| Product | Band | Color |
|---|---|---|
| 1–3 | Negligible | Green |
| 4–7 | Low | Amber |
| 8–11 | Moderate | Amber |
| 12–19 | High | Red |
| 20–25 | Critical | Red |

- Rate only when evidence supports both likelihood and impact. Otherwise mark Unassessed.
- Impact 5 or an explicitly unacceptable consequence? Flag the decision/review needed, even with a Low band. Keep the calculated band.
- **Urgency:** when action can still change the outcome. Not the score.
- **Confidence:** strength of evidence. High = current, direct, consistent, adequate coverage; medium = some inference or gaps; low = major gaps or contradictions. Not event likelihood.
- Rate current conditions. Lower the rating when evidence supports lower likelihood or impact. Planned mitigation or a completed mitigation task alone does not lower risk.
- Label estimates after proposed mitigation as hypothetical.
- These are qualitative judgments, not measured probabilities or an official Wrike standard.
- [score.py](../scripts/score.py) supports the default rubric only. For a user-requested method, calculate using that method. Check the arithmetic. Omit unverified calculations.
- Explain calculations when asked: factors, evidence, product, band, effective controls, and any severe-consequence decision.

## Reassess

- Read the previous assessment. Match risk IDs, projects, dates, and horizon.
- No baseline? Report current findings; do not claim improvement or deterioration.
- Compare ratings only with comparable methods and horizons. Otherwise compare facts and consequences.
- Mark changes: new, worse, better, unchanged, resolved, or unknown. Cite the new evidence.
- An updated timestamp does not prove a deadline changed.
- User correction? Revise the conclusion. Recheck the record; note any mismatch.
- What-if request? State assumptions. Keep the live baseline unchanged.

## Multiple projects

Group shared causes. Show each affected commitment, response, decision, and evidence. Do not count repeated mentions as separate risks or sum scores into a portfolio rating. Label existing local ratings separately.

## Do not invent forecasts

- Capacity needs effort, allocation, availability, skills, and timing.
- Budget forecasts need baseline, actuals, assumptions, and currency.
- Schedule forecasts need dependencies, lags, durations, calendars, and constraints.

Missing inputs? Explain the supported concern and needed inputs. Use supplied calculations or calculation tools for numerical forecasts.
