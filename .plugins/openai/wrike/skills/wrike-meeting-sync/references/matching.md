# Matching Meeting Notes to Wrike

Match the polished notes to Wrike without changing anything. The notes define what happened; Wrike defines what already exists and its current state.

## Closed input

The Signals table is the complete input. Resolve every signal exactly once and add none. If one row contains two independent deliverables, re-extract the notes instead of splitting it here. If there is no Signals table, report that the notes support no Wrike actions and stop.

Read and report the connected Wrike user first. If no Wrike connector is available, stop rather than guessing.

## Resolve each signal in this order

### 1. Find existing work before choosing an action

Search is mandatory before every proposed creation.

1. Resolve explicit Wrike links, IDs, quoted titles, and items the speakers found or opened during the call first. A named item remains the identity even when completed, cancelled, deferred, or old.
2. Search the deliverable’s distinctive nouns and object, not generic verbs such as “create,” “review,” or “discuss.” Run a close-title search and a broader intent/synonym search across active, deferred, completed, and cancelled tasks. For a multi-step outcome, search its independently meaningful components so an existing component cannot be hidden inside a larger new proposal.
3. Search projects and folders separately when looking for a destination. If the commitment names an agenda or list, search for that exact list in the relevant team's planning hierarchy. Inspect plausible hits and their parents, descriptions, people, dates, and status.
4. Inspect plausible meeting-notes or MoM items. An Active record counts only when deliberately maintained as a live tracker and its exact action row has an owner and state; when it tracks an event, later decisions about the event's recording, slides, or roles update that tracker rather than create component tasks. A Completed record never does: a row state or checkbox does not override completion. Its row blocks creation only when it links a dedicated work item.

A clear same-deliverable hit wins over a new item even if its wording differs, the meeting adds details or next steps, its status is Completed or Cancelled, or a speaker believed no ticket existed. Compare the exact object, change, prerequisite, and verification: a related completed operation or an empty task named for the artifact is not proof that the promised work is tracked. Add new activity to a genuine match. A broad project description or unowned checklist describing a topic is not proof that the specific owner–deliverable is tracked. A related parent is not a duplicate of a genuinely different child deliverable.

### 2. Choose the disposition

| Signal type | Allowed disposition |
|---|---|
| `commitment` | Update/assign the same existing work; otherwise create only after the safe-create gate below |
| `decision` | Update the affected existing item’s description or field; comment only when no canonical field fits; never create |
| `status` | Update an exact item when its live status differs; otherwise Already represented; never create |
| `date` | Update the exact item’s due date; never create |
| `ownership` | Update the exact item’s people; never create |
| `priority` | Update the exact item’s priority field; comment only if no such field exists; never create |
| `open-question` | Needs your input unless an exact existing item should carry it; never create |
| `non-action` | Not tracked, with the reason |

For an existing item, compare canonical fields rather than relying on comments. If Wrike reflects the exact signal, use **Already represented / no action needed**; otherwise prepare an update. An accepted investigation or unblock step absent from the item is new content: comment its owner, action, and due date on the exact blocked item rather than making it optional. Do not create a sibling or child merely to record context about an existing item.
When an existing item takes a dated commitment, propose changing its due-date field if the current due date differs. Mentioning the deadline only in a comment does not update the commitment.

When a commitment only advances an existing research or decision item, update that item. A separately accepted substantive session, findings handoff, or agenda placement is distinct when the existing item tracks the subject but not the promised event or slot; search for that event before creating it.

### 3. Safe-create gate for commitments

A commitment may appear as a Ready Create only when all four answers are yes:

1. **Task-worthy:** it is a discrete durable deliverable, not mere coordination, administration, a status report, an idea, or work already done. A substantive session, formal findings share, measurement, adoption tracking, or agenda placement passes this test when explicitly accepted.
2. **Owned:** the notes name the person who accepted it, and that name resolves to one Wrike user. A concrete assignment to an absent person remains Needs your input until confirmed.
3. **New:** the duplicate searches found no item, action row, or checklist entry that already represents it.
4. **Placed:** one exact active parent is clearly supported by the workstream or meeting context.

If ownership, novelty, or placement is uncertain, put the signal under **Needs your input** and show the best candidates. Do not make a Ready Create “for completeness.”

### 4. Choose a parent without guessing

Search for parents separately from duplicates, using the deliverable's domain and function as well as product nouns; expand organizational abbreviations. Check for a dedicated container matching the owner's functional work before treating a meeting-series project as the destination. Rank candidates:

1. an active destination explicitly named in the transcript, including purpose folders such as `To Discuss` or `Backlog`;
2. a dedicated active domain or operations container matching the deliverable;
3. the closest active project or epic parent of the exact item discussed in the meeting;
4. the meeting's broader workstream or series.

A MoM's location is provenance, not a default destination. Material to be shared is context, not automatically the parent of a handoff task. Dates and “this sprint” are schedule, not placement. Prefer a durable domain project over a sprint folder unless speakers explicitly place the work there. Same owner, a shared prefix, or one keyword is not proof of fit.

If the referenced item is Completed or Cancelled and is itself the same deliverable, use Already represented or update it. If it is only context for different new work, walk up to its active project or epic. Never create under a Completed or Cancelled parent.

When several candidates remain, compare people, scope, active state, and similar siblings. If none is clearly best after those checks, use Needs your input with at most three names and permalinks. Different signals may have different destinations.

## Supported updates

- **Dates:** copy the signal’s ISO Due exactly. `none` means set no due date. Never borrow a nearby date from the Date map or another signal.
- **People:** use the accepter from `Who`, not the requester, facilitator, or connected user. Map transcript labels such as `Me` to a participant, then resolve one active Wrike user. Use the connector's exact display name and ID everywhere, including Needs-input proposals; transcript spelling alone is unresolved. If search is ambiguous, keep the owner unresolved. Change existing assignees only for an ownership signal.
- **Statuses:** inspect the item’s workflow and resolve an exact status ID.
- **Descriptions:** fetch the complete description and preview the full replacement or an exact diff.
- **Custom fields:** resolve the field ID, type, and allowed value. Clear only when explicit.
- **Comments:** use only for information that belongs on an exact item but has no canonical field. A comment is never enough for a commitment whose work is absent.

## Preview

Give every signal exactly one visible outcome in these sections:

1. **Ready to apply** — fully resolved update or safe creation.
2. **Needs your input** — one missing choice, with candidates and the precise question.
3. **Already represented / no action needed** — name and link the evidence.
4. **Not tracked** — only explicit `non-action` signals.

Show all four sections; write `None` under an empty one.

Use this Ready table:

| Row | Signal | Action | Wrike item | Change | Basis |
|---|---|---|---|---|---|

- Label operations `M1`, `M2`, … and include one signal ID per row.
- Existing-item actions include the exact ID and permalink.
- Creations include title, item type, active parent, assignee, status, and due date.
- Show complete comment text and description changes below the table.
- A Ready row must have every required ID and value resolved.
- **Basis** — the signal’s Evidence quote and why this item or parent is the right target.

Before showing the preview, audit every Ready Create:

- Does the transcript contain direct acceptance by the named owner?
- Did both close-title and broader duplicate searches run across all states?
- Did an MoM action row or checklist already record the same owner and deliverable?
- Is the chosen parent an active domain project rather than an incidental sprint or completed item?
- Is Due copied from that signal, including `none`?

Move any row that fails an audit question to Already represented or Needs your input.

Finish with a conservation line that lists every signal exactly once:

```text
S1–S4 → Ready S2 · Needs input S1 · Already represented S3 · Not tracked S4
```
