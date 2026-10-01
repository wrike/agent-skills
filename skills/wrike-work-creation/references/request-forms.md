# Request forms

`SKILL.md` has the shared rules on asking, previewing and confirming. The
request form tool descriptions define ids, field values, paging, the page
graph, prefill and errors. This file adds only what a form needs on top of
both.

If a form id does not load, do not guess another id. Search with the user's
own words, or ask for the form's title or link.

## Asking the form's questions

The wording belongs to whoever built the form, and it usually matters: it is
how the receiving team gets an answer it can act on. `SKILL.md` decides which
questions you ask and in what batches. This section decides what each question
looks like.

- **Keep the original wording.** Adjust the style lightly to suit a
  conversation, and no more. Do not summarize, do not merge two questions into
  one, and do not replace the form's terms with your own. If a question is
  unclear, quote it as written and say what is unclear.
- **Keep the question's type.** Ask a free-text field as an open question.
  Never offer a menu of options you made up: the user reads a menu as the set of
  accepted answers, so a form owner who expected a paragraph gets a label
  instead. The reverse holds too: never turn a select into an open question and
  then map the answer to an option yourself.
- **Show every option, in the form's order.** Do not shorten the list ("…and 6
  more"), reorder it by what seems likely, or merge two options into one line.
- **Keep the helper text with its question.** If the helper text was cut
  short, do not rewrite the question from the part you have.
- **Use titles and names, never ids.**

Batching does not relax any of this. Three questions in one turn each keep
their own wording, type and full list of options.

## Attachment fields

Attachment fields cannot be filled here, so they decide how the form ends.

- **A mandatory attachment on the path**: the form is finished in Wrike. Build
  a prefill URL with the answers you have, tell the user exactly what to
  attach, and say the request exists only once they submit it there. If you
  have no answers to pre-fill yet, point them to the form in Wrike by its
  title, with its link if the user shared one.
- **An optional attachment**: say it is optional and offer two ways: submit
  now and attach the files to the created item afterwards, or open a prefill
  URL and attach them there. Let the user choose.

Files the user wants on the new item are added after the submit. Follow
[`attachments.md`](attachments.md).

## Resubmitting

A resubmit after a failed submit needs its own preview and yes (see *Preview*
in `SKILL.md`). In that preview, say which field you changed.
