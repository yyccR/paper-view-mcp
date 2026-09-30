"""Paper View's private Streamable HTTP MCP adapter."""

from __future__ import annotations

import os
import uuid
from typing import Any
from urllib.parse import urljoin

import httpx
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from .oauth import PaperViewOAuthProvider


API_BASE = os.environ.get('PAPER_VIEW_API_BASE_URL', 'https://api.ipaperview.com').rstrip('/')
PUBLIC_BASE = os.environ.get('PAPER_VIEW_PUBLIC_URL', 'https://ipaperview.com').rstrip('/') + '/'
MCP_HOST = os.environ.get('PAPER_VIEW_MCP_HOST', '127.0.0.1')
MCP_PORT = int(os.environ.get('PAPER_VIEW_MCP_PORT', '9410'))
ISSUER_URL = os.environ.get('PAPER_VIEW_MCP_ISSUER_URL', 'https://ipaperview.com')
RESOURCE_URL = os.environ.get('PAPER_VIEW_MCP_RESOURCE_URL', 'https://ipaperview.com/mcp')


oauth_provider = PaperViewOAuthProvider(
    api_base=API_BASE,
    website_base=PUBLIC_BASE,
    resource_url=RESOURCE_URL,
)
mcp = FastMCP(
    'Paper View Board',
    instructions=(
        'Use quote_image before submit_image when a user asks about cost. '
        'submit_image returns a job_id; poll get_image_job until completed or failed. '
        'For follow-up image changes, pass the previous session_id to submit_image so results stay on one canvas. '
        'Omit session_id only when the user starts a new canvas. '
        'Open board_url once for the first image. Keep that panel open for follow-up jobs; the canvas refreshes automatically. '
        'Use open_canvas only to recover a board URL, and never reopen an existing panel for the same session. '
        'Never include tokens in tool arguments or URLs.'
    ),
    host=MCP_HOST,
    port=MCP_PORT,
    stateless_http=True,
    json_response=True,
    auth=AuthSettings(
        issuer_url=ISSUER_URL,
        resource_server_url=RESOURCE_URL,
        client_registration_options=ClientRegistrationOptions(enabled=True),
    ),
    auth_server_provider=oauth_provider,
)


@mcp.custom_route('/complete', methods=['GET'])
async def complete_login_page(_request: Request) -> HTMLResponse:
    return HTMLResponse('''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>连接 Paper View Board</title><p id="status">正在完成连接…</p>
<script>
const status = document.getElementById('status');
const params = new URLSearchParams(location.hash.slice(1));
history.replaceState(null, '', location.pathname);
fetch('/complete-ticket', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({flow: params.get('flow'), ticket: params.get('ticket')})
}).then(async response => {
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || '连接失败');
  location.replace(result.redirect_url);
}).catch(error => { status.textContent = error.message; });
</script></html>''', headers={
        'Cache-Control': 'no-store',
        'Content-Security-Policy': "default-src 'none'; script-src 'unsafe-inline'; connect-src 'self'",
    })


@mcp.custom_route('/complete-ticket', methods=['POST'])
async def complete_login_ticket(request: Request) -> JSONResponse:
    try:
        data = await request.json()
        redirect_url = await oauth_provider.complete_login(
            str(uuid.UUID(str(data.get('flow')))),
            str(data.get('ticket') or ''),
        )
        return JSONResponse({'redirect_url': redirect_url}, headers={'Cache-Control': 'no-store'})
    except (ValueError, KeyError, httpx.HTTPError) as exc:
        return JSONResponse({'error': str(exc)}, status_code=400, headers={'Cache-Control': 'no-store'})


def _auth_header() -> dict[str, str]:
    token = get_access_token()
    if not token:
        raise ValueError('Authentication required')
    return {'Authorization': f'Bearer {token.token}'}


async def _api(method: str, path: str, *, payload: dict | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.request(
            method,
            f'{API_BASE}{path}',
            headers=_auth_header(),
            json=payload,
        )
    body = response.json()
    if response.status_code >= 400:
        raise ValueError(str(body.get('error') or 'Paper View request failed'))
    return body


def _with_canvas_url(payload: dict) -> dict[str, Any]:
    result = dict(payload)
    if result.get('board_url'):
        result['board_url'] = urljoin(PUBLIC_BASE, result['board_url'].lstrip('/'))
    return result


READ = ToolAnnotations(readOnlyHint=True, openWorldHint=False, destructiveHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, openWorldHint=False, destructiveHint=False)


@mcp.tool(annotations=READ, structured_output=True)
async def list_image_models() -> dict[str, Any]:
    """List supported Nano Banana and GPT Image models and sizes."""
    return await _api('GET', '/api/board/image-models/')


@mcp.tool(annotations=READ, structured_output=True)
async def quote_image(model: str, image_size: str = '1K') -> dict[str, Any]:
    """Get the current Credit price for one image without generating it."""
    return await _api('POST', '/api/board/image-quote/', payload={
        'model': model,
        'image_size': image_size,
    })


@mcp.tool(annotations=WRITE, structured_output=True)
async def submit_image(
    prompt: str,
    model: str,
    image_size: str = '1K',
    aspect_ratio: str = '1:1',
    generation_quality: str = '',
    session_id: str = '',
    client_request_id: str = '',
) -> dict[str, Any]:
    """Queue an image. Reuse session_id for follow-ups and client_request_id for retries."""
    result = await _api('POST', '/api/board/image-jobs/', payload={
        'prompt': prompt,
        'model': model,
        'image_size': image_size,
        'aspect_ratio': aspect_ratio,
        'generation_quality': generation_quality,
        'session_id': session_id,
        'client_request_id': client_request_id or str(uuid.uuid4()),
    })
    return _with_canvas_url(result)


@mcp.tool(annotations=READ, structured_output=True)
async def get_image_job(job_id: str) -> dict[str, Any]:
    """Read one generation job, result image, Credit receipt, and canvas link."""
    return _with_canvas_url(await _api('GET', f'/api/board/image-jobs/{uuid.UUID(job_id)}/'))


@mcp.tool(annotations=READ, structured_output=True)
async def list_image_jobs() -> dict[str, Any]:
    """List the current user's 20 most recent image jobs."""
    payload = await _api('GET', '/api/board/image-jobs/')
    payload['items'] = [_with_canvas_url(item) for item in payload.get('items', [])]
    return payload


@mcp.tool(annotations=READ, structured_output=True)
async def open_canvas(session_id: str) -> dict[str, Any]:
    """Get a link to the user's editable SVG canvas in a compact browser view."""
    session_id = str(uuid.UUID(session_id))
    session = await _api('GET', f'/api/board/ai-sessions/{session_id}/')
    return {
        'session_id': session_id,
        'title': session.get('title'),
        'canvas_revision': session.get('canvas_revision'),
        'board_url': urljoin(PUBLIC_BASE, f'board?board_session={session_id}&compact=1'),
    }


if __name__ == '__main__':
    mcp.run(transport='streamable-http')
