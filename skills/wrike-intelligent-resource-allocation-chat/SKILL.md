---
name: "wrike-intelligent-resource-allocation-chat"
description: "Runs Wrike Intelligent Resource Allocation for a scoped project, folder, or selected tasks with Labs Wrike MCP recommend_resources, then renders a compact visual assignee dashboard with KPI cards, attention cards, and workload bars in the current AI chat. Applies when the user explicitly requests current-chat output, declines a whiteboard, selects chat after being asked where to display the result, or invokes this skill directly."
metadata:
  version: "1.0.0"
---

# Wrike intelligent resource allocation in chat

Use `Labs Wrike MCP:recommend_resources`; host-specific prefixes may differ, so match the Labs Wrike MCP server and the `recommend_resources` tool name. If that tool is unavailable, say the required Wrike connection is unavailable and stop. This workflow recommends assignees only; do not shift dates or reschedule work. Never substitute a search or workload-reporting tool, call Klaxoon, or create a whiteboard.

## Call strategy

- Normally make one recommendation call. Do not fetch profiles, task details, or custom-field names merely to decorate the answer.
- Treat the live tool description as the source of truth for filters, identifiers, defaults, response semantics, errors, and recovery. Apply this skill's presentation rules to decide what appears in the user-facing answer.
- When requested interval-level data is not returned, say so and render the result from the available totals and overload entries.
- Follow errors and recovery guidance from the live tool contract. Do not turn an error into a staffing result or add the proposal-closing language below to an error response.

## Prepare presentation data

Read the first returned recommendation (`recommendations[0]` in the current response shape) and its `solutions[]`. Keep options in returned order.

For each option:

- Group assignment rows by task, but keep fit attached to each assignment row. Show every proposed assignee with that assignee's own fit.
- Preserve every entry in `unassignedItems`, including its reason. A task can have proposed assignees and items not assigned at the same time; show both and do not call it fully staffed.
- Render a numeric assignment `reasoning.matchPercent` as `100% fit`, `N% fit`, or `0% fit`. For a filled assignment, treat an absent or null match percent as `requirements not set`, as defined by the current output schema. For an unfilled item, use its returned flags and requirement facts instead of inferring a fit from a missing percentage.
- Treat every custom-field value in `reasoning.matchedAttributes`, `reasoning.missingAttributes`, or `reasoning.requiredAttributes` as opaque. Never invent, infer, expand, paraphrase, or add a parenthetical explanation of what a value means.
- By default, use only the attribute title and value returned by `recommend_resources`. If no title was returned, show the value neutrally as `Requirement: <value>` or omit that detail; do not call another tool just to label the standard dashboard. Call `get_item_details` only when the user asks for the exact custom-field title or that title is essential to explain a material staffing outcome accurately. In that exceptional case, batch up to five affected task IDs per call, leave `fullDescriptions` omitted, match the attribute ID to `customFields[].id`, use only `customFields[].name` as the title, and preserve the value without interpretation. A returned `kind: jobRole` value is already a job role title and does not require this lookup.
- Use `reasoning.flags` to select the appropriate plain-language explanation:
  - `NO_MATCH_REQUIREMENTS` → `no one has all required skills`
  - `NO_MATCH_AVAILABILITY` → `no matching candidate has capacity`
- In user-facing output, call each `unassignedItems` entry an **item**, not a slot.
- Convert displayed values to hours only when the conversion is defined: divide `MINUTES` by 60; leave `HOURS` unchanged. Round displayed hours to one decimal and drop a trailing `.0`. For any other `timeUnit`, keep the returned value and unit and say the tool contract does not define an hours conversion; do not guess.
- Determine overload status only from positive entries in `resourceWorkloads[userId].overload[]`. Translate `PROPOSAL` to `caused by this recommendation` and `EXISTING` to `already present before this recommendation` in the main explanation; retain raw reason values only if the live tool contract requires them.
- Use workload totals only as display data. Identify the returned totals that the live response and tool description define as capacity, already committed or out-of-scope effort, proposed effort, and projected workload. Do not assume undocumented property names.
- Report `unassignedWork.remainingTotal` when it is above zero, using the safe unit handling above.
- Calculate workload percentage as `round(projected workload / capacity × 100)`. Do not cap percentages above 100%. When capacity is zero, show `n/a`. This percentage is display-only and must not determine overload status.
- Treat solution feasibility, constraints, constraint priorities, penalty values, hard or soft scores, and similarly named diagnostics as internal-only data. Exclude them from user-facing output and do not use them to rank options. Surface only the concrete outcomes covered elsewhere in this skill: items not assigned, partial matches, overload entries, and remaining unassigned work.

Use these summary counts per option:

- Items with assignees: distinct task IDs in assignments, out of that option's `taskCount`.
- Assignees proposed: that option's `resourceCount`.
- Items not assigned: number of entries in `unassignedItems`.
- Assignees over capacity: distinct people with a positive entry in `overload[]`.
- Items with partial match: distinct task IDs having at least one numeric assignment fit above 0% and below 100%.

An option qualifies for the green overall-success widget only when all of these are true:

- `taskCount` is above zero and equals the number of distinct task IDs in assignments.
- `unassignedItems` is empty.
- Every assignment row has a numeric `matchPercent` of exactly 100.
- No assignee has a positive `overload[]` entry.
- `unassignedWork.remainingTotal` is absent or zero.

Do not create a composite score, quality ranking, or winning option unless the user states the priority to optimize.

## Use plain language

Use `Option A`, `Option B`, and `Option C`, never `solver variant`. Do not introduce implementation terms such as `solver`, `cutoff`, `feasible`, `constraint`, `priority`, `penalty`, response field paths, or internal field names.

