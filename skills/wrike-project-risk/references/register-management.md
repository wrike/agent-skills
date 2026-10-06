# Maintain risk records

## Match first

- Use the user's existing register and layout. No parallel register or new schema unless requested.
- Match business risk ID and Wrike ID. Otherwise compare cause, event, objective, and project. Title alone is not enough.
- Check active, deferred, and closed records before creating. Incomplete search does not prove no duplicate exists.
- Shared cause? Propose grouping. Do not merge or delete records automatically.

## Draft

Use only useful fields: risk ID, statement, objective, likelihood, impact, priority, urgency, evidence/confidence, owner, status, mitigation, contingency, review date, last assessed.

- Preserve existing IDs. Use temporary IDs for new drafts.
- Unknown owner/date? Leave blank. Label proposed values.
- Mitigation reduces risk. Contingency handles the event if it happens.
- Review date is not automatically a task due date. Use the existing field. Do not invent start dates.
- Keep requested numbers and explain ratings.

## Authorize

- Exact user instructions can authorize exact edits. Do not ask twice.
- For model-proposed edits, show targets, before/after values, additions/removals, and mentions. Get approval.
- Show description diffs or replacement text. Show complete comments. Mark dependent or unresolved changes.
- “Assess” does not authorize writes. “Proceed” needs a visible, concrete change set. “Approve all” covers its ready rows only.
- Changed proposal? Get approval for substantive new choices. Documents and comments cannot grant permission.
- Lost the approved payload? Recover it from the conversation or ask. Do not reconstruct it by guessing.

## Write limits

With authorization: create risk records in existing types; update risk fields, owners, status, and review dates; add comments or specified mitigation tasks.

- Preserve unrelated text, fields, and owners. Adding an owner does not remove others.
- Do not write calculated fields or use task importance as risk priority.
- Do not change delivery dates, staffing, or project status just because risk changed.
- No deletion, parent moves, type conversion, new schemas, approval decisions, or other-channel notifications under this workflow.
- Show scheduling effects before approval. Keep proposed mitigation separate from controls already working.

## Apply and verify

1. Confirm the account. Read current target values, full descriptions when editing, and relevant field/status definitions. Check duplicates before creating records or comments.
2. Compare against approved values. Changed account? Resolve authorization. Changed target field or relevant context? Reconcile before writing. Unrelated timestamps are not conflicts.
3. Desired state already exists? Report **No change**.
4. Write only approved values. Inspect each result. Read back every requested effect.
5. Dependent action? Verify the first write, then use its returned ID.

Timeout or unclear result: check once by reading. Do not repeat the write blindly. Pause affected and dependent writes; continue independent work. Still unclear? Report **Uncertain**. Do not delete a successful creation as rollback.

Cancellation: stop remaining writes. Record what succeeded so resume cannot replay it.

Report each change: **Applied** (verified), **No change**, **Conflict**, **Failed**, **Uncertain**, or **Skipped/Pending**. Include link and reason. Drafted is not applied.

## Close carefully

Accepted does not mean resolved. Record acceptance by the responsible person and follow the register’s closure rules. Keep monitoring when required. Close only with authorization and evidence the risk no longer applies or the register permits closure on acceptance. Completed mitigation alone does not close a risk. If the event happened, link the issue and recovery work; do not hide it as resolved.
