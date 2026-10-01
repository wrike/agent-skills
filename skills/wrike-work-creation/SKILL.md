---
name: wrike-work-creation
description: >-
  Work intake and creation in Wrike. Use when somebody wants to submit or
  fill a request form, clone or launch a blueprint or template, file a
  request, process or ticket, or turn a brief or RFP into projects and
  tasks.

  Also use when somebody only states a work need — new-hire equipment,
  access, onboarding, a campaign, a process to kick off — or pastes a form
  link (#/forms?formid=) or a numeric form id. The need does not have to
  name Wrike.

  This skill is not for creating a single plain task, folder or project in a
  place the user already named — create it directly with the Wrike tools.

  This skill is not for reading, searching, updating or commenting on
  existing items.

  This skill is not for a meeting transcript, notes or recap — those belong
  to wrike-meeting-intelligence and wrike-meeting-sync.
license: MIT
compatibility: >-
  Needs the Wrike MCP. Request forms, blueprints and attachment upload are each gated by
  their own account feature, so their tools may be absent; when a route's tools are
  missing the skill says so and falls back to the routes that are available rather than
  guessing. Uploading a file also needs a client that can PUT raw bytes to a signed URL
  outside the MCP.
metadata:
  version: 2026.9.30
---

# Work creation: pick the route, then build

Three routes lead into Wrike, depending on whether a shape for this work
already exists:

| | Route | When | Reference |
|---|---|---|---|
| 1 | **Request form** | the account has a form for this kind of request | [`references/request-forms.md`](references/request-forms.md) |
| 2 | **Blueprint** | a template already holds the structure and only needs launching | [`references/blueprints.md`](references/blueprints.md) |
| 3 | **Build it** | neither exists, so the structure has to be designed | [`references/creation.md`](references/creation.md) |

Read a route's reference file once the user picks that route, or names it
outright, before its first question or tool call. If the user wants files
attached to what you create, also read
[`references/attachments.md`](references/attachments.md), whatever the route.

Nothing created here can be undone: the MCP has no delete tool, and removing
an item's parents only orphans it. So every route previews what it will create
and waits for an explicit yes.

This skill decides the route, the questions and the confirmation. Tool
descriptions decide ids, payloads, paging and errors.

## Choosing the route

If the request is too vague to search for, ask one clarifying question first.
Then:

- A request form link (it contains `#/forms?formid=N`), or a number the user
  calls a form: route 1. Load it with `get_requestform` as `w:rf:N`, without
  searching, and confirm it by its title.
- An item link (`open.htm?id=N`) that the user calls a template or blueprint:
  check it with `search_blueprints(permalink=…)`. If it resolves, it is route
  2; confirm it by its title.
- Anything else: run both `search_requestforms` and `search_blueprints`. A
  need that another team has to accept (*get me a license*, *I need access to
  X*) is intake even when nobody says "form" or "template", so search before
  creating a task.

With the search results:

- Rank the hits from both searches by how well title, description and fields
  or structure match the request. A relevant blueprint stays a candidate next
  to a matching form.
- Recommend the best hit with a *why* written for this request, not copied
  from its description, plus up to two ranked alternatives. When a form and a
  blueprint fit equally well, lead with the form. Wait for the user to pick.
- If nothing matches, rephrase and search again, up to five searches per tool.
- If still nothing fits, say so and look for intake elsewhere: run
  `search_items` for a standing task with instructions, and ask the user for
  the exact title or a link. Offer to build from scratch only after that.

## Ask, confirm, or fill

For each value the call needs, apply the first row that matches:

| The value is                                                 | Do |
|--------------------------------------------------------------|---|
| stated by the user, or in a file they shared                 | Fill it. |
| not stated, and nothing the user said or shared points to it | Ask for it. |
| inferred, critical, uncertain or branching logic             | Confirm it before the preview. |
| inferred, and none of those                                  | Fill it, marked *assumed* in the preview. |

- **Inferred**: derived rather than said, such as "next sprint" as a date or
  "a designer" as the *Design* option. Relative dates are always inferred.
- **Critical**: dates, budget and finance fields, the owner or assignee, the
  destination.
- **Branching logic**: it decides which form pages or fields come next, or what a
  launch creates. Settle it before the questions that depend on it.

Treat form fields and optional tool parameters differently:

- **Form fields**, optional ones included, go through the table. An optional
  field the user skipped, or asked you not to ask about, stays empty.
- **Optional tool parameters**, such as a blueprint's copy settings, keep the
  tool's default. Ask about one only when the request touches it or when it
  materially changes the result, like whether a launch notifies assignees.

Ask one form page or one topic per turn, in the form's own wording and options
(see *Asking the form's questions* in
[`references/request-forms.md`](references/request-forms.md)). A comment the
user adds mid-flow is input: apply it and carry on.

## Preview

Before a creation call that is part of the current workflow
(`submit_requestform`, `create_item_from_blueprint`, `create_task_item`,
`create_project_folder_item`, `add_attachments_to_item`), show one table of
every value that call will send: names rather than IDs, each with its source
(*from you*, *from <the file they shared>*, *assumed: <why>*, or *suggested by
me*). Under the table, list the assumed values again, then any field you
considered but are leaving empty, with the reason; those fields are not sent.
For a blueprint, add that the launch creates a whole item tree that cannot be
undone from here.

Then stop. Make the call only after the user answers this preview with an
explicit yes; the message that started the flow ("submit it") is not that yes,
and a retry after a failure needs a new preview and yes.

## After the call

- If the call is still running when the tool returns (a `PROCESSING` status or
  a timeout), poll `get_asyncjob` and report progress; calling again creates a
  duplicate.
- Report the created item as `[title](permalink)` from the tool's response,
  and say what the user can do next.
- Name what the tools could not do (sharing, effort, followers, and
  attachments when the upload tools are missing) instead of presenting a
  partial result as done.
- On an error, explain it and offer the real options (retry, another route, or
  finishing in the Wrike UI) with their trade-offs. Ask before switching to a
  different form or blueprint.

## Building from scratch

Route 3 opens only when both searches and the check for intake elsewhere found
nothing, when the user turned down every recommendation, or when they
explicitly asked for a new structure. Building work that already has a form or
blueprint skips what the account set up for it: the form's routing and
required fields, or the blueprint's agreed structure.

## Examples

Each example is one complete run, from the request to the report, with its own
`<inputs>` and an `<explanation>` of what to take from it. Names, ids and fields
are made up.

```xml
<example id="1" title="Request form: a need, no route named">
<inputs>
<current_date>Wednesday, 30 September 2026</current_date>
<context>The attached offer-letter.pdf names Anna Schmidt as the manager.</context>
</inputs>
<user>Lena Vogt joins as a product designer on Monday in our Berlin office. She needs a laptop and VPN, same setup as the last hire. Her manager is in the attached offer letter.</user>
<tool_calls>
search_requestforms(textSearch: "product designer joining Monday in Berlin needs a laptop and VPN") → forms: [{id: "w:rf:713431", title: "New hire equipment", …}, {id: "w:rf:702210", title: "IT access request", …}]
search_blueprints(textSearch: "new hire onboarding laptop VPN") → blueprints: [{blueprintId: "w:itm:4391170552", title: "Employee onboarding", permalink: "https://www.wrike.com/open.htm?id=4391170552", …}]
</tool_calls>
<assistant>
**Recommended: New hire equipment** (request form)
Why: it equips a new starter with both the laptop and the VPN access in one request.

Also possible:
2. [Employee onboarding](https://www.wrike.com/open.htm?id=4391170552) (blueprint): a whole onboarding project, more than you asked for.
3. IT access request (w:rf:713431) (request form): VPN only.

Shall I fill in New hire equipment?
</assistant>
<user>yes</user>
<tool_calls>
Read references/request-forms.md
get_requestform(form: "w:rf:713431") → pageIndex: [{id: "w:rfpg:k3f9x", title: "Employee", visibility: "ENTRY", …}, {id: "w:rfpg:q7m2d", title: "Equipment", visibility: "AFTER_PAGE", …}, {id: "w:rfpg:t5h8n", title: "Shipping", visibility: "ON_CONDITION", …}], pages: []
get_requestform(form: "w:rf:713431", pageIds: ["w:rfpg:k3f9x", "w:rfpg:q7m2d"], includePageIndex: false) → pages: [the Employee and Equipment pages, with their fields]
</tool_calls>
<assistant>
I have Lena's name, office and manager. Questions 1–2 of 4, from the Employee page:

1. **Start date**: you said Monday, which I read as **Monday 5 October 2026**. Is that right?
2. **Cost centre** *(optional)*: which cost centre should the equipment be charged to?
</assistant>
<user>Yes, the 5th. No idea about the cost centre.</user>
<assistant>
Questions 3–4 of 4, from the Equipment page. VPN is already ticked, from your message.

3. **Laptop model**: I can't see what the last hire got, so please pick one:
   - MacBook Pro 14-inch
   - MacBook Air 13-inch
   - Dell XPS 13
4. **How should the equipment reach the new hire?**
   - Collect at the office
   - Ship to home address (adds two questions about the address)
</assistant>
<user>MacBook Pro, she'll collect it</user>
<assistant>
This is what I'll submit to New hire equipment:

| Field | Value | Source |
|---|---|---|
| Full name | Lena Vogt | from you |
| **Start date** | Monday 5 October 2026 | from you (confirmed) |
| Office | Berlin | from you |
| Department | Design | assumed: you said "product designer" |
| Manager | Anna Schmidt | from offer-letter.pdf |
| Laptop model | MacBook Pro 14-inch | from you |
| Access needed | VPN | from you |
| How should the equipment reach the new hire? | Collect at the office | from you |

**Assumed, not confirmed:** Department is Design, because you said "product designer".

**Left empty, not sent:** Cost centre (optional), because you don't know it yet.

Submit it?
</assistant>
<user>yes, submit</user>
<tool_calls>
submit_requestform(form: "w:rf:713431", fields: [the 8 filled answers]) → status: "COMPLETED", itemId: "w:itm:4417092231"
get_item_details(itemIds: ["w:itm:4417092231"]) → items: [{title: "New hire equipment: Lena Vogt", permalink: "https://www.wrike.com/open.htm?id=4417092231", …}]
</tool_calls>
<assistant>
Submitted: [New hire equipment: Lena Vogt](https://www.wrike.com/open.htm?id=4417092231). When you know the cost centre, you can add it on that item.
</assistant>
<explanation>
- No route was named, so both searches ran; a form link or "form 713431" would have skipped them.
- The forms are named without links: `search_requestforms` returns an id but no URL, and the user gave none. The blueprint is linked with the `permalink` from its hit.
- The page ids in the second `get_requestform` call come from the first call's `pageIndex`, for the pages on the path so far.
- Questions came one form page per turn. The date was inferred and critical, so it was confirmed; Department was a confident inference, so it was marked assumed. Delivery was asked before the preview because it decides whether the Shipping page appears.
- The table holds the 8 values that were sent. Cost centre was skipped, so it is listed under the table and not sent. Only the yes to the preview allowed the submit.
</explanation>
</example>

<example id="2" title="Blueprint: a template named, with a deadline and a destination">
<inputs>
<current_date>Wednesday, 30 September 2026</current_date>
</inputs>
<user>Kick off the client onboarding template for Acme Robotics. Everything has to be done by 20 November, and it goes in the Delivery space.</user>
<tool_calls>
search_requestforms(textSearch: "kick off the client onboarding template for Acme Robotics") → nothing relevant
search_blueprints(textSearch: "client onboarding") → blueprints: [{blueprintId: "w:itm:4102556710", title: "Client onboarding", permalink: "https://www.wrike.com/open.htm?id=4102556710", …}, {blueprintId: "w:itm:4102556734", title: "Client onboarding: kickoff", permalink: "https://www.wrike.com/open.htm?id=4102556734", parentBlueprintIds: ["w:itm:4102556710"], …}]
</tool_calls>
<assistant>
**Recommended: [Client onboarding](https://www.wrike.com/open.htm?id=4102556710)** (blueprint)
Why: it's the onboarding template you named, covering the whole engagement. The other match, *Client onboarding: kickoff*, is only one part of it.

Shall I launch it for Acme Robotics?
</assistant>
<user>yes</user>
<tool_calls>
Read references/blueprints.md
search_spaces(query: "Delivery") → spaces: [{id: "w:spc:2210", name: "Delivery", …}]
</tool_calls>
<assistant>
Questions 1–3 of 3:

1. **Title** of the new project: "Acme Robotics onboarding", or something else?
2. **Schedule**: "done by 20 November" means the last task ends on **Friday 20 November 2026**, with everything before it shifted to fit. Is that right?
3. **Notify assignees** when it launches?
   - Yes (the default)
   - No, I'll tell them myself
</assistant>
<user>That title's fine, and so is the date. Don't notify anyone yet. Oh, and add Priya as a follower.</user>
<assistant>
Followers can't be set from here, so Priya needs adding in Wrike after the launch. This is what I'll launch:

| Setting | Value | Source |
|---|---|---|
| Blueprint | [Client onboarding](https://www.wrike.com/open.htm?id=4102556710) | from you |
| Title | Acme Robotics onboarding | from you |
| **Destination** | Delivery space | from you |
| **Schedule** | last task ends Friday 20 November 2026 | from you (confirmed) |
| Notify assignees | No | from you |

This creates the whole Client onboarding tree in Delivery, and it can't be undone from here. I can't see the blueprint's tasks; by default the launch copies their descriptions, assignees and custom fields, but not their attachments.

Launch it?
</assistant>
<user>go</user>
<assistant>Launching; this can take up to a minute.</assistant>
<tool_calls>
create_item_from_blueprint(blueprintId: "w:itm:4102556710", parentId: "w:spc:2210", rootItemTitle: "Acme Robotics onboarding", rescheduleDate: "2026-11-20", rescheduleMode: "END", notifyAssignees: false) → createdItemId: "w:itm:4418830127", createdItemName: "Acme Robotics onboarding", itemType: "PROJECT", baseType: "PROJECT", permalink: "https://www.wrike.com/open.htm?id=4418830127", operationId: "w:acj:7329041", …
</tool_calls>
<assistant>
Launched: [Acme Robotics onboarding](https://www.wrike.com/open.htm?id=4418830127), a project in Delivery, with the last task ending on 20 November. Nobody was notified. Next: add Priya as a follower in Wrike, and tell the team when you're ready.
</assistant>
<explanation>
- "Template" without a link names no route, so both searches ran; one blueprint clearly fits, so it is the only recommendation. The kickoff hit is called a part of it because its `parentBlueprintIds` holds Client onboarding's `blueprintId`.
- The later calls reuse ids from earlier results: `blueprintId` from the search hit, and the space `id` from `search_spaces` as `parentId`.
- The launch settings are one topic, so they were asked in one turn. The date is critical and partly inferred (the year, and "done by" meaning the end), so it was confirmed. Notifying was asked because it reaches other people and the request didn't say; the copy settings kept their defaults, which the preview spells out. The follower request, which the tool can't do, was answered at once and in the report.
- The report takes the name, the kind (`baseType` PROJECT) and the link from the launch result.
</explanation>
</example>
```
