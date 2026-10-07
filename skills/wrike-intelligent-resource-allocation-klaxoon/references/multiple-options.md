# Multiple options

Read this only when the compiler manifest contains more than one scenario summary.

- Named scenario labels must already be present in `manifest.scenarioSummaries` from the pre-delivery check. If they are missing or mismatched, fix `parameterLabels` and recompile; never add a separate legend or text item to the board.
- Let the compiler render each option and the “Comparison of options” panel. Do not reproduce that comparison manually or alter its ordering.
- Describe tradeoffs factually. Never rank, endorse, or silently select an option.
- In the final response, point the user to “Comparison of options” and offer to apply the option they choose.
- When the user later asks to apply `Option A`, `Option B`, and so on in the context of this board, that request approves the option's current layout. Follow [apply-assignments.md](apply-assignments.md): read the board again and derive assignments from current card positions rather than the earlier recommendation response.
