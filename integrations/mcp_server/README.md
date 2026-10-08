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

Install `paper-view-canvas@paper-view-mcp` from this repository's marketplace.
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

`list_image_models`, `quote_image`, `submit_image`, `get_image_job`,
`list_image_jobs`, and `open_canvas` are available. Reuse a stable UUID
`client_request_id` on submit retries. A completed job includes its image,
Artifact reference, Credit receipt, and canvas URL.
