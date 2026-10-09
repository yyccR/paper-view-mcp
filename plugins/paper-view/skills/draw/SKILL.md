---
name: draw
description: Draw editable SVG diagrams in layers on Paper View Board, or generate raster images.
---

Use the Paper View Board MCP server for image generation and canvas links. If the MCP server needs authentication, tell the user to select Authenticate in Codex or run `codex mcp login paper-view-canvas`. The sign-in page must be on `https://ipaperview.com`. Wait for the connection to finish before calling paid tools.

For an agent-authored mechanism diagram or other editable vector drawing:

1. Plan the major visual layers and use one consistent numeric `viewBox` across them. Call `start_drawing` once, or reuse a known `session_id` from the same canvas.
2. Create each layer as complete SVG text without an XML declaration and call `draw_svg_layer` with a stable `client_request_id` UUID. Read a local `.svg` file and pass its content; a local path is not available to the remote MCP server. Submit one logical layer at a time so the open canvas can show progress.
3. Draw with the MCP SVG subset described in [SVG compatibility](references/svg-compatibility.md). Set presentation attributes directly, use local gradient and marker definitions, and avoid unsupported SVG/CSS constructs. In particular, `marker-mid` imports but prevents editable PPTX export; draw those arrowheads as polygons. Keep elements that must stay precisely aligned in one SVG layer, because separate layer imports may be placed independently by Board.
4. Call `inspect_drawing` after important stages. Use `get_svg_layer` to read source and revision before changing a prior layer; send the whole revised SVG to `update_svg_layer` with `base_revision` and a new stable request ID. On a revision conflict, inspect the drawing again before retrying.
5. Open the first `board_url` once. Subsequent layers appear in that canvas automatically; keep the panel open. The user can edit the vector elements in Board. If a user has modified a layer locally, the board preserves it and reports a conflict rather than replacing it automatically.

Do not claim that a `draw_svg_layer` call is visible until the open board has synchronized or `inspect_drawing` shows the saved canvas revision. For visual review, use the board's thumbnail or inspect its saved SVG. A successful SVG upload does not prove PPTX conversion: when editable PPTX is a requested deliverable, verify the selected element's PPTX download in Board. The whole-board PPTX export is a single image. SVG layer tools do not consume image-generation Credits.

1. Call `list_image_models` when the model or size is unclear.
2. Call `quote_image` before a paid generation when the user asks about price or has not chosen a size.
3. Call `submit_image` once with a stable `client_request_id` UUID. Reuse that ID when retrying a timed-out submission. For a follow-up change, pass the prior result's `session_id` so the new image appears on the same canvas. Omit `session_id` only when the user starts a separate canvas; use `list_image_jobs` to recover it if needed.
4. Poll `get_image_job` until the status is `completed` or `failed`. A completed result includes the image URL, artifact reference, Credit receipt, and canvas URL.
5. Open the compact editable board once for the first completed image. Use `open_canvas` only when the session link needs to be recovered.

For follow-up jobs in the same session, keep the existing browser panel open. The canvas imports new results automatically; do not open `board_url` again. If no panel is open, provide the clickable link. MCP cannot force a panel position. Never ask for an API Token in chat or put one in prompts, tool arguments, or canvas links. The generated image is a raster element on an editable SVG canvas; do not describe its pixels as vector-editable.
