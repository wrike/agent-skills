# Board delivery and verification

Read this after the first compiler run produces a manifest with no errors.

The compiler intentionally renders task cards as `SHAPE` items with `h4`–`h6` markup so their Wrike links and task identifiers remain recoverable. Assignee cards likewise retain the user identifiers needed by application mode. Preserve those generated representations; do not replace task cards with `IDEA` items.

## Deliver

1. Create the whiteboard with `manifest.board.title`.
2. Recompile with its id: `<python> scripts/compile_board.py INPUT.json --out PLAN_DIR --board-id BOARD_ID`.
3. In parallel, send a canary wave containing the first step 1 batch, first available step 3 or 5 batch, and first step 7 batch. Skip absent categories.
4. Check `summary.failed`, the step 3/5 echo for card HTML, and the step 7 echo for its full Wrike link id.
5. If the canary succeeds, send all remaining batches in bounded parallel waves that respect the live tool's current limits; do not wait for one generated step to finish before starting another.
6. Classify failures before recovery. Correct validation failures before retrying; stop and report permission or not-found failures; retry only failed items after retryable, throttling, or transient failures. If a create outcome is unknown, inspect the board before retrying and stop rather than risk duplicates when the result cannot be determined.

If the checked echo strips `<h4>`–`<h6>`, `<a>`, `<em>`, or alignment `<div>` tags, stop drawing and report the board incomplete.

## Verify and repair

In parallel, call `list_whiteboard_items` with `perPage: 1` for `SHAPE`, `TEXT`, and `IDEA`.

- Compare the reported totals with `manifest.expectedTotals`.
- `IDEA` must be zero; the compiler never creates IDEA items.
- On a mismatch, list only that type in full and repair missing or duplicate generated items.
- After two repair passes, stop and report incomplete bands.

Generated batches are order-independent because every item has explicit coordinates and z-order. During creation or repair, do not hand-edit compiler-owned layout, colors, markup, widgets, or option labels, and do not add a separate option-name legend. Fix the input or compiler and recompile instead. After delivery, the user may move task cards between assignee columns; application mode intentionally reads those current positions. Do not alter or remove the option panels, assignee cards, Wrike links, embedded identifiers, or rendered attribute values needed to interpret the board.

## Deliver by origin

- Wrike-origin: always include the verified board link in the closing comment as a short HTML anchor such as `<a href="BOARD_URL">Open the staffing board</a>`; do not place punctuation directly after a bare URL. When `add_whiteboard_to_item` is available, also attach the board to the trigger item and claim attachment only after the tool confirms success. If the capability is unavailable or attachment fails, still provide the link and state plainly that it was not attached.
- Chat-origin: return the board link only. Do not attach it to a Wrike item, even when the scope contains Wrike links.

If board creation returns no share link, call `get_whiteboard_info` once. If the link is still absent, report that the board was created but could not be linked.
