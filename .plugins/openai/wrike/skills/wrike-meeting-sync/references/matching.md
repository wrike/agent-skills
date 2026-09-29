# Matching Meeting Notes to Wrike

Match the polished meeting notes to Wrike tasks, projects, and folders. The notes are the only source for what happened in the meeting; Wrike is the source for current work state. Do not use the raw transcript or infer facts that are missing from the notes.

Matching is read-only. It inspects Wrike and prepares proposals, but it never creates, comments on, or updates anything. Applying approved changes happens later in the workflow (see `operation-rules.md`).

## Requirements

A Wrike MCP connector must be connected so you can search and read items. Use the connected Wrike tools (for example `Wrike:search_tasks`, `Wrike:search_folder_project`, `Wrike:get_task`, `Wrike:get_folder`, `Wrike:get_contacts`, `Wrike:get_workflows` — match the actual tool names your connector exposes) to read state. If no Wrike connector is available, say so and stop; do not guess at Wrike contents.

## Find relevant work

- Read and report the connected Wrike user first, so the user knows whose account is in scope.
- Identify the narrowest relevant space, project, or folder, and scope searches to it whenever possible.
- Resolve explicit Wrike links or item IDs first. If the notes quote a Wrike title or say they found or opened an existing item, search that title first (close-title) and inspect that hit before any broader keyword search. That item is identity even if it is old, deferred, or from a prior year. Otherwise derive distinctive search terms from the notes — the project, product, client, or initiative named around each action item.
- Search projects and folders as **two separate calls** (`project: true` and `project: false`). They are different queries; a single search will miss one kind.
- Use a task search when a mentioned work item may be a task-based custom type (Campaign, User Story, etc.), and inspect its parents for destination context.
- Inspect plausible items before proposing an action — check title, type, parent, status, people, dates, description, custom fields, and permalink as relevant.
- Same owner, same `[DS]`/`[BE]` prefix, or the same parent epic is not a match. The title's distinctive nouns must match the deliverable (analyze results is not identify use-case examples; ranking unification is not a shipped boost). A Completed item that holds a related artifact (spreadsheet, examples) is not the home for new hypotheses or next-step work on a different active item.
- Treat an explicit ID as item identity, not as proof that a change is supported by the notes.
- Never invent owners, dates, statuses, field values, or outcomes.

### Choosing a destination (do not guess)

Prefer a destination only when its title, hierarchy, description, and the notes' context make it **clearly more relevant** than the alternatives. Do not choose a destination merely because it has a keyword match — a shared keyword is not a match.

If, for a given action item, there is **no credible destination** or **more than one credible destination**, do not pick one. Put the item under **Needs your input** with up to three candidate names and permalinks and ask the user to choose. Different action items may belong in different destinations.

Before concluding that two candidates are equally credible, separate them on these signals, in order:

1. **People** — a project whose assignees, owner, or author include the action's owner, or the people in the meeting, beats one that does not.
2. **Scope** — a project whose title and description describe the workstream the action belongs to beats a folder that merely contains related items.
3. **State** — a project the team is actively delivering beats a dormant, completed, or archived one. Use this only when choosing a **parent for new work**. Do not skip an item the notes already named or opened because it looks stale.
4. **Siblings** — a parent that already holds comparable work from this workstream beats an empty or unrelated one.

Only when two candidates survive all four as genuine equals is the item **Needs your input**. "I could not decide quickly" is not the same as "the meeting does not say."

Never create under an item whose status category is Completed or Cancelled, even when the notes point straight at it. Walk up to its parent project or epic, use that as the parent, and say in the preview that you did and why.

Creating a **child** under a project or folder is not a duplicate of that parent. The parent is the destination; the child is new work. Do not skip a create because the destination project already exists.

When the notes name a destination kind — To Discuss, next planning, agenda, backlog — prefer the sibling folder or custom item whose title matches that kind over a generic Action Items / tasks folder.

If **every** action item in a meeting lands under **Needs your input**, treat that as evidence you have under-searched rather than as an answer. Before showing that preview, name the strongest candidate you found for each item and state what specifically disqualified it.

## Cover every action item

Account for every action item in the meeting notes. Do not silently omit one. Give each action exactly one visible outcome:

- update an existing Wrike item;
- create a new Task, Project, or Folder;
- **Already represented / no action needed**;
- **Needs your input**;
- **Not tracked**, with a short reason.

**Not tracked** is only for work the notes say will not be filed in Wrike (personal, courtesy, explicitly parked with no ticket). An explicit commitment with an owner is never Not tracked. If the destination is unclear, that is **Needs your input**, not Not tracked. External outreach, vendor calls, and architecture validation with a named owner are tracked unless the notes say otherwise.

Prefer structured Wrike work over comments, because a comment is easy to miss and does not drive Wrike's own reporting:

1. Update canonical fields on an exact existing item when appropriate: status, people, dates, description, or custom fields.
2. Create a new item when the notes contain explicit work and no suitable item exists.
3. Use comments to preserve rationale, decisions, or meeting context.

**A comment is never the whole answer for an action item that has a deliverable.** If the action names something a person will produce, change, or decide, a comment alone does not represent it. Only a purely informational item — context with no deliverable and no owner — may be represented by a comment alone. If the notes name an owner with a deliverable and no existing item is that work, create or update assigned to that owner. A comment on a nearby ticket, owned by the connected or facilitator user, is not enough.

**This is not a licence to create.** Work down this ladder and stop at the first rung that fits:

