# Attaching files

Files the user wants on an item this skill creates are attached once that item
exists, whichever route created it.

`SKILL.md` has the shared rules on previewing and confirming. The
`prepare_attachment_upload` and `add_attachments_to_item` tool descriptions
define the upload itself. This file adds only what attaching needs on top of
both.

1. If `prepare_attachment_upload` and `add_attachments_to_item` are not in your
   tool list, upload is not enabled for this account. Give the user the item's
   permalink and tell them to drop the files onto it in Wrike.
2. The upload is an HTTP PUT of the file's bytes that your client sends itself,
   outside the MCP. If your client cannot send file bytes, say so and hand off
   with the permalink. Do not reserve upload ids that nobody will use.
3. Otherwise, show the preview and get a yes before you reserve anything, since
   `add_attachments_to_item` is one of the create calls in `SKILL.md`. Then
   follow the two tools' descriptions.

Either way, give the user the created item's permalink and tell them they can
also drop files onto it in Wrike. Do not leave the attachment as the one part
of the request nobody answered.
