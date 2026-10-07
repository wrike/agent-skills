# Create or rebuild a staffing board

Read this only for board creation or rebuilding. The agent owns scope, authenticated MCP calls, recovery, and communication. The local, credential-free `scripts/compile_board.py` owns normalization, layout, HTML, ordering, batching, and expected totals.

Load supporting references only when their stage is reached:

- Prepare compiler input: [input-contract.md](input-contract.md)
- Deliver and verify: [board-delivery.md](board-delivery.md)
- Handle multiple solutions: [multiple-options.md](multiple-options.md)

## Workflow

1. Determine origin from trusted host context, not from the presence of a Wrike link. A Workmate-style trigger with a Wrike item and invoker is Wrike-origin; otherwise treat the request as chat-origin.
2. Route from request text already present in trusted trigger/chat context, before fetching or enumerating Wrike contents:
   - Wrike-origin: create a board without asking when the request explicitly asks for visual output, scopes a project/folder, or names/links more than 10 individual tasks. Count only tasks explicitly present in the request; never inspect a project/folder merely to decide routing. For 10 or fewer explicit tasks without a visual request, stop and answer without this mode.
   - Chat-origin: when no destination is stated, ask exactly: `Do you want this on a Klaxoon whiteboard, or just summarised here?` Stop this mode on a no.
3. Resolve only the named scope. Use supplied Wrike ids or links directly. When the user supplies only a project/folder name, search Wrike for that name; use a unique clear match or ask the user to disambiguate. Use the resolved container for a project/folder scope and preserve its HTTPS Wrike permalink as `scopeUrl`; use resolved task ids for named tasks and omit `scopeUrl` so the header remains `for selected Wrike tasks`.
4. Call the Wrike MCP `recommend_resources` tool with the resolved scope and user filters or scenarios. Set `solutionsCount` to 1 unless the user explicitly asks for alternatives, a comparison, or a specific larger number of options.
5. Read the input contract and assemble one JSON input from saved MCP results. Put the untouched `recommend_resources` result(s) under `recommendations`. When the user names or distinguishes scenarios, also put those concise names under `parameterLabels` in the same order. Under `users`, keep only each referenced assignee's `id`, display `name`, and `title` (use an empty string when Wrike returned no title); do not copy other profile fields, including the generic account-permission `role`. Add `attributeNames` only for custom-field ids actually present in returned reasoning arrays. Run `<python> scripts/compile_board.py INPUT.json --out PLAN_DIR`.
6. Read only `PLAN_DIR/manifest.json`. A nonzero exit or any `errors` blocks board creation. If no eligible items were found, stop without creating a board and tell the user: `No eligible items were found, so there is nothing to find assignees for.` When the user named or distinguished scenarios, confirm that each `scenarioSummaries[].label` contains the matching requested name; otherwise fix the input and recompile before any Klaxoon call. Load the multiple-options reference when the manifest has multiple scenario summaries.
7. Follow the board-delivery reference to create, populate, verify, and deliver the board according to request origin.
8. Reply in 3–4 sentences with the most important user-relevant risk first, then the board link. In a Wrike comment host, also follow its acknowledgement, closing-comment, and mention rules; use the live comment tool's mention syntax with an id supplied by the host.

## User-facing invariants

- Treat solution feasibility, constraints, constraint priorities, penalty values, hard or soft scores, and similarly named diagnostics as internal-only data. Exclude them from user-facing output and do not use them to rank options.
- Do not introduce implementation terms such as `solver`, `cutoff`, `feasible`, `constraint`, `priority`, `penalty`, response field paths, or internal field names.
- Use `reasoning.flags` only to select a plain-language explanation. Determine overload status only from positive entries in `resourceWorkloads[userId].overload[]`; translate `PROPOSAL` to `caused by this recommendation` and `EXISTING` to `already present before this recommendation`. Do not expose raw diagnostic codes unless the live tool contract makes retaining one unavoidable.
- Treat every custom-field value in `reasoning.matchedAttributes`, `reasoning.missingAttributes`, or `reasoning.requiredAttributes` as opaque. Never invent, infer, expand, paraphrase, or explain what a value means.
- Do not expose raw ids except the muted user id rendered on an assignee card or an id required by the host's real mention syntax.
- Never hand-edit batches; fix the input or compiler and recompile.