1. The work already exists in Wrike → **Already represented**. Name the item and stop.
2. An exact existing item should carry it → **update** its canonical fields. Recording a decision, a scope, an agreed priority, or a set of hypotheses belongs in that item's description or custom fields, not only in a comment.
3. Nothing represents it and the notes carry an explicit commitment → **create**, and only after the duplicate search below comes back empty.

Replacing a comment with a task you did not duplicate-search is a worse error than the comment was. An existing comment that mentions an owner, status, or date does not prove the corresponding Wrike fields are populated — inspect those fields and propose updates when they do not reflect the notes.

When one action item contains distinct work with different owners, timing, or dependencies, prepare separate proposals when that creates clearer accountability.

## Check for existing work before creating

Before proposing to create anything, search the resolved parent for work that already represents the action. "No visible match" alone is not permission to create — the notes must contain an explicit action or creation decision. A restated commitment in the notes (unchanged since a prior meeting, already a task, recap of a decided date) is not a creation decision.

Run a real duplicate search, not a single glance:

- Search **active and deferred** items using the deliverable's distinctive nouns and verbs.
- Run a close-title search first and, when needed, one broader keyword search.
- A meeting-notes / MoM / minutes item is the meeting record, not the work. It is a duplicate only when that item *is* the deliverable (same title/gist as the commitment). Listing an owner, action, and date in MoM does not mean the work already exists — create or update the real item under the destination project.
- Compare title, description, assignees, and status. A shared keyword alone is not a duplicate.

Then branch on the result:

- **Clear match** — report the action as **Already represented**, linking the existing item; do not create a duplicate. Continuing, refining, or sequencing work that already has a Wrike item is an **update** of that item, not a create. If the notes named or opened an existing title, that item is the clear match: update it with the agreed next step. "I'll file this / drop it in chat" after finding it is that update, not a create. A MoM row that merely records the commitment is not a clear match.
- **Ambiguous match** — put it under **Needs your input** with the candidate(s) linked, and state the single decision needed.
- **Failed or unavailable search** — disclose it in the preview; never treat a failed search as a silent "no duplicate."

## Prepare supported actions

Prepare read-only proposals for: comments and due dates; creating standard Tasks, Projects, or Folders; status changes, including completing or cancelling tasks; adding or removing task assignees or project owners; description edits; and custom-field changes.

- **Dates** — the Wrike due-date field is exactly one token: `YYYY-MM-DD` or `none`. If the notes Due is already ISO, copy it. If the notes say "today", "this afternoon", "by end of day", or leave Due as `today`, write `meeting_date`. If a weekday and a day-of-month disagree, use the weekday's ISO from the Date map. Never leave "today" in the field, and do not substitute a nearby Friday.
- **Creation** — resolve the exact parent (per "Choosing a destination") and run the duplicate search above first.
- **Statuses** — inspect the relevant workflow and resolve the exact standard or custom status. Do not guess from a display label.
- **People** — the owner is who accepted the work, not who requested it and not who last mentioned it. "I'll create / file / drop it in chat" from the facilitator is filing, not ownership — assign the Ready row to whoever accepted the deliverable. Resolve that name to a unique Wrike user ID. If more than one person matches, put the proposal under **Needs your input**.
- **Descriptions** — fetch the full current description. Never prepare an edit from truncated content.
- **Custom fields** — resolve the field ID and type, and inspect allowed options when applicable. Clearing a field must be explicit.

## Preview

Group proposals into the sections below.

### Ready to apply

Use a compact table:

| Row | Action | Wrike item | Change |
|---|---|---|---|

- Use stable row labels such as `M1`, `M2`, `M3` for the current preview. Each row is one operation.
- Existing-item actions must identify an exact item and include its canonical ID and permalink.
- Creation actions must identify the exact parent and item type.
- Keep the Change cell short, such as `Active → Completed`, `Sam → Alex`, or `Add comment`.
- Do not dump full comments or descriptions into the table.

Show detailed content only below the table when needed: the exact comment body (before any signature the apply step adds); a description diff or complete before/after text; a new item's title, parent, description, people, status, and dates; custom-field name with human-readable old/new values; and an inline note such as `Runs after M1` when an operation depends on a prior creation.

A proposal belongs under **Ready to apply** only when the exact target or parent, required IDs, valid values, duplicate checks, and complete preview content are all resolved.

Before showing the preview, re-read your own Ready rows and check each one:

- Any row whose only operation is `Add comment` — name the deliverable it records and why no field change applies, or convert it into the create or update it should have been.
- Any Add-comment-only row whose notes name an owner other than the connected user — convert to create or update assigned to that owner.
- Any Ready row that updates item A while the notes name a different existing title — retarget to the named item.
- Any row creating under a Completed or Cancelled parent — re-parent it.
- Any action item with a named owner and a deliverable that is not represented by a Ready row — say which of the other three sections it went to, and why.
- Any Create row for work a duplicate search would have found — that is an **Already represented**, not a create. Re-run the search before keeping it. A MoM / meeting-notes item that only lists the commitment does not count.
- Any Ready row whose due is `today`, empty, or `none` while the notes named today / this afternoon — set due to `meeting_date`.

### Needs your input

List proposals that need one clarification — an ambiguous person, target, parent, status, field, value, destination, or duplicate. State the single decision needed, and link up to three candidates when a choice of destination or item is involved. Do not create a row that looks ready when required information is missing.

### Already represented / no action needed

List action items that require no Wrike change, and identify the item or evidence that already represents the work. Check canonical fields rather than relying on a comment alone.

### Not tracked

List any action intentionally not represented in Wrike, with the reason. External outreach, vendor calls, and architecture validation with a named owner are tracked unless the notes say otherwise.

Every action item must appear under exactly one of these four sections. If the notes support no Wrike actions, say so plainly.
