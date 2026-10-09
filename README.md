# Paper View Board

An SVG board for your agent to draw on. Agents can build editable SVG diagrams one layer at a time, inspect the canvas, and revise individual layers. Nano Banana and GPT Image generation remains available for raster content.

The hosted MCP endpoint is **https://ipaperview.com/mcp**. Sign in through **https://ipaperview.com** when your client asks to connect. The server uses your existing Paper View Credits; no token belongs in prompts or this repository.

## Codex

Install a published plugin version by pinning the marketplace to its Git tag:

```bash
codex plugin marketplace add yyccR/paper-view-mcp --ref v0.4.6
codex plugin add paper-view@paper-view-mcp
codex plugin list --marketplace paper-view-mcp --json
```

To switch to a newer release later, replace `vX.Y.Z` below with its published tag:

```bash
codex plugin remove paper-view@paper-view-mcp
codex plugin marketplace remove paper-view-mcp
codex plugin marketplace add yyccR/paper-view-mcp --ref vX.Y.Z
codex plugin add paper-view@paper-view-mcp
```

If a local `paper-view-mcp` marketplace is already configured, remove that marketplace source before adding the Git source. Users of the previous plugin ID must also remove `paper-view-canvas@paper-view-mcp` before installing `paper-view@paper-view-mcp`.

In the Codex Plugins view, install **Paper View** and select **Authenticate** if prompted. The browser opens the Paper View website. Start a new Codex conversation after installation so its tools and skill are loaded.

For a direct MCP connection without the plugin:

```bash
codex mcp add paper-view-board --url https://ipaperview.com/mcp
codex mcp login paper-view-board
```

The plugin ID is `paper-view`; its display name is **Paper View**. Its bundled Codex skill is named `draw`, so its qualified skill name is `paper-view:draw`. The MCP server ID remains `paper-view-canvas`. Do not install both the plugin and the direct MCP connection unless you want duplicate tools.

To publish a new version, update `plugins/paper-view/.codex-plugin/plugin.json` to the next `X.Y.Z`, run `python scripts/check_plugin_release.py` and the package tests, then merge the changes and create an immutable `vX.Y.Z` Git tag on that exact commit. Pushing the tag runs CI again and rejects a tag that differs from the manifest version. Never reuse or move a published tag; the tag and manifest identify the same downloadable plugin source.

Authentication and consent happen on `https://ipaperview.com`. After approval, Codex may briefly open `http://127.0.0.1:<port>/callback`: this is Codex's temporary local listener receiving the authorization result, not the Paper View server. The MCP connection itself remains `https://ipaperview.com/mcp`. If the browser opens localhost before the Paper View sign-in page, or the callback fails, restart authentication in the MCP client.

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

For editable agent-authored diagrams, call `start_drawing` and retain its `session_id`. Send one SVG layer at a time with `draw_svg_layer`; use the same numeric `viewBox` in every layer so they align on the canvas. Each call returns an `artifact_ref` and `revision`. Call `inspect_drawing` to list layers and read the saved canvas, and `get_svg_layer` before changing a prior layer. Submit the revised complete SVG with `update_svg_layer`, passing the current `base_revision`. A stale revision is rejected. Keep the first `board_url` open while subsequent layers sync into it.

The SVG tools accept inline SVG text, not local file paths: the hosted MCP server cannot read a file on the agent's computer. They allow vector shapes, paths, text, groups, gradients, and local markers. SVG scripts, stylesheets, external references, embedded images, and `foreignObject` are rejected. Each layer is limited to 512 KiB. The bundled `draw` skill has a [tested compatibility guide](plugins/paper-view/skills/draw/references/svg-compatibility.md) for SVG/PNG/JPEG/PPTX exports and alternative drawing methods. Drawing SVG layers does not consume image-generation Credits. If a user edits an imported layer on the board, the live canvas preserves it instead of automatically replacing it with an agent revision.

For raster image generation:

`list_image_models` reads the current model catalog from Paper View, including Nano Banana 2.1. Model availability and Credit prices are controlled by the hosted API, so a new image model does not require a plugin update.

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

Codex 执行上面的两条安装命令后，在插件页面选择 **Paper View** 并通过 `ipaperview.com` 登录。授权完成后短暂跳转到 `127.0.0.1` 是 Codex 接收回调的正常步骤，MCP 服务地址仍为 `https://ipaperview.com/mcp`。WorkBuddy 添加远程 Streamable HTTP MCP 地址，或使用仓库内的连接器包提交其开放平台。`list_image_models` 会实时读取模型列表，当前包含 Nano Banana 2.1。绘制可编辑图时先调用 `start_drawing`，再用 `draw_svg_layer` 逐层提交 SVG，用 `inspect_drawing` 查看状态；修改旧图层时先用 `get_svg_layer` 读取修订号，再调用 `update_svg_layer`。打开首次返回的 `board_url` 后，后续图层会自动进入同一画板。
