# Paper View Board MCP

This Streamable HTTP MCP service exposes Nano Banana and GPT Image generation
through a Paper View account. Users sign in at `https://ipaperview.com` with
the normal website login. The service then connects to their existing Credit
account and Board. No API Token needs to be pasted into Codex.

## Production

Apply `core.0089_board_image_job` and `core.0090_board_mcp_login_ticket` before
starting the updated backend. The image worker must run for queued jobs.

The MCP service has its own Compose file and joins the existing production app
network. Start it before deploying the gateway image that proxies `/mcp` and
the OAuth routes. Its SQLite volume retains OAuth client registrations and
refresh tokens across container restarts.

```bash
docker compose -f integrations/mcp_server/compose.prod.yml up -d --build
```

The production plugin connects to `https://ipaperview.com/mcp`. The website
serves `/mcp/connect`; the MCP service serves `/authorize`, `/token`, `/register`,
`/complete`, `/client-info`, and the OAuth discovery endpoints through the gateway. The MCP
service is private on the Docker app network and has no published host port.

## Codex

Install `paper-view@paper-view-mcp` from this repository's marketplace.
Codex should display **OAuth** and offer **Authenticate** for this MCP server.
Select Authenticate, sign in at `https://ipaperview.com`, and confirm the
connection. The command line equivalent is:

```bash
codex mcp login paper-view-canvas
```

The website handles sign-in and consent. After approval, Codex can redirect the browser to a temporary `127.0.0.1` callback so the local client receives the authorization code. This is separate from the hosted MCP endpoint and the local development server below.

The MCP tool returns a canvas URL on `https://ipaperview.com`. Codex decides
where to open it; MCP cannot force a right sidebar.

## Local development

The server can also run directly with the MCP SDK:

```bash
PAPER_VIEW_MCP_ISSUER_URL=http://127.0.0.1:9410 \
PAPER_VIEW_MCP_RESOURCE_URL=http://127.0.0.1:9410/mcp \
uv run --no-project --with 'mcp==1.26.0' python3 -m integrations.mcp_server.server
```

The default API base is `https://api.ipaperview.com`. Override it with
`PAPER_VIEW_API_BASE_URL` for a development backend.

## WorkBuddy

The WorkBuddy connector template is in
`integrations/workbuddy/paper-view-canvas`. It connects to the same public
Streamable HTTP endpoint and uses WorkBuddy's built-in MCP OAuth flow. Users
sign in on `https://ipaperview.com`; no personal API Token is required.

## Tools

`start_drawing`, `draw_svg_layer`, `get_svg_layer`, `update_svg_layer`, and
`inspect_drawing` support editable agent-authored SVG. Create one object with
`draw_svg_layer` for a figure that should download and edit as a whole. Read
its latest source/revision with `get_svg_layer`, then update the same
`artifact_ref` with a complete cumulative SVG and the current `base_revision`.
This replaces the whole SVG; it does not append fragments. Each additional
create is an independent object, even with a shared session and viewBox.

The MCP initialization instructions and tool descriptions in `server.py`
explain this routing to clients that do not load a bundled skill. Deploy the
updated MCP adapter for remote clients to receive these descriptions, and
refresh/reconnect clients that cache their tool catalog. The bundled Codex
and WorkBuddy skills are distributed separately through their plugin or
connector release; editing server descriptions does not update an installed
skill package. See the root README for the plugin release process.

`list_image_models`, `quote_image`, `submit_image`, `get_image_job`,
`list_image_jobs`, and `open_canvas` are available. Reuse a stable UUID
`client_request_id` on submit retries. A completed job includes its image,
Artifact reference, Credit receipt, and canvas URL.

## Native image inputs and parameters

Deploy the backend and image worker from the matching Paper View product commit,
apply `core.0092_board_image_native_parameters`, then deploy this MCP adapter.
The migration adds durable native request options, all result images, and batch
reservation IDs. Keep the adapter copies in both repositories synchronized.

`list_image_models` returns per-model reference limits, mask support, and
`model_parameters_schema`. `submit_image` and `quote_image` both accept:

- `reference_images`: public HTTP(S) image URLs or PNG/JPEG/WebP base64 data URLs;
  local paths and shared upstream file IDs are not accepted.
- `mask_image`: a GPT Image PNG mask with alpha/transparent pixels matching the
  first reference image.
- `model_parameters`: the native inference body, including nested Gemini
  `generationConfig`, `tools`, `safetySettings`, etc., or GPT Image `quality`,
  `size`, `n`, background/format/compression, streaming and preview settings.
  Extra native inference fields pass through to the provider, which validates
  its current model, gateway and account capabilities. Routing/authentication
  and the named prompt/model/image arguments remain managed by the service.

Use the same inputs when quoting and submitting. Native dimensions determine
the 1K/2K/4K billing tier; automatic GPT sizing uses the 4K tier. Batch counts
reserve each potential output and charge only delivered final images. All final
URLs appear in `get_image_job.images`, with the first URL retained in
`image_url`. The worker collects upstream SSE responses; MCP clients continue
polling the job. `session_id` groups board results only; edit a previous image
by explicitly passing its URL in `reference_images`.

See the bundled skill's `references/image-generation.md` for provider examples,
input limits and incompatible settings. Refresh the MCP tool catalog after
server deployment. Installing a new skill alone does not update a hosted API.
