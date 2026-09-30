# Paper View Board

An SVG board for your agent to draw on. Generate images with Nano Banana or GPT Image using your Paper View account, then open the result on an editable SVG board.

The hosted MCP endpoint is **https://ipaperview.com/mcp**. Sign in through **https://ipaperview.com** when your client asks to connect. The server uses your existing Paper View Credits; no token belongs in prompts or this repository.

## Codex

Install the repository marketplace and plugin:

```bash
codex plugin marketplace add yyccR/paper-view-mcp
codex plugin add paper-view-canvas@paper-view-mcp
```

In the Codex Plugins view, install **Paper View Board** and select **Authenticate** if prompted. The browser opens the Paper View website. Start a new Codex conversation after installation so its tools and skill are loaded.

For a direct MCP connection without the plugin:

```bash
codex mcp add paper-view-board --url https://ipaperview.com/mcp
codex mcp login paper-view-board
```

The plugin's stable technical ID remains `paper-view-canvas`; its display name is **Paper View Board**. Do not install both the plugin and the direct MCP connection unless you want duplicate tools.

## WorkBuddy

The connector package is in [`integrations/workbuddy/paper-view-canvas`](integrations/workbuddy/paper-view-canvas). It uses WorkBuddy's built-in MCP OAuth flow: `mcp.json` points to the hosted HTTPS endpoint, and `connector-meta.json` intentionally has no `auth_mode` or token form. On first connection, WorkBuddy should open the Paper View login page.

For local use, add a remote **Streamable HTTP** MCP server in WorkBuddy with URL `https://ipaperview.com/mcp`. To distribute it in the WorkBuddy connector marketplace, package that connector directory and submit it through the [WorkBuddy open platform](https://open.workbuddy.cn/docs/connector); marketplace listing requires WorkBuddy's review.

## Other MCP clients

Any client that supports Streamable HTTP MCP with OAuth can connect to `https://ipaperview.com/mcp`. For Claude Code:

```bash
claude mcp add --transport http paper-view-board https://ipaperview.com/mcp
```

Follow the client's OAuth prompt to sign in. Clients without MCP OAuth cannot use the browser-login flow; use a client that supports OAuth rather than putting a Paper View token in chat.

## Image and board workflow

1. Call `list_image_models` to inspect available models and sizes.
2. Call `quote_image` to check the current Credit cost.
3. Call `submit_image` with a stable `client_request_id`; reuse it when retrying the same request. For later changes to the same drawing, pass the returned `session_id`. Omit it only to start a separate canvas.
4. Poll `get_image_job` until the job completes. `list_image_jobs` retrieves recent jobs.
5. Open the returned `board_url` once, or call `open_canvas` with the session ID. The compact board checks for new results and adds them to the open canvas automatically.

The board link uses `https://ipaperview.com/board?board_session=...&compact=1`. It restores the generated image on the SVG board without opening the AI chat panel. The image itself remains raster content placed on an editable SVG canvas. MCP returns the URL; the desktop client decides whether to open it in a browser tab, side panel, or external browser.

## Server source

[`integrations/mcp_server`](integrations/mcp_server) contains the hosted service's Python MCP adapter and OAuth bridge. It calls Paper View's existing backend APIs and needs a deployed Paper View website, API, and image worker. It is not a standalone image generator. Its production Compose example expects the Paper View Docker network and a gateway routing `/mcp` plus the advertised OAuth endpoints.

Run server tests locally with:

```bash
uv run --no-project --with 'mcp==1.26.0' python -m unittest discover -s integrations/mcp_server/tests -p 'test_*.py'
python3 -m unittest discover -s tests -p 'test_*.py'
```

See [the server notes](integrations/mcp_server/README.md) for deployment details. Source and logo usage are subject to [the Paper View license](LICENSE).

## 中文速览

Codex 执行上面的两条安装命令后，在插件页面选择 **Paper View Board** 并通过 `ipaperview.com` 登录。WorkBuddy 添加远程 Streamable HTTP MCP 地址 `https://ipaperview.com/mcp`，或使用仓库内的连接器包提交其开放平台。首张图片生成完成后打开工具返回的 `board_url`，即可查看不带聊天框的紧凑 SVG 画板。后续任务复用同一 `session_id`，已打开的画板会自动显示新图片，不需要重复打开。
