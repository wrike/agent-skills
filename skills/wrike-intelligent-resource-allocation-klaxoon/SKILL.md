---
name: "wrike-intelligent-resource-allocation-klaxoon"
description: "Creates verified Klaxoon staffing boards from Wrike assignee recommendations and applies user-approved assignments from the current layout of a Klaxoon staffing board created by this workflow. In a Wrike comment agent, create a board for a project, folder, more than 10 explicitly named tasks, or an explicit visual request; do not create one for 10 or fewer explicit tasks unless visual output is requested. In other AI chats, ask once when the destination is unspecified. Use application mode only when the request is connected to an identifiable current staffing board, not for generic requests to apply recommendations. Not for standalone workload reports or free-person searches."
metadata:
  version: "1.0.0"
---

# Wrike staffing board

Choose one mode before loading references:

- **Create or rebuild a board:** read [references/create-board.md](references/create-board.md).
- **Apply the current board:** use this mode only when context identifies a current Klaxoon staffing board created by this workflow, such as an explicit link, a Wrike whiteboard attachment, or an unambiguous reply to its delivery message. Then read only [references/apply-assignments.md](references/apply-assignments.md). Do not reuse an earlier recommendation response or load rendering references unless the user also asks to rebuild the board.

For changes or distribution, read [references/package-maintenance.md](references/package-maintenance.md).

## Shared rules

- A generic phrase such as “apply these recommendations” is relevant only after the current context has established the Klaxoon staffing board it refers to. Otherwise do not use application mode and do not change assignments.
- Creating a board never changes Wrike assignments. Apply only after an unambiguous approval covered by the application reference.
- Follow live MCP tool descriptions for parameters, defaults, limits, pagination, and errors.
- Use Python 3.9 or newer for the bundled scripts. They use only the standard library and make no service calls.
- Do not inspect script source during an ordinary run; use their JSON inputs, outputs, and exit status.
