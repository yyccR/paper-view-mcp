---
name: paper-view-canvas
description: Generate images with Paper View Board and refine them on its SVG canvas.
---

Use the Paper View Board MCP server for image generation and canvas links. If the MCP server needs authentication, tell the user to select Authenticate in Codex or run `codex mcp login paper-view-canvas`. The sign-in page must be on `https://ipaperview.com`. Wait for the connection to finish before calling paid tools.

1. Call `list_image_models` when the model or size is unclear.
2. Call `quote_image` before a paid generation when the user asks about price or has not chosen a size.
3. Call `submit_image` once with a stable `client_request_id` UUID. Reuse that ID when retrying a timed-out submission.
4. Poll `get_image_job` until the status is `completed` or `failed`. A completed result includes the image URL, artifact reference, Credit receipt, and canvas URL.
5. Call `open_canvas` to get the compact editable board link for an existing session.

When a job completes, open its `board_url` in the client's side browser panel if one is available. Otherwise provide the clickable link. MCP cannot force a panel position. Never ask for an API Token in chat or put one in prompts, tool arguments, or canvas links. The generated image is a raster element on an editable SVG canvas; do not describe its pixels as vector-editable.
