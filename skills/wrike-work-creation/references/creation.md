# Building the structure

`SKILL.md` specifies when this route applies and has the shared rules on asking,
previewing and confirming. The tool descriptions define each tool's parameters
and limits. This file adds what designing a structure needs on top of both.

## Say what the request did not

Pull five things out of the request:

- the deliverable, in the requester's own words;
- the date, and whether it is a commitment or an aspiration;
- who the work is for;
- anything stated as a constraint rather than a preference;
- who signs off, which is often not the person asking.

Then list what the request left open. Usually that is the budget, the real
deadline behind a soft one, the guidelines the work must follow, and which of
two readings of an ambiguous line is meant.

Ask about ambiguity, not only about gaps. "The brief says localized: is that
four languages or twenty-four? It moves the timeline by a month" is worth more
than a general request for clarification. Anything you would otherwise have to
invent goes on the list of questions.

If the request came through a request form, the form's answers are structured
data and better evidence than the free-text field below them.

## How to use existing tools

The account already has conventions. Four reads show them:

| Call                                                                       | What it tells you                                                                                                                  |
|----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| `get_items_children` on the space                                          | how the space divides itself in terms of folders, projects, and tasks.                                                             |
| `search_customitemtypes` without `spaceId`                                 | which item types exist across the account (a `spaceId` would hide the account-wide ones); `usageCount` shows which are really used |
| `search_items(parentItemId: <a comparable project>)`                       | how deep real work goes, and how titles are written                                                                                |
| `get_item_details` on two or three of those, with `fullDescriptions: true` | the house description style, and which fields are filled at which level                                                            |

A read that was cut short (`truncated`) is not the convention. Read further
before you copy it.

Copy the naming style. If every project is `[CLIENT] Q3 Campaign`, match it.
If task titles start with a verb, `Draft the brief`, do not write
`Brief drafting`. A structure that reads like its neighbors gets adopted.

## Decide the shape

Three decisions. Each default holds until the request says otherwise, or until
the sibling items show a different convention.

**How many levels: three.** A project, the projects inside it, and the tasks
inside those. Add a fourth only when one level would otherwise hold more than
about fifteen children, or when two teams own different parts of it. Drop to a
flat list of numbered tasks only for a backlog that genuinely has no stages.

**What the middle items are: projects.** Anything with a schedule, an owner or
a budget of its own is a project. Use a task with subtasks only when that level
is nothing more than a checkpoint: one date the rest of the work waits on, and
nothing else. A project's dates are yours to set and yours to keep current;
they do not follow its children.

**Which item type: the account's custom item type that plainly fits.** It tells a reader
what the item is and makes it findable by type. Choose from the account-wide
list you read in [*How to use existing tools*](#how-to-use-existing-tools),
prefer the types the team really uses, and say which one you picked and why.
If nothing clearly fits, use a plain task or project — never the
nearest-sounding type, which puts the item in somebody's filtered view where
it does not belong.

## Show it before you create

The preview rules in `SKILL.md` apply unchanged: one table, every value
sourced, assumptions named. A structure adds three rules:

- **Every deliverable traces to something**: the request asked for it, the
  account's convention always includes it, or the work cannot happen without
  it.
- **Milestones are dates other people plan around.** If nobody outside the
  delivery team cares about a date, make it an ordinary task with a start and
  a due date, not a milestone.
- **The last milestone is the deadline.** A structure that ends after the
  requested date is a finding: put it above the structure, not inside it.

Do not create anything while questions are still open.

## Write it top down

Create parents before children. A child needs its parent's real ID; a
placeholder such as `parentId: "tmp:1"` is not resolved.

Plan the calls around what each tool can set:

- **Project dates come after creation.** `create_project_folder_item` sets no
  dates, so each phase project gets its dates from `update_items`.
- **`update_items` sends the same values to every id in a call**, so a
  different date per phase means one call per date. Put everything that
  differs per item into the create call, where each entry carries its own
  values.
- **Some fields are update-only**: custom fields, importance, a custom status
  and a second task assignee. Group the IDs that share a value, say how you
  grouped them and how many calls that makes, and never make one call per item.

To learn which custom fields a type has, read the type with
`search_customitemtypes`, not an item: `get_item_details` shows only fields
that already hold a value. Items can carry more fields than their type
declares, so treat the type's list as the minimum.

## Read back what you wrote

A create call takes a list and can partly succeed, so check every row before
you report the tree. A row that reports success can still be wrong without any
error:

- **Re-read the dates.** Wrike may store a date other than the one you sent,
  and a milestone placed on the committed date may now sit past it. Report
  what you read back, not what you sent.
- **Re-read any custom field you set.** A field that did not apply can report
  success and simply be absent.
- **Check the status if it matters.** Tasks nested under a task do not always
  carry the workflow status that a status-filtered search looks for.

`search_items` returns one page at a time, and its hits carry no dates or
descriptions. Page through the whole result, and use `get_item_details` for
dates and descriptions.

## Titles and descriptions

**Titles carry the order, because nothing else can.** No tool sets or reads the
display order. Number the titles with zero padding, `01`, `02`, … `10`,
because unpadded numbers sort `10` between `1` and `2`. Copy the numbering
punctuation the siblings already use.

**Descriptions are HTML.** Markdown is stored as literal text, so send real
tags. The house style is a bold label and a line break:

```html
<b>Done means</b><br />The endpoint returns a signed URL and the file appears on the item.<br />
```

**A description answers what the title cannot, for its own level only.** Put
each fact on exactly one level:

| Level | Holds | Never holds |
|---|---|---|
| The top project | why the work exists, what done means, what is out of scope, who decides | the list of work below it |
| A project inside it | what must be true to call that part finished | a restatement of the project above |
| A task | the one output, and how you know it is finished | context readable one level up |
| A subtask | usually nothing | anything |

Six to ten lines on the top project, one or two on a task, none on a subtask.

Repeat the deadline on the project, the project below it and every task, and
one change becomes four edits, three of which will not happen when the date
moves. The next reader then sees three different dates and believes the wrong
one.

To test a sentence, delete it. If someone looking at that item, and one level
up, has lost nothing they need, leave it out.

Never restate the title as a sentence: not "This task involves", not "The goal
of this task is to". If a task needs a third paragraph, that content belongs on
the parent, or the task should be two tasks.

## Where this stops

Leave assignment alone. Who does the work is a separate decision, and the
requester may want to make it differently. Name the roles the work needs, not
people.

Give the estimate, label it a planning number rather than a commitment, and say it has
to be set in the Wrike UI. Do not leave it out because you cannot write it, and
do not imply you wrote it.
