# Compiler input contract

Read when preparing or diagnosing input. The compiler consumes UTF-8 JSON from saved MCP results and never calls services.

## Top-level object

```json
{
  "scopeTitle": "Website redesign",
  "scopeUrl": "https://www.wrike.com/workspace.htm?acc=123",
  "selectedTasks": false,
  "recommendations": [],
  "users": [],
  "attributeNames": {},
  "parameterLabels": []
}
```

- `scopeTitle` is optional for an explicit task list; when absent, the board uses “selected Wrike tasks”.
- `scopeUrl` optionally supplies the resolved HTTPS Wrike permalink for a named project or folder. In the second header line, the word “for” stays regular black text and only the scope name is a plain link, using Klaxoon's default link formatting just like task-card links. Omit it for an explicit task list; an absent or invalid URL falls back to the unquoted plain black scope name.
- `selectedTasks: true` forces that wording even when `scopeTitle` is present.
- `recommendations` is required. Put the untouched `recommend_resources` result or wrapper here; the compiler flattens its solutions in input then solution-index order.
- `users` contains compact rows for referenced assignees only: `id`, display `name`, and `title`. A name is required and cannot be blank, whitespace, or a raw `w:usr:...` id; an invalid name or a missing referenced user row blocks compilation before any Klaxoon request. Use `title: ""` when Wrike returned no title; this is valid and does not block compilation. The compiler deliberately ignores Wrike's generic `role` because that field is an account permission level, not a job title.
- `attributeNames` maps only custom-field ids (`w:cp:N`) actually present in returned reasoning arrays to their display names. Do not copy unrelated user custom fields.
- `parameterLabels` supplies concise plain-language labels in flattened scenario order whenever the user names or distinguishes scenarios, such as different member pools or matching rules. Each label appears both in the comparison summary and under its `Option A`, `Option B`, and so on heading. Use an empty or missing label only for unnamed alternatives, which keeps the compiler's generated option subheader; omit the field for unlabeled alternatives returned by one recommendation call.

## Prepare supporting metadata

- Pass each saved recommendation result through unchanged so every returned `reasoning.matchedAttributes`, `reasoning.missingAttributes`, and `reasoning.requiredAttributes` array reaches the compiler. Empty arrays remain valid and render no empty label.
- Resolve a `get_users` row for every user referenced by a `resourceWorkloads` map, following the live tool's batching and pagination instructions, then retain only id, display name, and title in compiler input. Keep the user with an empty `title` when no title was returned.
- When a returned attribute contains a custom-field id, resolve its display name by id using current Wrike tool capabilities when needed. Do not search for a custom field by name, and never guess a label.

## Fields consumed from recommendation data

The compiler consumes the following fields from recommendation results; additional response fields are ignored:

- run: `affectedPeriod.start/end`, `timeUnit`, `effortEstimationPrecision`, `solutions`, `solutionsMetadata.tasks.tasks`, `solutionsMetadata.resources.resources`;
- solution: `index`, `assignments`, `unassignedItems`, `resourceWorkloads`, `taskCount`;
- assignment: `taskId`, `responsibleId`, optional `reasoning.matchPercent`, `matchedAttributes`, `missingAttributes`;
- unassigned row: `taskId`, optional `reasoning.flags`, `requiredAttributes`;
- workload: `periodTotals.capacity`, `outOfScopeAllocation`, `proposedAllocation`, `projectedWorkload`, `overload`, and optional `overload[]` intervals with their reason.

The compiler reads `timeUnit` for every recommendation run. For `MINUTES`, it converts effort and capacity to hours. For any other declared unit, it preserves the numeric values and labels them with that unit.
Options compared on one board must use compatible units. Minutes and hours are compatible after conversion; incompatible mixed units block compilation rather than producing misleading workload bars.

For summary counts, “not assigned” is the number of unique task ids in `unassignedItems` and “staffed” is `taskCount` minus that number, bounded at zero. A task may count in both “not assigned” and “partial match” when one requested assignment is unfilled and another has missing requirements. The user-facing board does not expose the response's internal assignment-row mechanics. The all-clear message is allowed only when no `unassignedItems` row exists and no other displayed staffing risk remains.

## Output

Inspect `manifest.json`, not all batches at once. After `--board-id`, each batch is a ready-to-send `create_whiteboard_items` argument. Use a dedicated plan directory; recompilation replaces its prior manifest and batches.

The compiler does not apply assignments, call Klaxoon, repair boards, or choose a scenario. Do not read its source during an ordinary run.
