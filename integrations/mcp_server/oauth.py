"""OAuth authorization-code bridge from Paper View web login to Canvas MCP."""

from __future__ import annotations

import asyncio
import hashlib
import os
import secrets
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

import httpx
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    RefreshToken,
    TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken


@dataclass
class PendingLogin:
    client_id: str
    client_name: str
    params: AuthorizationParams
    expires_at: float


class PaperViewOAuthProvider:
    def __init__(self, *, api_base: str, website_base: str, resource_url: str, state_db: str | None = None):
        self.api_base = api_base.rstrip('/')
        self.website_base = website_base.rstrip('/')
        self.resource_url = resource_url
        self.state_db = Path(state_db or os.environ.get(
            'PAPER_VIEW_MCP_STATE_DB',
            '~/.local/share/paper-view/canvas-mcp-oauth.sqlite3',
        )).expanduser()
        self.state_db.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with self._database() as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS clients (client_id TEXT PRIMARY KEY, info TEXT NOT NULL)')
            connection.execute('''CREATE TABLE IF NOT EXISTS refresh_tokens (
                token_hash TEXT PRIMARY KEY, client_id TEXT NOT NULL,
                api_token TEXT NOT NULL, expires_at INTEGER NOT NULL
            )''')
        os.chmod(self.state_db, 0o600)
        self.pending: dict[str, PendingLogin] = {}
        self.codes: dict[str, tuple[AuthorizationCode, str]] = {}
        self.lock = asyncio.Lock()

    def _database(self):
        return sqlite3.connect(self.state_db)

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        with self._database() as connection:
            row = connection.execute('SELECT info FROM clients WHERE client_id = ?', (client_id,)).fetchone()
        return OAuthClientInformationFull.model_validate_json(row[0]) if row else None

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        if not client_info.client_id:
            raise ValueError('OAuth client ID is required')
        with self._database() as connection:
            connection.execute(
                'INSERT INTO clients (client_id, info) VALUES (?, ?)',
                (client_info.client_id, client_info.model_dump_json()),
            )

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        flow_id = str(uuid.uuid4())
        async with self.lock:
            now = time.time()
            self.pending = {key: value for key, value in self.pending.items() if value.expires_at > now}
            self.pending[flow_id] = PendingLogin(
                client_id=client.client_id,
                client_name=' '.join(str(getattr(client, 'client_name', '') or '').split())[:80],
                params=params,
                expires_at=now + 600,
            )
        return f'{self.website_base}/mcp/connect?{urlencode({"flow": flow_id})}'

    async def get_pending_client_name(self, flow_id: str) -> str:
        async with self.lock:
            pending = self.pending.get(flow_id)
            if not pending or pending.expires_at < time.time():
                raise ValueError('This connection request expired. Start login again in your MCP client.')
            return pending.client_name or '第三方应用'

    async def complete_login(self, flow_id: str, ticket: str) -> str:
        async with self.lock:
            pending = self.pending.get(flow_id)
            if not pending or pending.expires_at < time.time():
                raise ValueError('This connection request expired. Start login again in your MCP client.')
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f'{self.api_base}/api/board/plugin/exchange-ticket/',
                    json={'flow_id': flow_id, 'ticket': ticket},
                )
            if response.status_code != 200:
                raise ValueError(response.json().get('error') or 'Paper View login failed')
            access_token = response.json()['access_token']
            code = secrets.token_urlsafe(32)
            auth_code = AuthorizationCode(
                code=code,
                scopes=pending.params.scopes or [],
                expires_at=time.time() + 300,
                client_id=pending.client_id,
                code_challenge=pending.params.code_challenge,
                redirect_uri=pending.params.redirect_uri,
                redirect_uri_provided_explicitly=pending.params.redirect_uri_provided_explicitly,
                resource=pending.params.resource,
            )
            self.codes[code] = (auth_code, access_token)
            del self.pending[flow_id]
            from mcp.server.auth.provider import construct_redirect_uri

            return construct_redirect_uri(
                str(pending.params.redirect_uri),
                code=code,
                **({'state': pending.params.state} if pending.params.state else {}),
            )

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str,
    ) -> AuthorizationCode | None:
        entry = self.codes.get(authorization_code)
        if not entry or entry[0].client_id != client.client_id or entry[0].expires_at < time.time():
            return None
        return entry[0]

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode,
    ) -> OAuthToken:
        async with self.lock:
            entry = self.codes.pop(authorization_code.code, None)
        if not entry or entry[0].client_id != client.client_id:
            raise TokenError(error='invalid_grant', error_description='Authorization code already used')
        refresh = self._new_refresh_token(client.client_id, entry[1])
        return OAuthToken(access_token=entry[1], token_type='Bearer', refresh_token=refresh)

    def _new_refresh_token(self, client_id: str, api_token: str) -> str:
        refresh = secrets.token_urlsafe(48)
        with self._database() as connection:
            connection.execute('DELETE FROM refresh_tokens WHERE expires_at < ?', (int(time.time()),))
            connection.execute(
                'INSERT INTO refresh_tokens (token_hash, client_id, api_token, expires_at) VALUES (?, ?, ?, ?)',
                (hashlib.sha256(refresh.encode()).hexdigest(), client_id, api_token, int(time.time()) + 30 * 86400),
            )
        return refresh

    async def load_refresh_token(self, client: OAuthClientInformationFull, refresh_token: str) -> RefreshToken | None:
        with self._database() as connection:
            row = connection.execute(
                'SELECT client_id, expires_at FROM refresh_tokens WHERE token_hash = ?',
                (hashlib.sha256(refresh_token.encode()).hexdigest(),),
            ).fetchone()
        if not row or row[0] != client.client_id or row[1] < time.time():
            return None
        return RefreshToken(token=refresh_token, client_id=client.client_id, scopes=[], expires_at=row[1])

    async def exchange_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: RefreshToken, scopes: list[str],
    ) -> OAuthToken:
        token_hash = hashlib.sha256(refresh_token.token.encode()).hexdigest()
        with self._database() as connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute(
                'SELECT api_token FROM refresh_tokens WHERE token_hash = ? AND client_id = ? AND expires_at > ?',
                (token_hash, client.client_id, int(time.time())),
            ).fetchone()
            if row:
                connection.execute('DELETE FROM refresh_tokens WHERE token_hash = ?', (token_hash,))
        if not row:
            raise TokenError(error='invalid_grant', error_description='Refresh token expired or already used')
        refresh = self._new_refresh_token(client.client_id, row[0])
        return OAuthToken(access_token=row[0], token_type='Bearer', refresh_token=refresh)

    async def load_access_token(self, token: str) -> AccessToken | None:
        if not token.startswith('pv_live_'):
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f'{self.api_base}/api/board/plugin/identity/',
                    headers={'Authorization': f'Bearer {token}'},
                )
            if response.status_code != 200:
                return None
            user_id = response.json().get('user_id')
            if not user_id:
                return None
            return AccessToken(
                token=token,
                client_id=f'paperview-user-{user_id}',
                scopes=[],
                resource=self.resource_url,
            )
        except (httpx.HTTPError, ValueError, KeyError):
            return None

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        if isinstance(token, RefreshToken):
            with self._database() as connection:
                connection.execute(
                    'DELETE FROM refresh_tokens WHERE token_hash = ?',
                    (hashlib.sha256(token.token.encode()).hexdigest(),),
                )
