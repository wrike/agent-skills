# Operation Rules, Bulk Execution, and Results

Read this before executing any approved row. It defines exactly how each operation type behaves, how to run bulk approvals safely, and how to report outcomes.

## Contents

- Per-operation rules (comments, due dates, creation, statuses, people, descriptions, custom fields)
- Bulk execution and dependencies
- Results reporting

## Per-operation rules

### Comments

- Read recent comments and return `No change` if the exact signed comment already exists.
- Use the approved signed text exactly as previewed.

### Due dates

- Preserve the existing start date.
- Do not schedule an unscheduled task, clear dates, or change duration unless that was separately previewed and approved.

### Creation

- Require an exact parent, a standard item type, and an explicit title.
- Refuse the operation if the parent's status category is Completed or Cancelled; report it rather than creating there.
- Populate only previewed values supported by the notes or by direct user instruction.
- After an uncertain creation, search once for the result and do not retry blindly.

### Statuses

- Require an exact target and a resolved workflow status (not a display label).
- Completion and cancellation require explicit support from the notes or direct user instruction.

### People

- Use only uniquely resolved Wrike user IDs.
- Apply exactly the previewed additions and removals.

### Descriptions

- Read the full current description first.
- Apply the complete previewed replacement, preserving existing content unless replacement was explicit.

### Custom fields

- Use the resolved field ID, the correct value format, and an allowed option when applicable.
- Clear a field only when clearing was explicitly previewed and approved.

## Bulk execution

One approval may authorize multiple rows. Execute approved rows sequentially or in dependency order, revalidating and verifying each row as you go.

- Create a parent before any approved child rows that depend on it.
- Skip dependent rows when their prerequisite fails or is uncertain.
- Continue after independent `Conflict` or definite `Failed` rows.
- Stop remaining execution after an `Uncertain` result, and never retry an uncertain mutation automatically.

Bulk approval is not an atomic transaction; partial success is possible, so the results table is how the user learns exactly what landed.

## Results

Report every selected row:

| Row | Result | Wrike item | Observation |
|---|---|---|---|

Use one of `Applied`, `No change`, `Conflict`, `Failed`, `Uncertain`, `Skipped`, or `Pending`. Re-read created or updated items and comments before reporting `Applied`, so the status reflects verified Wrike state rather than an assumed success.
