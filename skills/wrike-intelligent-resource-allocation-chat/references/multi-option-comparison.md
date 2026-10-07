# Compare multiple options

Keep `Option A`, `Option B`, and `Option C` tied to returned order. Compare them using these columns:

`Option | Items with assignees | Assignees | Items not assigned | Items with partial match | Assignees over capacity`

For each task, compare the complete sorted set of `(assignee, fit)` rows plus the count and reasons of its items not assigned. Include every task that has an item not assigned in all options and every task whose assignments, fits, or items not assigned differ between options. Omit only tasks that have the same assignees at 100% fit and no items not assigned in every option.

Order comparison rows by attention priority:

1. Has at least one item not assigned in every option.
2. Has at least one item not assigned in some options.
3. Has a 0% assignment in any option.
4. Has requirements explicitly not set or a fit not reported in any option.
5. Has a partial fit; sort by the lowest numeric fit ascending.
6. Has different assignees, all at 100% fit.

Break ties by task title. This is a categorical sort, not a new score.
