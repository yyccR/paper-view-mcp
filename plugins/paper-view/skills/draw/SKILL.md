---
name: draw
description: Draw and revise editable SVG diagrams progressively on Paper View Board, or generate raster images.
---

Use the Paper View Board MCP server for image generation and canvas links. If the MCP server needs authentication, tell the user to select Authenticate in Codex or run `codex mcp login paper-view-canvas`. The sign-in page must be on `https://ipaperview.com`. Wait for the connection to finish before calling paid tools.

For an agent-authored mechanism diagram or other editable vector drawing:

1. Treat one figure as one SVG object when it should be selectable, downloadable, and editable as a whole. Plan logical sections inside that SVG using independent vector elements and one fixed numeric `viewBox`. Call `start_drawing` once, or reuse the known `session_id` from the same canvas.
2. Call `draw_svg_layer` once for the initial stage and retain its `artifact_ref` and `revision`. For each later stage, call `get_svg_layer`, then `update_svg_layer` with that same `session_id` and `artifact_ref`, the latest `revision` as `base_revision`, and the **complete cumulative SVG**. Keep earlier content and add the new section; this interface replaces the document rather than appending or merging fragments. The open canvas can still show progress as that one object receives revisions. Use a stable UUID `client_request_id` for each new submission and reuse it only for retries of the exact request. Read a local `.svg` file and pass its text without an XML declaration; the remote server cannot read a local path.
3. Draw with the MCP SVG subset described in [SVG compatibility](references/svg-compatibility.md). Set presentation attributes directly, use local gradient and marker definitions, and avoid unsupported SVG/CSS constructs. In particular, `marker-mid` and `gradientTransform` import but prevent editable PPTX export in tested drawings; draw middle arrowheads as polygons and set gradient coordinates directly. Keep elements that must stay precisely aligned in one SVG layer, because separate layer imports may be placed independently by Board.
4. Call `inspect_drawing` after important stages. A single progressively drawn figure should have one `artifact_ref` with increasing revisions. Each additional `draw_svg_layer` creates an independent board object; sharing a `session_id` and `viewBox` does not combine those objects. Add separate objects only for independent figures, explicitly requested separate layers, or drawings that exceed the per-object limits; explain that these require separate selection/export unless actually combined and verified.
5. Open the first `board_url` once and keep the panel open while revisions synchronize. After the final stage, verify one selection covers the whole figure, its selected-object SVG download includes every section, and one click on Edit exposes vector elements across the figure. Exit edit mode to restore whole-object selection. If a user has modified the object locally or a revision conflicts, inspect before proceeding and preserve their changes. `get_svg_layer` reads saved agent source and does not prove that local edits were merged; do not force replacement.

Example: create stage A once → read the returned ref → update the same ref with A+B → read its latest revision → update the same ref with A+B+C. Use a new create call for a separate figure, not for section B or C of this figure.

Do not claim that a create or update is visible until the open board has synchronized or `inspect_drawing` shows the saved canvas revision. For visual review, use the board's thumbnail or inspect its saved SVG. A successful SVG upload does not prove PPTX conversion: when editable PPTX is a requested deliverable, verify the selected element's PPTX download in Board. The whole-board PPTX export is a single image. SVG layer tools do not consume image-generation Credits.

1. Call `list_image_models` when the model or size is unclear.
2. Call `quote_image` before a paid generation when the user asks about price or has not chosen a size.
3. Call `submit_image` once with a stable `client_request_id` UUID. Reuse that ID when retrying a timed-out submission. For a follow-up change, pass the prior result's `session_id` so the new image appears on the same canvas. Omit `session_id` only when the user starts a separate canvas; use `list_image_jobs` to recover it if needed.
4. Poll `get_image_job` until the status is `completed` or `failed`. A completed result includes the image URL, artifact reference, Credit receipt, and canvas URL.
5. Open the compact editable board once for the first completed image. Use `open_canvas` only when the session link needs to be recovered.

For follow-up jobs in the same session, keep the existing browser panel open. The canvas imports new results automatically; do not open `board_url` again. If no panel is open, provide the clickable link. MCP cannot force a panel position. Never ask for an API Token in chat or put one in prompts, tool arguments, or canvas links. The generated image is a raster element on an editable SVG canvas; do not describe its pixels as vector-editable.
