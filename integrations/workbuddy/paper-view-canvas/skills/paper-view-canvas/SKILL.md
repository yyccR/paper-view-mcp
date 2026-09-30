---
name: paper-view-canvas
description: Generate images with Paper View Board and open its SVG canvas.
---

Connect through the Paper View website OAuth page at `https://ipaperview.com` before calling paid tools. Use `list_image_models` to check model and image-size support. Use `quote_image` to report the current Credit cost before a requested generation. Submit with `submit_image`, retaining the returned `job_id` and a stable `client_request_id` for retries. Poll `get_image_job` until completed or failed. Use `open_canvas` for a session's compact editable board URL. Open `board_url` in WorkBuddy's browser panel if available, or provide a clickable link. The generated raster image can be arranged with SVG elements in the board; do not claim the image pixels are vectors. Never place tokens in tool arguments or chat text.
