import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import httpx
from mcp.server.auth.provider import AuthorizationParams, TokenError

from integrations.mcp_server.oauth import PaperViewOAuthProvider


class FakeAPIClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def post(self, url, json):
        assert url == 'https://api.ipaperview.com/api/board/plugin/exchange-ticket/'
        assert json['ticket'] == 'website-ticket'
        return httpx.Response(200, json={'access_token': 'pv_live_test', 'user_id': 7})

    async def get(self, url, headers):
        assert url == 'https://api.ipaperview.com/api/board/plugin/identity/'
        assert headers['Authorization'] == 'Bearer pv_live_test'
        return httpx.Response(200, json={'user_id': 7})


class OAuthProviderTests(unittest.TestCase):
    def test_authorization_code_and_refresh_are_single_use(self):
        asyncio.run(self._run_flow())

    async def _run_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = PaperViewOAuthProvider(
                api_base='https://api.ipaperview.com',
                website_base='https://ipaperview.com',
                resource_url='https://ipaperview.com/mcp',
                state_db=str(Path(directory) / 'oauth.sqlite3'),
            )
            client = type('Client', (), {'client_id': 'codex-client'})()
            params = AuthorizationParams(
                state='codex-state', scopes=[], code_challenge='challenge',
                redirect_uri='http://127.0.0.1:2345/callback',
                redirect_uri_provided_explicitly=True,
                resource='https://ipaperview.com/mcp',
            )
            authorize_url = await provider.authorize(client, params)
            self.assertEqual(urlparse(authorize_url).netloc, 'ipaperview.com')
            flow = parse_qs(urlparse(authorize_url).query)['flow'][0]

            with patch('integrations.mcp_server.oauth.httpx.AsyncClient', return_value=FakeAPIClient()):
                callback = await provider.complete_login(flow, 'website-ticket')
                self.assertEqual(parse_qs(urlparse(callback).query)['state'], ['codex-state'])
                with self.assertRaisesRegex(ValueError, 'expired'):
                    await provider.complete_login(flow, 'website-ticket')
                code = parse_qs(urlparse(callback).query)['code'][0]
                auth_code = await provider.load_authorization_code(client, code)
                self.assertIsNotNone(auth_code)
                tokens = await provider.exchange_authorization_code(client, auth_code)
                self.assertEqual(tokens.access_token, 'pv_live_test')
                self.assertIsNotNone(await provider.load_access_token(tokens.access_token))
                with self.assertRaises(TokenError):
                    await provider.exchange_authorization_code(client, auth_code)

                refresh = await provider.load_refresh_token(client, tokens.refresh_token)
                self.assertIsNotNone(refresh)
                rotated = await provider.exchange_refresh_token(client, refresh, [])
                self.assertEqual(rotated.access_token, 'pv_live_test')
                self.assertIsNone(await provider.load_refresh_token(client, tokens.refresh_token))
                self.assertIsNotNone(await provider.load_refresh_token(client, rotated.refresh_token))
