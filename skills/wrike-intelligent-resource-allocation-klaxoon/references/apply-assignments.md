# Apply the current board

Read this only when context identifies a current Klaxoon staffing board created by this workflow and the user asks to apply its assignments. A generic request to “apply recommendations” outside that context does not activate this mode and does not authorize a Wrike write.

Do not call `recommend_resources` again. The current board layout is the source of truth because the user may have moved task cards between assignee columns after reviewing the recommendations.

## Read the current layout

1. Locate the board from its explicit link, the trigger item's whiteboard attachment, or the unambiguous board-delivery message being answered. If no board is identifiable or more than one board is plausible, ask which board to use.
2. List every current `SHAPE` item on the board, following the live tool's pagination instructions. Record the reported total and make sure every page belongs to this fresh read; do not use an earlier board read.
3. Save the page responses verbatim in UTF-8 JSON:

   ```json
   {
     "option": "Option A",
     "expectedShapeCount": 123,
     "shapeResponses": []
   }
   ```

   Set `expectedShapeCount` to the total reported by that read. Omit `option` for a single-option board. For a multi-option board, use the option identified by the user.
4. Run `<python> scripts/compile_assignments.py BOARD_INPUT.json --out ASSIGNMENT_PLAN.json`.
5. Read only `ASSIGNMENT_PLAN.json`. Any `errors` block all Wrike updates. Do not guess when the read is incomplete, a generated card lacks exactly one required id, a task lies outside every option's horizontal span, or its position does not clearly identify one assignee column.

The parser identifies option panels left to right, reads each task id from its Wrike link, reads each assignee id from the assignee card, and assigns a task to the assignee column matching its current horizontal position. Option ownership and assignee choice are horizontal: a task card that has been moved below the visible bottom of an option frame is still valid when it remains below the assignee headers and clearly within that option's assignee column. Do not ask the user to move or revert such a card merely because it extends below the background frame. Moving a task card to another assignee column therefore changes the assignment that will be applied. The parser may produce more than one assignee for a task when the selected option contains multiple cards for that task.

## Approval

- A direct request to apply a named option from the identified current board approves the exact assignments currently positioned in that option. Do not repost the full list or ask for another confirmation.
- When the identified board contains one option, an unambiguous reply in that board's context such as “apply these assignments,” “apply the recommendations,” or “go ahead with this plan” approves it. The same words outside an identified Klaxoon staffing-board context do not.
- When the identified board contains multiple options, a generic request is ambiguous. Ask which option unless the surrounding message clearly identifies one.
- If the board or option cannot be resolved, ask a concise clarification. If the user changes the board after approval but before application, use the latest state only when their instruction clearly covers those changes; otherwise ask again.

## Apply

1. For each entry in `updates`, call the Wrike MCP `update_items` tool in batches that follow its current live limit, with the entry's `taskIds` and `addAssignees: [userId]`.
2. Preserve existing assignees. Never remove an assignee unless the user explicitly asks.
3. Report failed updates precisely. Do not claim the board was fully applied if any batch failed.
4. Return the board link. Applying assignments does not require rebuilding the board unless the user asks for an updated visual.