## Render the recommendation

Once this skill is selected, current-chat output is already established. Do not ask again where the recommendations should be shown, whether the user wants a visual or text response, or which rendering capability to use. A rendered visual dashboard is the default. Autonomously inspect the capabilities available in the current host and use the best supported native visual path. If several are available, choose the quickest self-contained option that can render the specified widgets clearly.

Do not choose a plain Markdown answer merely because it is faster or because no separately named visualization tool is listed.

When the current host can render native artifacts, canvases, components, HTML/SVG, or charts, create one lightweight dashboard attached to the current conversation:

- Use whichever native visualization, canvas, artifact, component, HTML/SVG, or chart capability the host provides.
- Keep it self-contained and quick to render. Use only built-in HTML/CSS/SVG or the host's built-in components; do not install packages, load external libraries, or call another visualization service.
- Render the dashboard for the user rather than returning its HTML, SVG, JavaScript, or component source as the recommendation.

Use Markdown only when the host cannot render a native visual, the user requests text-only output, or the native rendering attempt fails. Fall back without asking the user to choose. Keep the result in or attached to the current conversation; never create an external board.

Make every displayed item name a Wrike permalink in every visual and fallback location, including attention cards, fit groups, recommendation cards or tables, and multi-option comparison rows. When the canonical item ID is `w:itm:N`, link the visible item name to `https://www.wrike.com/open.htm?id=N`. Use the same target for every occurrence of that item. If a canonical item ID is unavailable or does not match that format, show the name as plain text and do not invent a link.

Use one panel for one option and side-by-side panels for multiple options when the host supports them. Each option panel contains:

1. **Top KPI widgets**, compact and in one row when possible:
   - `Items with assignees` — `<assigned items> of <taskCount>`; red when any items are not assigned, otherwise blue or neutral.
   - `Assignees proposed` — `<resourceCount>`; blue.
   - `Assignees over capacity` — `<count>`; red above zero, green at zero.
   - `Items with partial match` — show only above zero; orange.
   - `Items not assigned` — show only above zero; red.
2. **Fit and attention cards**:
   - Red header: `Items with no match found (<count>)`, where `<count>` is the number of entries in `unassignedItems`; order them by task title and include every item's plain-language reason.
   - Red header: `0% fit`.
   - Orange header: `Items with partial match (<count>)`, using the distinct-item count defined above and ordering items by fit ascending.
   - Orange header: `Requirements not set (<count>)` when explicitly established; otherwise `Fit not reported (<count>)`. Count distinct assigned items in the displayed category.
   - Green overall-success widget: show it only when the complete success condition above is met. Its text is `All <taskCount> items staffed at 100% fit, no one over capacity`.
   - Red header: `Over capacity`, with the affected date or week, overload hours, and whether it was caused by this recommendation or already existed.
   - Omit empty categories. In Markdown or plain text, prefix red and orange headers with `⚠️` and the green overall-success widget with `✅`.
3. **Workload impact**:
   - Draw one horizontal stacked bar per proposed assignee using the safely converted display values.
   - Gray = already assigned effort; blue = effort added by this recommendation; pale blue = free capacity (`max(capacity - projected workload, 0)`); a capacity marker = total capacity.
   - Add a red overload indicator only when positive `overload[]` entries exist.
   - Label each row: `<added>h added + <already assigned>h already assigned = <projected>h of <capacity>h (<workload percentage>%)`. With zero capacity, end with `(n/a)`. If hours conversion is unavailable, use the returned unit consistently instead of `h`.
   - A Markdown fallback uses: `Assignee | Added | Already assigned | Projected / capacity (%) | Overload`.
4. **Assignee recommendations**:
   - Show one row or card per task: `Item | Suggested assignee(s) and fit | Notes`.
   - List every assignee separately inside the grouped task row so each fit remains attached to the correct person.
   - In Notes, include only relevant missing requirements, every item not assigned, or overload impact.

For the Markdown fallback, preserve the visual hierarchy instead of returning only plain tables:

- Start with compact KPI tiles on one line when space allows, using `🟦`, `🟩`, `🟧`, and `🟥` as color accents.
- Render attention sections as short card-like blocks with `⚠️` or `✅` headers.
- Approximate each workload bar with proportional `█` and `░` characters and keep its numeric label. Do not imply more precision than the returned values support.
- Use tables only for workload rows, task recommendations, and multi-option comparison when they improve scanning.

Lead with the most important exception. If none exists, say there are no items left unassigned and no detected overloads; do not imply that every fit is complete unless the data shows that separately.

## Compare multiple options

For more than one returned option, read [references/multi-option-comparison.md](references/multi-option-comparison.md).

## Close with the assignment choice

If at least one assignment was proposed, state exactly:

`These are recommendations only — nothing has been assigned in Wrike.`

Then ask one application question:

- If one option was rendered: `Would you like me to apply these assignments in Wrike?`
- If multiple options were rendered: `Which option, if any, would you like me to apply in Wrike: Option A, Option B, or Option C?` Include only the option labels actually rendered.

When no assignments were proposed in any option, do not show the recommendations-only statement and do not ask an application question:

- If the tool returned an error, follow its error and recovery guidance without adding fixed wording from this skill.
- Otherwise, trust the returned result. State that the item or items cannot be assigned and give one brief aggregate summary of the returned `reasoning.flags`, covering capacity and/or required skills as applicable. Do not repeat or render the item list again, and do not invent a reason that the tool did not return.

Never apply assignments in the same turn as the recommendation. Wait for an explicit user reply; when several options were shown, the reply must identify the option to apply.
