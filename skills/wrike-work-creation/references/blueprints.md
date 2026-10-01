# Blueprints

A blueprint is a reusable template. Launching one creates a real tree of
folders, projects or tasks, and nothing here can undo it.

`SKILL.md` has the shared rules on asking, previewing and confirming. The
`search_blueprints` and `create_item_from_blueprint` tool descriptions define
every parameter, default, limit and error. This file adds only what a launch
needs on top of both.

## Destination

The destination must come from the user, on every launch. That includes a
second launch later in the same chat: do not reuse the earlier destination
without asking.

1. If the request names no destination, ask for a link or a name.
2. Resolve a named place to its id before the preview.
3. If the user still gives none, leave `parentId` out and show "your Personal
   space" as the destination in the preview.

## Settings to ask about

- **Title**: if the user gave none, propose one and ask.
- **Notify assignees**: if the user has not said, ask. Do not rely on the
  default.
- **Schedule**: say in plain words what the date anchors (see
  `rescheduleMode`), as example 2 in `SKILL.md` does.
- **Any other setting**: if the conversation touches it but does not settle
  it, ask, and list the choices instead of asking an open question.

## Description

The launch cannot set a new description. If the user wants one, set it with
`update_items` after the launch. That is a separate change, with its own
preview and yes.

## Attachments

Files the user wants on the new item are added after the launch. Follow
[`attachments.md`](attachments.md).

## Preview

Use the preview table from `SKILL.md` with these rows: the blueprint (title and
permalink), the root item title, the destination, whether assignees are
notified, and every other setting you are sending. Name assignees only if you
have read them.

A search hit says nothing about the tree the launch will build. Say that the
preview covers only the title and the settings you are sending, and do not
describe a structure, a child count or an assignee list you have not read. If
the user wants to look inside first, read it with `get_items_children` and
present only what you read, never as the whole tree unless you read all of it.
Or give them the blueprint's permalink to open in Wrike.

## After the launch

When you poll a launch with `get_asyncjob` (see *After the call* in
`SKILL.md`), a `FAILED` result always says nothing was created. For a launch
that is not necessarily true, so go by `progressPercent` instead. At 0, nothing
was created. Above 0, part of the tree may exist: check the destination before
offering to launch again, and never launch over a partial tree.
